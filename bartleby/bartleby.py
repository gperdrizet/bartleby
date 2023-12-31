import asyncio
from nio import RoomMessageText

import bartleby.matrix_class as matrix
import bartleby.llm_class as llm
import bartleby.docx_class as docx

async def main_loop(matrix_instance, llm_instance, docx_instance):

    # Log bot into the matrix server and post a hello
    result = await matrix_instance.async_client.login(matrix_instance.matrix_bot_password)
    result = await matrix_instance.post_message('Bartleby online. Send "--commands" to see a list of available control commands or just say "Hi!".')
    
    while True:

        # Poll the matrix server
        sync_response = await matrix_instance.async_client.sync(300000)

        # Write the next-batch token to a file here for the next restart
        with open(matrix_instance.next_batch_token_file, 'w') as next_batch_token:
            next_batch_token.write(sync_response.next_batch)

        # Check to make sure that the bot has been joined to the room
        if matrix_instance.matrix_room_id in sync_response.rooms.join:

            # Get events in the room
            for event in sync_response.rooms.join[matrix_instance.matrix_room_id].timeline.events:
                
                # If the event is a message...
                if isinstance(event, RoomMessageText):

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

def run():

    print('\nStarting bartleby')

    # Instantiate new matrix chat session.
    matrix_instance = matrix.Matrix()
    matrix_instance.start_matrix_client()
    print('Matrix chat client started successfully\n')

    # Initialize the model, tokenizer and generation configuration.
    llm_instance = llm.Llm()
    llm_instance.initialize_model()
    llm_instance.initialize_model_config()
    print('Model initialized successfully')

    # Initialize a new docx document for text output
    docx_instance = docx.Docx()
    print('Blank docx document created\n')

    # Run the main loop.
    asyncio.run(main_loop(matrix_instance, llm_instance, docx_instance))
