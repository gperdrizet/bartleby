import os
import pathlib

# Set HuggingFace home to ./hf_cache
os.environ['HF_HOME'] = f'{pathlib.Path(__file__).parent.resolve()}/hf_cache'

import bartleby.credentials.matrix as matrix
import bartleby.credentials.gdrive as gdrive

# Specify encoding here. This is needed because some phones
# have a tendency to autocorrect '--' to '–', which is not an
# ASCII character and so the command parser was not recognizing
# it correctly

#-*- coding: utf-8 -*-

MODE = 'matrix'

# Paths
PROJECT_ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
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
gdrive_folder_id = gdrive.gdrive_folder_id

# Model stuff
#model_type = 'HuggingFaceH4/zephyr-7b-beta'
#initial_prompt = 'You are a friendly chatbot who always responds in the style of Bartleby the scrivener; a depressed and beleaguered legal clerk from the mid 1800s.'

model_type = 'microsoft/DialoGPT-small'

#model_type = 'tiiuae/falcon-7b-instruct'
#initial_prompt = 'Continue the story in a surprising and interesting way.\nIt is morning, the sun is rising and it is very quiet.\nThe lamps are on and she rearranges them for hours.\nShe deals a deck of cards in silence.'

device_map = 'cpu'
CPU_threads = 18
prompt_buffer_size = 3
max_new_tokens = 16
do_sample = True
temperature = 1.0
top_k = 50
top_p = 0.95
truncate_newlines = True # If true, will cut off generated text at newline
