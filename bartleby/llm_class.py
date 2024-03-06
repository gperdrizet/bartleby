import gc
import time
import torch
#import logging
import queue
import bartleby.configuration as conf
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig #BitsAndBytesConfig, FalconForCausalLM

class Llm:
    '''Class to hold object related to the LLM'''

    def __init__(self, logger):

        # Set device map
        self.device_map = conf.device_map

        # Set newline truncation
        self.truncate_newlines = conf.truncate_newlines

        # Add logger
        self.logger = logger

    def initialize_model(self, model_type):
        '''Fire up a model'''

        # Set model type
        self.model_type = model_type

        # Fire up the model and tokenizer based on model type
        if self.model_type in conf.mistral_family_models:

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_type)

            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_type,
                device_map = self.device_map
            )

        elif self.model_type in conf.falcon_family_models:

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_type)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_type)

        elif self.model_type in conf.dialo_family_models:

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_type)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_type)

        # Read the default generation config from the model
        self.default_generation_configuration = GenerationConfig.from_model_config(
            self.model.config
        )

        # Replace some stock values with new defaults from configuration file
        self.default_generation_configuration.max_new_tokens = conf.max_new_tokens
        self.default_generation_configuration.do_sample = conf.do_sample
        self.default_generation_configuration.temperature = conf.temperature
        self.default_generation_configuration.top_k = conf.top_k
        self.default_generation_configuration.top_p = conf.top_p
        #self.default_generation_configuration.torch_dtype = torch.bfloat16

    def restart_model(self, model_type):

        # Get rid of model and tokenizer
        del self.model
        del self.tokenizer

        # Clean up memory
        gc.collect()
        torch.cuda.empty_cache()

        self.initialize_model(model_type)

    def prompt_model(self, user):

        self.logger.info('Prompting model')

        # If we are early in the conversation, the chat history may be shorter
        # than the model input buffer size, in that case, use the length
        # of the chat history as the input buffer size
        if len(user.messages) < user.model_input_buffer_size:
            model_input_buffer_size = len(user.messages)

        else:
            model_input_buffer_size = user.model_input_buffer_size

        # Log user's chat buffer and input messages for debug
        i = 0

        for message in user.messages:
            self.logger.debug(f'{user.user_name}\'s chat buffer message {i}: {message}')
            i += 1

        self.logger.debug(f'Model input size: {model_input_buffer_size} most recent messages')

        # Select last n messages for input to the model
        input_messages = user.messages[-model_input_buffer_size:]

        i = 0

        for message in input_messages:
            self.logger.debug(f'Model input {i}: {message}')
            i += 1

        # Start generation timer
        generation_start_time = time.time()

        if user.model_type in conf.mistral_family_models:

            # Tokenize the updated conversation
            prompt = self.tokenizer.apply_chat_template(
                input_messages,
                tokenize = True,
                add_generation_prompt = True,
                return_tensors = 'pt'
            )
            
            if self.device_map != 'cpu':
                prompt=prompt.to('cuda')

            # Generate response
            output_ids = self.model.generate(
                prompt,
                generation_config = user.generation_configurations[user.model_type]
            )

            # Un-tokenize response
            model_output = self.tokenizer.batch_decode(
                output_ids,
                skip_special_tokens = True,
                clean_up_tokenization_spaces = False
            )

            # Stop generation timer and calculate total generation time
            dT = time.time() - generation_start_time
            self.logger.info(f'{output_ids.size()[1] - prompt.size()[1]} tokens generated in {round(dT, 1)} seconds')

            model_output_content = model_output[0]
            reply = model_output_content.split('\n<|assistant|>\n')[-1]
        
        elif user.model_type in conf.falcon_family_models:

            messages = []

            for message in user.messages[-model_input_buffer_size:]:
                messages.append(message['content'])

            input = '\n'.join(messages)
            inputs = self.tokenizer(input, return_tensors='pt')

            output_ids = self.model.generate(
                **inputs, 
                eos_token_id=self.tokenizer.eos_token_id,
                pad_token_id=self.tokenizer.eos_token_id,
                generation_config = user.generation_configurations[user.model_type],
                num_return_sequences = 1
            )

            reply = self.tokenizer.batch_decode(output_ids, eos_token_id=self.tokenizer.eos_token_id)

            # Stop generation timer and calculate total generation time
            dT = time.time() - generation_start_time
            self.logger.info(f'{output_ids.size()[1]} tokens generated in {round(dT, 1)} seconds')

            try:
                self.logger.debug(f'Raw reply: {reply}')
                reply = reply[0]
                reply = reply.split('\n')
                reply = reply[model_input_buffer_size]
                self.logger.debug(f'Parsed reply: {reply}')

            except IndexError as e:
                self.logger.error(f'Caught index error in reply parse.')
                reply = ''

        elif user.model_type in conf.dialo_family_models:

            # Collect and encode chat history

            # Empty holder for tokenized messages
            tokenized_messages = []

            # Add end-of-sequence as last 'message' in input
            input_messages.append({'content': self.tokenizer.eos_token})

            for message in input_messages[1:]:
                tokenized_message = self.tokenizer.encode(message['content'], return_tensors='pt')
                tokenized_messages.append(tokenized_message)

            # Concatenate tokenized chat messages
            inputs = torch.cat(tokenized_messages, dim=-1)

            # Generate response
            output_ids = self.model.generate(inputs, max_length=1000, pad_token_id=self.tokenizer.eos_token_id)

            # De-tokenize last response by bot
            reply = self.tokenizer.decode(output_ids[:, inputs.shape[-1]:][0], skip_special_tokens=True)

            # Stop generation timer and calculate total generation time
            dT = time.time() - generation_start_time
            self.logger.info(f'{len(output_ids[:, inputs.shape[-1]:][0])} tokens generated in {round(dT*1000, 0)} milliseconds')

        # Format and add the model's reply to the users message history
        model_message = {
            'role': 'assistant',
            'content': reply
        }

        user.messages.append(model_message)
        self.logger.debug(f'Model reply: {model_message}')

        # Done
        return True
