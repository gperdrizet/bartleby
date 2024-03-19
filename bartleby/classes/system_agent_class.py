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

        # Start model and tokenizer
        self.tokenizer = T5Tokenizer.from_pretrained('google-t5/t5-base')
        self.model = T5ForConditionalGeneration.from_pretrained('/mnt/fast_scratch/huggingface_transformers_cache/T5-base-system-agent')

    def translate_command(self, message):
        input_ids = self.tokenizer(f'summarize: {message}', return_tensors="pt").input_ids
        outputs = self.model.generate(input_ids, max_new_tokens=10)

        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)