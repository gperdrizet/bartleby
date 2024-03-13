import gc
import time
import torch
import bartleby.configuration as conf
import bartleby.functions.model_prompting_functions as prompt_funcs
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig, BitsAndBytesConfig

class Llm:
    '''Class to hold object related to the LLM'''

    def __init__(self, logger):

        # Give torch the requested CPU resources
        torch.set_num_threads(conf.CPU_threads)
        logger.info(f'Assigned {conf.CPU_threads} CPU threads')

        # Set device map
        self.device_map = conf.device_map

        # Set quantization
        self.quantization = conf.model_quantization

        # Add logger
        self.logger = logger

    def initialize_model(self, model_type):
        '''Fire up a model'''

        # Set model type
        self.model_type = model_type

        # Fire up the model and tokenizer
        if self.model_type in conf.supported_models:

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_type)

            if self.quantization == 'four bit':
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True, 
                    bnb_4bit_compute_dtype=torch.float16
                )

            else:
                quantization_config = None

            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_type,
                device_map = self.device_map,
                quantization_config=quantization_config
            )

        # Read the default generation config from the model
        self.default_generation_configuration = GenerationConfig.from_model_config(
            self.model.config
        )

        # Replace some stock values with new defaults from configuration file
        self.default_generation_configuration.max_new_tokens = conf.max_new_tokens
        #self.default_generation_configuration.length_penalty = conf.length_penalty
        self.default_generation_configuration.torch_dtype = torch.bfloat16

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
            # If we have enough past messages, use the full buffer size from the
            # Users config
            model_input_buffer_size = user.model_input_buffer_size

        # Log user's chat history for debug
        i = 0

        for message in user.messages:
            self.logger.debug(f'{user.user_name}\'s chat buffer message {i}: {message}')
            i += 1

        self.logger.debug(f'Model input size: {model_input_buffer_size} most recent messages')

        # Select last n messages from chat history for input to the model
        input_messages = user.messages[-model_input_buffer_size:]

        i = 0

        # Log the contents of the model input buffer for debug
        for message in input_messages:
            self.logger.debug(f'Model input {i}: {message}')
            i += 1

        # Reset cuda memory stats
        torch.cuda.reset_peak_memory_stats()

        # Start generation timer
        generation_start_time = time.time()

        # Select and prompt model: mistral
        if user.model_type in conf.mistral_family_models:

            reply, num_tokens_generated = prompt_funcs.prompt_mistral(
                input_messages, 
                self.device_map, 
                self.model, 
                self.tokenizer,
                user.generation_configurations[user.model_type]
            )

        # Select and prompt model: falcon
        elif user.model_type in conf.falcon_family_models:

            reply, num_tokens_generated = prompt_funcs.prompt_falcon(
                input_messages,
                self.device_map,
                self.model, 
                self.tokenizer,
                user.generation_configurations[user.model_type]
            )

        # Select and prompt model: dialo
        elif user.model_type in conf.dialo_family_models:

            reply, num_tokens_generated = prompt_funcs.prompt_dialo(
                input_messages,
                self.device_map,
                self.model, 
                self.tokenizer
            )

        # Stop generation timer, calculate and log total generation time
        dT = time.time() - generation_start_time
        self.logger.info(f'{num_tokens_generated} tokens generated in {round(dT, 1)} seconds')

        # Get and log peak GPU memory use
        max_memory = torch.cuda.max_memory_allocated()
        self.logger.info(f'Peak GPU memory use: {round(max_memory / 10**9, 1)}')

        # Format models reply as dict
        model_message = {
            'role': 'assistant',
            'content': reply
        }

        # Add the reply to the users chat history and log for debug
        user.messages.append(model_message)
        self.logger.debug(f'Model reply: {model_message}')

        # Done
        return True
