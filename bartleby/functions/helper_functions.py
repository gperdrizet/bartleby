import glob
import logging
import os
import time
import bartleby.configuration as conf
import bartleby.classes.user_class as user
import bartleby.classes.llm_class as llm
from pathlib import Path
from logging.handlers import RotatingFileHandler

def start_logger():
    '''Sets up logging, returns logger'''

    # Clear logs if asked
    if conf.CLEAR_LOGS == True:
        for file in glob.glob(f'{conf.LOG_PATH}/*.log*'):
            os.remove(file)

    # Create logger
    logger = logging.getLogger('bartleby')
    logger.setLevel(conf.LOG_LEVEL)
    
    handler = RotatingFileHandler(
        f'{conf.LOG_PATH}/bartleby.log',
        encoding='utf-8',
        maxBytes=32 * 1024 * 1024,  # 32 MiB, 
        backupCount=5
    )
    
    formatter = logging.Formatter(conf.LOG_PREFIX, datefmt='%Y-%m-%d %I:%M:%S %p')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.info('############################################### ')
    logger.info('############## Starting bartleby ############## ')
    logger.info('############################################### ')

    return logger

def check_directory_structure():
    '''Check to make sure we have directories that were not tracked by git'''

    Path(conf.HF_CACHE).mkdir(parents=True, exist_ok=True)
    Path(conf.LOG_PATH).mkdir(parents=True, exist_ok=True)

def setup_user(logger, user_name, users, llms):

    message_time = time.time()
    logger.info(f'0.00s: Caught message from {user_name} mentioning bartleby')

    # If we have not heard from this user before, add them to users
    # and populate some defaults from configuration.py
    if user_name not in users.keys():

        users[user_name] = user.User(user_name)
        logger.info(f'+{round(time.time() - message_time, 2)}s: New user: {user_name}')

    # Then check to see if we have a running instance of the user's model type,
    # if we don't spin one up
    if users[user_name].model_type not in llms.keys():

        # Instantiate the llm class instance and initialize the model, then
        # add it to the list of running llms
        llms[users[user_name].model_type] = llm.Llm(logger)
        llms[users[user_name].model_type].initialize_model(users[user_name].model_type)
        logger.info(f"+{round(time.time() - message_time, 2)}s: Initialized {users[user_name].model_type} model for {user_name}")

    else:
        logger.info(f"+{round(time.time() - message_time, 2)}s: Already have {users[user_name].model_type} running for {user_name}")

    # Check if the user has a configuration set for this type of model
    if users[user_name].model_type not in users[user_name].generation_configurations.keys():

        # If not, get the default generation configuration that came from 
        # the model's initialization and give it to the user so they can have their
        # own copy to modify at will
        model_default_generation_configuration = llms[users[user_name].model_type].default_generation_configuration
        users[user_name].generation_configurations[users[user_name].model_type] = model_default_generation_configuration
        users[user_name].set_decoding_mode()
        logger.info(f'+{round(time.time() - message_time, 2)}s: Set generation configuration for {user_name} with {users[user_name].decoding_mode} defaults')

    return message_time

def generator(llms, generation_queue, response_queue):
    '''Takes a user from the listener and generates a reply.
    Sends the reply to the responder.'''

    # Do this forever
    while True:
        
        # Get the next user from the generation input queue
        queued_user = generation_queue.get()

        # Send the user for generation
        _ = llms[queued_user.model_type].prompt_model(queued_user)
        generation_queue.task_done()

        # Send the user to responder to post the LLM's response
        response_queue.put(queued_user)