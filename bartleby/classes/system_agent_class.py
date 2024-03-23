import torch
import bartleby.configuration as conf
from transformers import T5Tokenizer, T5ForConditionalGeneration

class System_agent:
    '''Class to hold object related to the system agent'''

    def __init__(self, logger):

        # Give torch the requested CPU resources
        torch.set_num_threads(conf.CPU_threads)
        logger.info(f'Assigned {conf.CPU_threads} CPU threads')

        # Add logger
        self.logger = logger

        # Start tokenizer and models
        self.tokenizer = T5Tokenizer.from_pretrained('google-t5/t5-small')

        self.system_agent_model = T5ForConditionalGeneration.from_pretrained(
            'gperdrizet/T5-small-system-agent',
            device_map='cpu'    
        )

        self.output_sizer_model = T5ForConditionalGeneration.from_pretrained(
            'gperdrizet/T5-small-output-size-selector',
            device_map='cpu'    
        )

    def translate_command(self, message):
        input_ids = self.tokenizer(f'summarize: {message}', return_tensors='pt').input_ids
        outputs = self.system_agent_model.generate(input_ids, max_new_tokens=10)

        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    def select_output_size(self, message):
        input_ids = self.tokenizer(f'summarize: {message}', return_tensors='pt').input_ids
        outputs = self.output_sizer_model.generate(input_ids, max_new_tokens=10)

        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)