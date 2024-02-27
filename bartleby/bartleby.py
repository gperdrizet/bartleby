import asyncio
import torch
import logging
from nio import RoomMessageText
from logging.handlers import RotatingFileHandler

import bartleby.configuration as config
import bartleby.helper_functions as helper_funcs
import bartleby.matrix_class as matrix
import bartleby.llm_class as llm
import bartleby.docx_class as docx

async def main_matrix_loop(matrix_instance, llm_instance, docx_instance):

    # Log bot into the matrix server and post a hello
    result = await matrix_instance.async_client.login(matrix_instance.matrix_bot_password)
    result = await matrix_instance.post_message('Bartleby online. Send "--commands" to see a list of available control commands or just say "Hi!".')
    
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

                    # Get the username so we can make sure that the bot does not 
                    # respond to it's own messages
                    user = event.sender.split(':')[0][1:]

                    # If the message was sent by a user other than the bot...
                    if user != matrix_instance.matrix_bot_username:
                        
                        # Get body of user message
                        user_message = await matrix_instance.catch_message(event)

                        # If the message is a command, send it to the command parser
                        if user_message[:2] == '--' or user_message[:1] == '–':
                            result = await matrix_instance.parse_command_message(
                                llm_instance, 
                                docx_instance, 
                                user_message
                            )

                        # Otherwise, Prompt the model with the user's message and post the
                        # model's response to chat
                        else: 
                            model_output = llm_instance.prompt_model(user_message)
                            result = await matrix_instance.post_message(model_output)


def main_local_text_loop(llm_instance, docx_instance):

    # Post a hello
    print('Bartleby online. Send "--commands" to see a list of available control commands or just say "Hi!".\n')
    
    while True:

        # Wait for user input
        user_message = input('User: ')
        #print(f'User message: {user_message}')

        # If the message is a command, send it to the command parser
        if user_message[:2] == '--' or user_message[:1] == '–':
            result = helper_funcs.parse_command_message(
                llm_instance, 
                docx_instance, 
                user_message
            )

            print(result)

        # Otherwise, Prompt the model with the user's message and post the
        # model's response to chat
        else: 
            model_output = llm_instance.prompt_model(user_message)
            print(model_output)
            
def run():
    '''Run bartleby'''

    # Create logger
    logger = logging.getLogger(__name__)
    handler = RotatingFileHandler(f'{config.LOG_PATH}/bartleby.log', maxBytes=20000, backupCount=10)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %I:%M:%S %p')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel('DEBUG')

    logger.info('############################################### ')
    logger.info('############## Starting bartleby ############## ')
    logger.info('############################################### ')

    # Give torch CPU resources
    logger.info(f'Using {config.CPU_threads} CPU threads')
    torch.set_num_threads(config.CPU_threads)

    # Initialize the model, tokenizer and generation configuration.
    llm_instance = llm.Llm(logger)
    llm_instance.initialize_model()
    llm_instance.initialize_model_config()
    logger.info('Model initialized successfully')

    # Initialize a new docx document for text output
    docx_instance = docx.Docx()
    logger.info('Blank docx document created')

    # Choose the right mode
    if config.MODE == 'matrix':

        logger.info('Running in Matrix mode')

        # Instantiate new matrix chat session.
        matrix_instance = matrix.Matrix(logger)
        matrix_instance.start_matrix_client()
        logger.info('Matrix chat client started successfully')

        asyncio.run(main_matrix_loop(matrix_instance, llm_instance, docx_instance))

    elif config.MODE == 'local_text':

        logger.info('Running in local text only mode')

        main_local_text_loop(llm_instance, docx_instance)
