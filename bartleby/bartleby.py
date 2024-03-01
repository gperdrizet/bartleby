import os
import glob
import asyncio
import torch
import logging
from nio import RoomMessageText
from logging.handlers import RotatingFileHandler
from transformers import GenerationConfig

import bartleby.configuration as config
import bartleby.helper_functions as helper_funcs
import bartleby.matrix_class as matrix
import bartleby.llm_class as llm
import bartleby.docx_class as docx
import bartleby.user_class as user

async def main_matrix_loop(matrix_instance, users, llms, docx_instance, logger):

    # Log bot into the matrix server and post a hello
    _ = await matrix_instance.async_client.login(matrix_instance.matrix_bot_password)
    _ = await matrix_instance.post_system_message('Bartleby online. Send "--commands" to see a list of available control commands or just say "Hi!".')
    
    # Loop like this forever
    while True:

        # Poll the matrix server
        sync_response = await matrix_instance.async_client.sync(30000)

        # Write the next-batch token to a file here for the next restart
        with open(matrix_instance.next_batch_token_file, 'w') as next_batch_token:
            next_batch_token.write(sync_response.next_batch)

        # Check to make sure that the bot has been joined to the room
        if matrix_instance.matrix_room_id in sync_response.rooms.join:

            # Get events in the room
            for event in sync_response.rooms.join[matrix_instance.matrix_room_id].timeline.events:
                matrix_instance.logger.debug(f'Room event: {event.source}')
                
                # If the event is a message and mentions bartleby...
                if isinstance(event, RoomMessageText) and event.source['content']['body'].lower().find('bartleby: ') == 0:

                    # Get the username
                    user_name = event.sender.split(':')[0][1:]
                    logger.info(f'Caught message from {user_name} mentioning bartleby')

                    # If we have not heard from this user before, add them to users
                    # and populate some defaults from configuration.py
                    if user_name not in users.keys():

                        users[user_name] = user.User(user_name)
                        logger.info(f'New user: {user_name}')

                    # Then check to see if we have an instance of the user's model type,
                    # if we don't spin one up
                    if users[user_name].model_type not in llms.keys():

                        # Instantiate the llm class instance and initialize the model, then
                        # add it to the list of running llms
                        llms[users[user_name].model_type] = llm.Llm(logger)
                        llms[users[user_name].model_type].initialize_model(users[user_name].model_type)
                        logger.info(f"Initialized {users[user_name].model_type} model for {user_name}")

                    else:
                        logger.info(f"Already have {users[user_name].model_type} running for {user_name}")

                    # Check if the user has a configuration set for this type of model
                    if users[user_name].model_type not in users[user_name].generation_configurations.keys():

                        # If not, get the default generation configuration that came from 
                        # the model's initialization and give it to the user so they can have their
                        # own copy to modify at will
                        model_default_generation_configuration = llms[users[user_name].model_type].default_generation_configuration
                        users[user_name].generation_configuration = model_default_generation_configuration
                        logger.info(f'Set generation configuration for {user_name} from model defaults')
                        
                    # Get body of user message and add it to the user's conversation
                    user_message = await matrix_instance.catch_message(event)

                    users[user_name].messages.append({
                        'role': 'user',
                        'content': user_message
                    })

                    # # If the message is a command, send it to the command parser
                    # if user_message[:2] == '--' or user_message[:1] == '–':
                    #     _ = await matrix_instance.parse_command_message(
                    #         llm_instance, 
                    #         docx_instance,
                    #         user_message,
                    #         user
                    #     )
                    # else:

                    # Otherwise, Prompt the model with the user's message and post the
                    # model's response to chat
                    _ = llms[users[user_name].model_type].prompt_model(users[user_name])
                    _ = await matrix_instance.post_message(users[user_name])
                    logger.info(f'Bot posted reply to {user_name} in chat')
            
def run():
    '''Run bartleby'''

    # Fire up a logger
    logger = helper_funcs.start_logger()
    logger.info(f'Running in {config.MODE} mode')
    logger.info(f'Using {config.CPU_threads} CPU threads')

    # Give torch CPU resources
    torch.set_num_threads(config.CPU_threads)

    # Initialize a new docx document for text output
    docx_instance = docx.Docx()
    logger.info('Blank docx document created')

    # Choose the right mode
    if config.MODE == 'matrix':

        # Instantiate new matrix chat session
        matrix_instance = matrix.Matrix(logger)
        matrix_instance.start_matrix_client()
        logger.info('Matrix chat client started successfully')

        # Make empty dictionaries to hold user and llm class instances
        users, llms = {}, {}

        # Start the main loop
        asyncio.run(main_matrix_loop(matrix_instance, users, llms, docx_instance, logger))
