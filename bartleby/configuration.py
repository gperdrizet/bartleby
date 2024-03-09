import os
import pathlib

# Set HuggingFace home to ./hf_cache
os.environ['HF_HOME'] = f'{pathlib.Path(__file__).parent.resolve()}/hf_cache'

import bartleby.credentials.matrix as matrix

# Specify encoding here. This is needed because some phones
# have a tendency to autocorrect '--' to '–', which is not an
# ASCII character and so the command parser was not recognizing
# it correctly

#-*- coding: utf-8 -*-

MODE = 'matrix'

LOG_LEVEL = 'DEBUG'
LOG_PREFIX = '%(levelname)s - %(message)s' # '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
CLEAR_LOGS = True

# Paths
PROJECT_ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
HF_CACHE = f'{PROJECT_ROOT_PATH}/hf_cache'
DATA_PATH = f'{PROJECT_ROOT_PATH}/data'
NEXT_BATCH_TOKEN_FILE = f'{DATA_PATH}/next_batch'
DOCUMENTS_PATH = f'{PROJECT_ROOT_PATH}/documents'
LOG_PATH = f'{PROJECT_ROOT_PATH}/logs'

# Matrix room parameters
matrix_room_id = matrix.matrix_room_id
matrix_server_url = matrix.matrix_server_url
matrix_bot_username = matrix.matrix_bot_username
matrix_bot_password = matrix.matrix_bot_password

# Document output stuff
docx_template_file = 'blank_template.docx'
default_title = 'Bartleby Text'

# Model stuff
default_model_type = 'tiiuae/falcon-7b-instruct'
initial_prompt = 'You are a friendly chatbot who always responds in the style of Bartleby the scrivener; a depressed and beleaguered legal clerk from the mid 1800s.'

supported_models = [
    'HuggingFaceH4/zephyr-7b-beta',
    'tiiuae/falcon-7b-instruct',
    'microsoft/DialoGPT-small',
    'microsoft/DialoGPT-medium',
    'microsoft/DialoGPT-large',
]

mistral_family_models = [
    'HuggingFaceH4/zephyr-7b-beta'
]

falcon_family_models = [
    'tiiuae/falcon-7b-instruct'
]

dialo_family_models = [
    'microsoft/DialoGPT-small',
    'microsoft/DialoGPT-medium',
    'microsoft/DialoGPT-large'
]

device_map = 'cpu'
CPU_threads = 18
model_input_buffer_size = 5
max_new_tokens = 128
do_sample = True
temperature = 1.0
top_k = 10
top_p = 0.95
truncate_newlines = True # If true, will cut off generated text at newline
