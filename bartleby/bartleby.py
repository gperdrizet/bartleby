#import torch
import queue
import discord
from threading import Thread

import bartleby.configuration as config
import bartleby.functions.helper_functions as helper_funcs
import bartleby.functions.IO_functions as io_funcs
import bartleby.classes.matrix_class as matrix
import bartleby.classes.docx_class as docx

def run():
    '''Run bartleby'''

    # Fire up a logger
    logger = helper_funcs.start_logger()
    logger.info(f'Running in {config.MODE} mode')
    logger.info(f'Using {config.CPU_threads} CPU threads')
    logger.info(f'Device map is: {config.device_map}')

    helper_funcs.check_directory_structure()
    logger.info('Directory structure OK')

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
    generator_thread = Thread(target=io_funcs.generator, args=[llms, generation_queue, response_queue, logger])
    generator_thread.start()
    logger.info('Started LLM generator thread')

    if config.MODE == 'matrix':

        # Instantiate new matrix chat session
        matrix_instance = matrix.Matrix(logger)
        matrix_instance.start_matrix_client()
        logger.info('Matrix chat client started successfully')

        # Start the matrix listener
        matrix_listener_thread = Thread(target=io_funcs.matrix_listener, args=[
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
        discord_listener_thread = Thread(target=io_funcs.discord_listener, args=[
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

        # # Start discord poster
        # discord_poster_thread = Thread(target=io_funcs.discord_poster, args=[
        #     response_queue, 
        #     logger
        # ])

        # discord_poster_thread.start()
        # logger.info('Started discord poster thread')