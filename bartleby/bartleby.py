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

async def main_matrix_loop(matrix_instance, users, llms, docx_instance, logger):

    # Log bot into the matrix server and post a hello
    _ = await matrix_instance.async_client.login(matrix_instance.matrix_bot_password)
    _ = await matrix_instance.post_message('Bartleby online. Send "--commands" to see a list of available control commands or just say "Hi!".')
    
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
                    user = event.sender.split(':')[0][1:]
                    logger.info(f'Caught message from {user} mentioning bartleby')

                    # If we have not heard from this user before, add them to users
                    # and populate some defaults from configuration.py
                    if user not in users.keys():

                        logger.info(f'New user: {user}')

                        users[user] = {
                            'messages': [{
                                'role': 'system',
                                'content': config.initial_prompt
                            }],
                            'model_type': config.model_type
                        }

                    # Then check to see if we have an instance of the user's model type
                    # if we don't spin one up
                    if users[user]['model_type'] not in llms.keys():

                        llms[users[user]['model_type']] = llm.Llm(logger, users[user]['model_type'])
                        llms[users[user]['model_type']].initialize_model()
                        logger.info(f"Initialized {users[user]['model_type']} model for {user}")

                        users[user]['generation_config'] = GenerationConfig.from_model_config(llms[users[user]['model_type']].model.config)
                        logger.info(f'Set default generation configuration for {user}')

                    else:
                        logger.info(f"Already have {users[user]['model_type']} running for {user}")

                    # Get body of user message
                    user_message = await matrix_instance.catch_message(event)

                    # And add it to the user's conversation
                    users[user]['messages'].append({
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

                    # # Otherwise, Prompt the model with the user's message and post the
                    # # model's response to chat
                    # else: 
                    model_output, users = llms[users[user]['model_type']].prompt_model(users, user)
                    result = await matrix_instance.post_message(model_output, user)
                    logger.info('Bot reply posted to chat')
            
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
        users, llms = {}

        # Start the main loop
        asyncio.run(main_matrix_loop(matrix_instance, users, llms, docx_instance, logger))
