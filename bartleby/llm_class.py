import gc
import time
import torch
import logging
import bartleby.configuration as conf
from transformers import AutoTokenizer, AutoModelForCausalLM, FalconForCausalLM, GenerationConfig

class Llm:
    '''Class to hold object related to the LLM'''

    def __init__(self, logger):

        # Model related stuff
        self.model_type = conf.model_type
        self.device_map = conf.device_map
        self.prompt_buffer_size = conf.prompt_buffer_size

        # Add logger
        self.logger = logger

        # Empty dict to hold conversations
        self.messages = {}

    def initialize_model(self):

        if self.model_type == 'HuggingFaceH4/zephyr-7b-beta':

            # Fire up the model and tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_type)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_type, device_map = self.device_map)

        elif self.model_type == 'tiiuae/falcon-7b-instruct':

            # Fire up the model and tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_type)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_type)

        elif self.model_type == 'microsoft/DialoGPT-small':

            # Fire up the model and tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_type, padding_side='left')
            self.model = AutoModelForCausalLM.from_pretrained(self.model_type)
            

    def add_conversation(self, user):

        if self.model_type == 'HuggingFaceH4/zephyr-7b-beta':

            # Load default prompt
            self.messages[user] = [{
                'role': 'system',
                'content': conf.initial_prompt
            }]

        elif self.model_type == 'tiiuae/falcon-7b-instruct':

            self.messages[user] = []

            for instruction in conf.initial_prompt.split('\n'):

                self.messages[user].append({
                    'role': 'system',
                    'content': instruction
                })

        elif self.model_type == 'microsoft/DialoGPT-small':

            self.messages[user] = []

    def restart_model(self):

        # Get rid of model and tokenizer
        del self.model
        del self.tokenizer

        # Clean up memory
        gc.collect()
        torch.cuda.empty_cache()

        self.initialize_model()

    def initialize_model_config(self):

        # Read and set generation configuration defaults from config file.
        self.truncate_newlines = conf.truncate_newlines

        self.gen_cfg = GenerationConfig.from_model_config(self.model.config)
        self.gen_cfg.max_new_tokens = conf.max_new_tokens
        self.gen_cfg.do_sample = conf.do_sample
        self.gen_cfg.temperature = conf.temperature
        self.gen_cfg.top_k = conf.top_k
        self.gen_cfg.top_p = conf.top_p
        self.gen_cfg.torch_dtype = torch.bfloat16

    def prompt_model(self, user_message, user):

        self.logger.info('Prompting model')

        # Check to see if we already have a running conversation
        # with this user, if not start one
        if user not in self.messages.keys():
            self.add_conversation(user)

        # Format user message as dict
        user_message = {
            'role': 'user',
            'content': user_message
        }

        # Add new message to conversation
        self.messages[user].append(user_message)

        # Start generation timer
        generation_start_time = time.time()

        if self.model_type == 'HuggingFaceH4/zephyr-7b-beta':

            # Tokenize the updated conversation
            prompt = self.tokenizer.apply_chat_template(
                self.messages[user][-self.prompt_buffer_size:],
                tokenize = True,
                add_generation_prompt = True,
                return_tensors = 'pt'
            )
            
            if self.device_map != 'cpu':
                prompt=prompt.to('cuda')

            # Generate response
            output_ids = self.model.generate(
                prompt,
                generation_config = self.gen_cfg
            )

            # Stop generation timer and calculate total generation time
            generation_finish_time = time.time()
            dT = (generation_finish_time - generation_start_time) / 60
            self.logger.info(f'{output_ids.size()[1] - prompt.size()[1]} tokens generated in {round(dT, 1)} seconds')

            # Un-tokenize response
            model_output = self.tokenizer.batch_decode(
                output_ids,
                skip_special_tokens = True,
                clean_up_tokenization_spaces = False
            )

            model_output_content = model_output[0]

            reply = model_output_content.split('\n<|assistant|>\n')[-1]
        
        elif self.model_type == 'tiiuae/falcon-7b-instruct':

            messages = []

            for message in self.messages[user]:
                messages.append(message["content"])

            input = "\n".join(messages[-self.prompt_buffer_size:])

            inputs = self.tokenizer(input, return_tensors='pt')

            output_ids = self.model.generate(
                **inputs, 
                eos_token_id=self.tokenizer.eos_token_id,
                pad_token_id=self.tokenizer.eos_token_id,
                generation_config = self.gen_cfg
            )

            # Stop generation timer and calculate total generation time
            generation_finish_time = time.time()
            dT = (generation_finish_time - generation_start_time) / 60
            self.logger.info(f'{output_ids.size()[1]} tokens generated in {round(dT, 1)} seconds')

            reply = self.tokenizer.batch_decode(output_ids)

            try:
                reply = reply[0]
                reply = reply.split('\n')[self.prompt_buffer_size]

            except IndexError as e:
                print(f'Caught index error in reply parse.')
                print(f'Reply: {reply}')

                reply = ''

        elif self.model_type == 'microsoft/DialoGPT-small':

            self.logger.debug(f'Chat buffer: {self.messages}')
            self.logger.debug(f'Prompt input buffer size: {self.prompt_buffer_size}')

            # Collect and encode chat history
            tokenized_messages = []
            input_messages = self.messages[user][-self.prompt_buffer_size:]

            for message in input_messages:
                self.logger.debug(f'Message to be tokenized: {message}')
                tokenized_message = self.tokenizer.encode(message['content'] + self.tokenizer.eos_token, return_tensors='pt')
                tokenized_messages.append(tokenized_message)

            self.logger.debug(f'Have {len(tokenized_message)} tokenized message to torch concat.')

            # append the new user input tokens to the chat history
            inputs = torch.cat(tokenized_messages, dim=-1)

            # generated a response while limiting the total chat history to 1000 tokens, 
            chat_history_ids = self.model.generate(inputs, max_length=1000, pad_token_id=self.tokenizer.eos_token_id)

            # pretty print last output tokens from bot
            reply = self.tokenizer.decode(chat_history_ids[:, inputs.shape[-1]:][0], skip_special_tokens=True)

        model_message = {
            'role': 'assistant',
            'content': reply
        }

        self.logger.debug(f'Model reply: {model_message}')
        
        self.messages[user].append(model_message)

        return reply
