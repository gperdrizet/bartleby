# import os
# import glob
import asyncio
import torch
import time
# import logging
import queue
from nio import RoomMessageText
from threading import Thread
# from logging.handlers import RotatingFileHandler
# from transformers import GenerationConfig

import bartleby.configuration as config
import bartleby.helper_functions as helper_funcs
import bartleby.matrix_class as matrix
import bartleby.llm_class as llm
import bartleby.docx_class as docx
import bartleby.user_class as user

async def matrix_listener_loop(docx_instance, matrix_instance, users, llms, generation_queue, response_queue, logger):
    '''Watches for messages from users in the matrix room, when it finds
    one, handles routing that user to an LLM'''

    # Log bot into the matrix server and post a hello
    _ = await matrix_instance.async_client.login(matrix_instance.matrix_bot_password)
    _ = await matrix_instance.post_system_message('Bartleby online. Send "--commands" to see a list of available control commands or just say "Hi!".', '')
    
    # Loop like this forever
    while True:

        # Poll the matrix server and wait 0 milliseconds for new events
        sync_response = await matrix_instance.async_client.sync(timeout=0)

        # Write the next-batch token to a file here for the next restart
        with open(matrix_instance.next_batch_token_file, 'w') as next_batch_token:
            next_batch_token.write(sync_response.next_batch)

        # Check to make sure that the bot has been joined to the room
        if matrix_instance.matrix_room_id in sync_response.rooms.join:

            # Get events in the room
            for event in sync_response.rooms.join[matrix_instance.matrix_room_id].timeline.events:
                matrix_instance.logger.debug(f'{event.source}')
                
                # If the event is a message and mentions bartleby...
                if isinstance(event, RoomMessageText) and event.source['content']['body'].lower().find('bartleby: ') == 0:

                    # Get the username
                    user_name = event.sender.split(':')[0][1:]

                    message_time = time.time()
                    logger.info(f't = 0.00: Caught message from {user_name} mentioning bartleby')

                    # If we have not heard from this user before, add them to users
                    # and populate some defaults from configuration.py
                    if user_name not in users.keys():

                        users[user_name] = user.User(user_name)
                        logger.info(f't = {round(time.time() - message_time, 2)}: New user: {user_name}')

                    # Then check to see if we have a running instance of the user's model type,
                    # if we don't spin one up
                    if users[user_name].model_type not in llms.keys():

                        # Instantiate the llm class instance and initialize the model, then
                        # add it to the list of running llms
                        llms[users[user_name].model_type] = llm.Llm(logger)
                        llms[users[user_name].model_type].initialize_model(users[user_name].model_type)
                        logger.info(f"t = {round(time.time() - message_time, 2)}: Initialized {users[user_name].model_type} model for {user_name}")

                    else:
                        logger.info(f"t = {round(time.time() - message_time, 2)}: Already have {users[user_name].model_type} running for {user_name}")

                    # Check if the user has a configuration set for this type of model
                    if users[user_name].model_type not in users[user_name].generation_configurations.keys():

                        # If not, get the default generation configuration that came from 
                        # the model's initialization and give it to the user so they can have their
                        # own copy to modify at will
                        model_default_generation_configuration = llms[users[user_name].model_type].default_generation_configuration
                        users[user_name].generation_configurations[users[user_name].model_type] = model_default_generation_configuration
                        logger.info(f't = {round(time.time() - message_time, 2)}: Set generation configuration for {user_name} from model defaults')

                    # Get body of user message
                    user_message = await matrix_instance.catch_message(event)
                    logger.debug(f't = {round(time.time() - message_time, 2)}: User message: {user_message}')

                    # Check to see if it's a command message, if so, send it to the command parser
                    if user_message[:2] == '--' or user_message[:1] == '–':

                        result = helper_funcs.parse_command_message(docx_instance, users[user_name], user_message)
                        _ = await matrix_instance.post_system_message(result, user_name)

                    # If it's not a command, add it to the user's conversation and 
                    # send them to the LLM for a response
                    else:

                        users[user_name].messages.append({
                            'role': 'user',
                            'content': user_message
                        })

                        # Put the user into the llm's queue
                        generation_queue.put(users[user_name])
                        logger.info(f't = {round(time.time() - message_time, 2)}: Added {user_name} to generation queue')

        # Check to see if there are any users with generated responses in the
        # Response queue, if so, post to chat.
        #
        # NOTE: documentation says, "Similarly, if empty() returns False it doesn’t 
        # guarantee that a subsequent call to get() will not block."
        # Not sure when/why that would happen...
        if response_queue.empty() == False:

            # Get the next user from the responder queue
            queued_user = response_queue.get()
            logger.info(f't = {round(time.time() - message_time, 2)}: Responder got {queued_user.user_name} from generator')

            # Post the new response from the users conversation
            _ = await matrix_instance.post_message(queued_user)
            response_queue.task_done()
            logger.info(f't = {round(time.time() - message_time, 2)}: Posted reply to {queued_user.user_name} in chat')


def generator(llms, generation_queue, response_queue, logger):
    '''Takes a user from the listener and generates a reply.
    Sends the reply to the responder.'''

    # Do this forever
    while True:
        
        # Get the next user from the generation input queue
        queued_user = generation_queue.get()
        logger.info(f'LLM got {queued_user.user_name} from listener')

        # Send the user for generation
        _ = llms[queued_user.model_type].prompt_model(queued_user)
        generation_queue.task_done()
        logger.info(f'Response for {queued_user.user_name} generated')

        # Send the user to responder to post the LLM's response
        response_queue.put(queued_user)


# Wrapper function to start the matrix listener loop via asyncIO in a thread
def matrix_listener(docx_instance, matrix_instance, users, llms, generation_queue, response_queue, logger):
    asyncio.run(matrix_listener_loop(docx_instance, matrix_instance, users, llms, generation_queue, response_queue, logger))

def run():
    '''Run bartleby'''

    # Fire up a logger
    logger = helper_funcs.start_logger()
    logger.info(f'Running in {config.MODE} mode')
    logger.info(f'Using {config.CPU_threads} CPU threads')

    helper_funcs.check_directory_structure()
    logger.info('Directory structure OK')

    # Give torch the requested CPU resources
    torch.set_num_threads(config.CPU_threads)
    logger.info(f'Assigned {config.CPU_threads} CPU threads')

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

    # Instantiate new matrix chat session
    matrix_instance = matrix.Matrix(logger)
    matrix_instance.start_matrix_client()
    logger.info('Matrix chat client started successfully')

    # Start the matrix listener
    matrix_listener_thread = Thread(target=matrix_listener, args=[
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

    # Start generator thread for LLMs
    generator_thread = Thread(target=generator, args=[llms, generation_queue, response_queue, logger])
    generator_thread.start()
    logger.info('Started LLM generator thread')