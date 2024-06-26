import queue
from threading import Thread

import bartleby.configuration as config
import bartleby.functions.helper_functions as helper_funcs
import bartleby.functions.bartleby_discord as discord_funcs
import bartleby.functions.bartleby_matrix as matrix_funcs
import bartleby.classes.matrix_class as matrix
import bartleby.classes.docx_class as docx

def run():
    '''Run bartleby'''

    # Check for existence of logs and hf_cache directories
    helper_funcs.check_directory_structure()

    # Fire up a logger
    logger = helper_funcs.start_logger()

    logger.info('Directory structure OK')
    logger.info(f'Running in {config.MODE} mode')
    logger.info(f'Using {config.CPU_threads} CPU threads')
    logger.info(f'Device map is: {config.device_map}')

    # Make empty dictionaries to hold user and llm class instances
    users, llms = {}, {}
    logger.info(f'Initialized empty data structures for users and LLMs')

    # Make generation queue to take users from the listener
    # and send them to the LLM when the need a response
    generation_queue = queue.Queue()
    response_queue = queue.Queue()
    logger.info('Created queues for LLM IO.')
    
    # Make instance of docx class to generate and upload documents
    docx_instance = docx.Docx()
    logger.info('Docx instance started successfully')

    # Start generator thread for LLMs
    generator_thread = Thread(target=helper_funcs.generator, args=[llms, generation_queue, response_queue])
    generator_thread.start()
    logger.info('Started LLM generator thread')

    if config.MODE == 'matrix':

        # Instantiate new matrix chat session
        matrix_instance = matrix.Matrix(logger)
        matrix_instance.start_matrix_client()
        logger.info('Matrix chat client started successfully')

        # Start the matrix listener
        matrix_listener_thread = Thread(target=matrix_funcs.matrix_listener, args=[
            docx_instance,
            matrix_instance, 
            users, 
            llms, 
            generation_queue, 
            response_queue, 
            logger
        ])

        matrix_listener_thread.start()
        logger.info('Started matrix listener thread')

    elif config.MODE == 'discord':
        
        # Start the discord listener
        discord_listener_thread = Thread(target=discord_funcs.discord_listener, args=[
            config.bot_token,
            docx_instance, 
            users, 
            llms, 
            generation_queue, 
            response_queue, 
            logger
        ])

        discord_listener_thread.start()
        logger.info('Started discord listener thread')