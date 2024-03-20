import os
import pathlib

# Set HuggingFace home to ./hf_cache
os.environ['HF_HOME']=f'{pathlib.Path(__file__).parent.resolve()}/hf_cache'

# Set visible GPUs
os.environ['CUDA_VISIBLE_DEVICES']='0'

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

# Decoding modes, used to set groups of generation 
# config parameters to non-model default values
# corresponding to common decoding methods

default_decoding_mode='sampling'

decoding_mode={
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


# Commands documentation to post in chat when asked

commands = '''\n<b>Available commands:</b>\n
\r  <b>--commands</b>                Posts this message to chat.
\r  <b>--input-buffer-size</b>       Post size of LLM input buffer.
\r  <b>--set-input-buffer-size N</b> Updates LLM input buffer to N messages.
\r  <b>--input-messages</b>          Posts content of LLM input buffer.
\r  <b>--prompt</b>                  Post the current system prompt to chat.
\r  <b>--set-prompt PROMPT</b>       Updates the system prompt to PROMPT and 
\r  <b></b>                          restarts chat history.
\r  <b>--reset-chat</b>              Clears and restarts chat history.
\r  <b>--decoding-mode</b>           Posts the current decoding mode.
\r  <b>--decoding-modes</b>          Posts available decoding mode presets.
\r  <b>--set-decoding-mode X</b>     Sets decoding mode to X preset.
\r  <b>--config</b>                  Post generation configuration parameters 
\r  <b></b>                          not set to model default.
\r  <b>--config-full</b>             Show all available generation
\r  <b></b>                          configuration parameters.
\r  <b>--set-config X Y</b>          Updates value of generation configuration 
\r  <b></b>                          parameter X to Y.
\r  <b>--model</b>                   Post current model to chat.
\r  <b>--models</b>                  Post supported models to chat.
\r  <b>--swap-model X</b>            Change the model type used for generation.
\r  <b>--document-title</b>        Posts current Google Doc document title 
\r  <b></b>                        to chat.
\r  <b>--set-document-title</b>    Updates Google Doc document title.
\r  <b>--set-gdrive-folder X</b>   Set Google Drive folder ID for document 
\r  <b></b>                        upload. 
\r  <b>--make-docx N</b>           Makes and uploads docx document to 
\r  <b></b>                        Google Drive using last N message.
'''