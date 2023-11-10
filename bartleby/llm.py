import torch
import bartleby.configuration as conf
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig

class Llm:
    '''Class to hold object related to the LLM'''

    def __init__(self):

        # Model related stuff
        self.model_type = conf.model_type
        self.device_map = conf.device_map

    def initialize_model(self):

        # Fire up the model and tokenizer from HuggingFace.
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_type)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_type, device_map = self.device_map)

        # Load default prompt
        self.messages = [{
            'role': 'system',
            'content': conf.initial_prompt
        }]

    def initialize_model_config(self):

        # Read and set generation configuration defaults from config file.
        self.gen_cfg = GenerationConfig.from_model_config(self.model.config)
        self.gen_cfg.max_new_tokens = conf.max_new_tokens
        self.gen_cfg.do_sample = conf.do_sample
        self.gen_cfg.temperature = conf.temperature
        self.gen_cfg.top_k = conf.top_k
        self.gen_cfg.top_p = conf.top_p
        self.gen_cfg.torch_dtype = torch.bfloat16

        print(f'\n{self.gen_cfg}')

    def prompt_model(self, user_message):
        
        user_message = {
            'role': 'user', 
            'content': user_message
        }

        self.messages.append(user_message)

        print(f'\n{self.messages}')

        prompt = self.tokenizer.apply_chat_template(
            self.messages, 
            tokenize = True, 
            add_generation_prompt = True,
            return_tensors = 'pt'
        ).to('cuda')

        output_ids = self.model.generate(
            prompt, 
            generation_config = self.gen_cfg
        )

        model_output = self.tokenizer.batch_decode(
            output_ids, 
            skip_special_tokens = True, 
            clean_up_tokenization_spaces = False
        )[0]

        reply = model_output.split('\n<|assistant|>\n')[-1]

        model_message = {
            'role': 'assistant',
            'content': reply
        }
        
        self.messages.append(model_message)

        print(f'\n{self.messages}')

        return reply