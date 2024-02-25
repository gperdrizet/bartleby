import gc
import time
import torch
import bartleby.configuration as conf
from transformers import AutoTokenizer, AutoModelForCausalLM, FalconForCausalLM, GenerationConfig

class Llm:
    '''Class to hold object related to the LLM'''

    def __init__(self):

        # Model related stuff
        self.model_type = conf.model_type
        self.device_map = conf.device_map
        self.prompt_buffer_size = conf.prompt_buffer_size

    def initialize_model(self):

        if self.model_type == 'HuggingFaceH4/zephyr-7b-beta':

            # Fire up the model and tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_type)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_type, device_map = self.device_map)

            # Load default prompt
            self.messages = [{
                'role': 'system',
                'content': conf.initial_prompt
            }]

        elif self.model_type == 'tiiuae/falcon-7b-instruct':

            # Fire up the model and tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_type)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_type)

            self.messages = []

            for instruction in conf.initial_prompt.split('\n'):

                self.messages.append({
                    'role': 'system',
                    'content': instruction
                })


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

        print(f'\n{self.gen_cfg}')

    def prompt_model(self, user_message):

        # Format user message as dict
        user_message = {
            'role': 'user',
            'content': user_message
        }

        # Add new message to conversation
        self.messages.append(user_message)

        # Start generation timer
        generation_start_time = time.time()

        if self.model_type == 'HuggingFaceH4/zephyr-7b-beta':

            # Tokenize the updated conversation
            prompt = self.tokenizer.apply_chat_template(
                self.messages[-self.prompt_buffer_size:],
                tokenize = True,
                add_generation_prompt = True,
                return_tensors = 'pt'
            )
            
            if self.device_map != 'cpu':
                prompt=prompt.to('cuda')

            #print(f'Model input shape: {prompt.size()}')

            # Generate response
            output_ids = self.model.generate(
                prompt,
                generation_config = self.gen_cfg
            )

            # Stop generation timer and calculate total generation time
            generation_finish_time = time.time()
            dT = (generation_finish_time - generation_start_time) / 60

            #print(f'Model output shape: {output_ids.size()}')
            #print(f'New tokens generated: {output_ids.size()[1] - prompt.size()[1]}')
            #print(f'Generation time (min.): {round(dT, 1)}')

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

            for message in self.messages:
                messages.append(message["content"])

            #print(f'Messages: {messages}')
            input = "\n".join(messages[-self.prompt_buffer_size:])
            #print(f'Input:\n{input}\n')

            inputs = self.tokenizer(input, return_tensors='pt')

            output_ids = self.model.generate(
                **inputs, 
                eos_token_id=self.tokenizer.eos_token_id,
                pad_token_id=self.tokenizer.eos_token_id,
                generation_config = self.gen_cfg
            )

            reply = self.tokenizer.batch_decode(output_ids)

            try:
                reply = reply[0]
                reply = reply.split('\n')[self.prompt_buffer_size]

            except IndexError as e:
                print(f'Caught index error in reply parse.')
                print(f'Reply: {reply}')

                reply = ''

        model_message = {
            'role': 'assistant',
            'content': reply
        }
        
        self.messages.append(model_message)

        return reply
