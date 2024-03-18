import os
import pathlib

# Set HuggingFace home to ./hf_cache
os.environ['HF_HOME']=f'{pathlib.Path(__file__).parent.resolve()}/hf_cache'

# Set visible GPUs
os.environ['CUDA_VISIBLE_DEVICES']='1'

import bartleby.credentials.matrix as matrix
import bartleby.credentials.discord_credentials as discord

# Specify encoding here. This is needed because some phones
# have a tendency to autocorrect '--' to '–', which is not an
# ASCII character and so the command parser was not recognizing
# it correctly

#-*- coding: utf-8 -*-

MODE='discord' #'matrix'

LOG_LEVEL='DEBUG'
LOG_PREFIX='%(levelname)s - %(message)s' # '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
CLEAR_LOGS=True

# Paths
PROJECT_ROOT_PATH=os.path.dirname(os.path.realpath(__file__))
HF_CACHE=f'{PROJECT_ROOT_PATH}/hf_cache'
DATA_PATH=f'{PROJECT_ROOT_PATH}/data'
NEXT_BATCH_TOKEN_FILE=f'{DATA_PATH}/next_batch'
DOCUMENTS_PATH=f'{PROJECT_ROOT_PATH}/documents'
LOG_PATH=f'{PROJECT_ROOT_PATH}/logs'

# Matrix room parameters
matrix_room_id=matrix.matrix_room_id
matrix_server_url=matrix.matrix_server_url
matrix_bot_username=matrix.matrix_bot_username
matrix_bot_password=matrix.matrix_bot_password

# Discord stuff
bot_token = discord.token

# Document output stuff
docx_template_file='blank_template.docx'
default_title='Bartleby Text'

# Model stuff
default_model_type='tiiuae/falcon-7b-instruct'
initial_prompt='You are a friendly chatbot who always responds in the style of Bartleby the scrivener; a depressed and beleaguered legal clerk from the mid 1800s.'

supported_models=[
    'HuggingFaceH4/zephyr-7b-beta',
    'tiiuae/falcon-7b-instruct',
    'microsoft/DialoGPT-small',
    'microsoft/DialoGPT-medium',
    'microsoft/DialoGPT-large',
]

mistral_family_models=[
    'HuggingFaceH4/zephyr-7b-beta'
]

falcon_family_models=[
    'tiiuae/falcon-7b-instruct'
]

dialo_family_models=[
    'microsoft/DialoGPT-small',
    'microsoft/DialoGPT-medium',
    'microsoft/DialoGPT-large'
]

device_map='cuda:0'
model_quantization = 'four bit'
CPU_threads=18
model_input_buffer_size=5
max_new_tokens=128

# Generation modes, used to set groups of generation 
# config parameters to non-model default values

default_generation_mode='sampling'

generation_mode={
    'greedy': {
        'exponential_decay_length_penalty': (16, -1)
    },
    'beam_search': {
        'num_beams': 10,
        'early_stopping': True,
        'no_repeat_ngram_size': 2,
        'length_penalty': -0.1
    },
    'sampling': {
        'do_sample': True,
        'top_k': 0,
        'temperature': 0.6,
        'exponential_decay_length_penalty': (16, -1)
    },
    'top_k': {
        'do_sample': True,
        'top_k': 50,
        'exponential_decay_length_penalty': (16, -1)
    },
    'top_p': {
        'do_sample': True,
        'top_p': 0.92,
        'top_k': 0,
        'exponential_decay_length_penalty': (16, -1)
    },
    'top_kp':{
        'do_sample': True,
        'top_k': 50,
        'top_p': 0.95,
        'exponential_decay_length_penalty': (16, -1)
    }
}
