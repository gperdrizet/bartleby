import os
from transformers import T5Tokenizer, T5ForConditionalGeneration

# Set HuggingFace cache
os.environ['HF_HOME'] = '/mnt/fast_scratch/huggingface_transformers_cache'

if __name__ == '__main__':

    model = T5ForConditionalGeneration.from_pretrained(
        '/mnt/fast_scratch/huggingface_transformers_cache/2024-03-26_T5-base-system-agent'
    )

    model.push_to_hub('T5-base-system-agent')