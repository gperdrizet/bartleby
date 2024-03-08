import os
import torch
import pandas as pd
from transformers import T5Tokenizer, T5ForConditionalGeneration

# Set HuggingFace cache
os.environ['HF_HOME'] = '/mnt/fast_scratch/huggingface_transformers_cache'

if __name__ == '__main__':

    torch.set_num_threads(18)
    
    tokenizer = T5Tokenizer.from_pretrained('google-t5/t5-small')
    model = T5ForConditionalGeneration.from_pretrained('/mnt/fast_scratch/huggingface_transformers_cache/T5-system-agent')

    print()

    while True:
        message = input('User: ')
        input_ids = tokenizer(f'summarize: {message}', return_tensors="pt").input_ids
        outputs = model.generate(input_ids, max_new_tokens=10)
        print(f'System-agent: {tokenizer.decode(outputs[0], skip_special_tokens=True)}')