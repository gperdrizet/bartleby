import os
import bartleby.credentials.matrix as matrix
import bartleby.credentials.gdrive as gdrive

# Specify encoding here. This is needed because some phones
# have a tendency to autocorrect '--' to '–', which is not an
# ASCII character and so the command parser was not recognizing
# it correctly

#-*- coding: utf-8 -*-

# Paths
PROJECT_ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
DATA_PATH = f'{PROJECT_ROOT_PATH}/data'
NEXT_BATCH_TOKEN_FILE = f'{DATA_PATH}/next_batch'
DOCUMENTS_PATH = f'{PROJECT_ROOT_PATH}/documents'

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
model_type = 'HuggingFaceH4/zephyr-7b-beta'
device_map = 'auto'
initial_prompt = 'You are a friendly chatbot who always responds in the style of Bartleby the scrivener; a depressed and beleaguered legal clerk from the mid 1800s.'

max_new_tokens = 256
do_sample = True
temperature = 0.9
top_k = 50
top_p = 0.95

# Benchmarking parameters
replicates = 3
repetitions = 10
query = 'Please write a paragraph describing how to make scrambled eggs. Write in the style of a script for a youtube video.'
