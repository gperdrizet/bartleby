import os
import bartleby.credentials.matrix as matrix
import bartleby.credentials.gdrive as gdrive

# Specify encoding here. This is needed because some phones
# have a tendency to autocorrect '--' to '–', which is not an
# ASCII character and so the command parser was not recognizing
# it correctly

#-*- coding: utf-8 -*-

MODE = 'loop_on_prompt'

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
#model_type = 'HuggingFaceH4/zephyr-7b-beta'
#initial_prompt = 'You are a friendly chatbot who always responds in the style of Bartleby the scrivener; a depressed and beleaguered legal clerk from the mid 1800s.'

model_type = 'tiiuae/falcon-7b-instruct'
initial_prompt = 'Continue the story in a surprising and interesting way.\nIt is morning, the sun is rising and it is very quiet.\nThe lamps are on and she rearranges them for hours.\nShe deals a deck of cards in silence.'

device_map = 'cpu'
CPU_threads = 18
prompt_buffer_size = 3
max_new_tokens = 64
do_sample = True
temperature = 1.0
top_k = 50
top_p = 0.95
num_beams = 1
length_penalty = 0.1 # Only used if num_beams > 1
exponential_decay_length_penalty = (8, 1)
truncate_newlines = False # If true, will cut off generated text at newline

# Benchmarking parameters
replicates = 3
repetitions = 20
query = 'Please write a paragraph describing how to make scrambled eggs. Write in the style of a script for a youtube video.'
