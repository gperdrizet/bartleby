import os
from nio import AsyncClient

import bartleby.configuration as conf

class Matrix:
    '''Class to hold session objects related to matrix chat'''

    def __init__(self, logger):

        # Matrix server related stuff.
        self.matrix_server_url = conf.matrix_server_url
        self.matrix_room_id = conf.matrix_room_id
        self.matrix_bot_username = conf.matrix_bot_username
        self.matrix_bot_password = conf.matrix_bot_password
        self.next_batch_token_file = conf.NEXT_BATCH_TOKEN_FILE

        # Add logger
        self.logger = logger

    def start_matrix_client(self):

        # Fire up the matrix client.
        self.async_client = AsyncClient(
            self.matrix_server_url,
            self.matrix_bot_username
        )

        # Read the previously-written next batch token if it exists and feed it to the nio 
        # AsyncClient so that we don't see all prior messages in the room as 'new' events.
        if os.path.isfile(self.next_batch_token_file):
            with open (self.next_batch_token_file,'r') as next_batch_token:
                self.async_client.next_batch = next_batch_token.read()

    async def post_message(self, message, recipient='None'):

        # Get rid of any <strong> tags in message for unformatted body
        body = message.replace('<strong>', '').replace('</strong>', '')

        # Replace \n with html <br> for formatted body
        formatted_body = message.replace('\n', '<br>')

        # Format output as matrix message
        content = {
            'msgtype': 'm.text',
            'format': 'org.matrix.custom.html'
        }

        # Add mention for recipient if we have one, if not just
        # add the message
        if recipient == 'None':
            content['body'] = body
            content['formatted_body'] = formatted_body

        elif recipient != 'None':
            content['body'] = f'{recipient}: {body}'
            content['formatted_body'] = f'<a href="https://matrix.to/#/@{recipient}:perdrizet.org">{recipient}</a>: {formatted_body}'
            content['m.mentions'] = {'user_ids': [f'@{recipient}:perdrizet.org']}
        
        # Post message to room
        result = await self.async_client.room_send(
            self.matrix_room_id, 
            'm.room.message', 
            content
        )

        # Then set lavern's state to 'not typing'..
        result = await self.async_client.room_typing(
            self.matrix_room_id,
            typing_state = False
        )

        return True

    async def catch_message(self, event):

        self.logger.info('Caught user message mentioning bartleby')
        self.logger.debug(event)

        # Get event id for user's message
        user_message_event_id = event.event_id

        # Mark the message as read by the bot in chat
        await self.async_client.update_receipt_marker(
            self.matrix_room_id, 
            user_message_event_id, 
        )

        # Then set the bot's state to 'typing' with a timeout
        # of ten minutes, in case it takes a while to come
        # up with a response
        await self.async_client.room_typing(
            self.matrix_room_id,
            typing_state = True, 
            timeout = 600000
        )

        # Get body of message.
        user_message = event.body.rstrip()

        # Since bartleby only responds to messages which mention him,
        # clip the mention off of the start of the message
        user_message = user_message.replace('bartleby: ', '')

        return user_message

    async def parse_command_message(self, llm_instance, document, command_message, user):
        '''Takes a user message that contains a command and runs the 
        command'''

        # Fix long dash that sometimes gets substituted for two short
        # dashes by autocorrect
        formatted_command_message = command_message.replace('–', '--')

        # Split the command message into words
        command = formatted_command_message.split(' ')

        self.logger.info(f'Caught user command: {command}')

        # Update docx document title
        if command[0] == '--title':
            document.title = ' '.join(command[1:])
            message = f'Document title set to: {document.title}'
            result = await self.post_message(message)

        # Post current prompt to chat
        elif command[0] == '--show-prompt':
            message = f'Prompt: {llm_instance.messages[0]["content"]}'
            result = await self.post_message(message)

        # Update prompt with user input and reset message chain
        elif command[0] == '--update-prompt':
            llm_instance.messages[user] = [{'role': 'system', 'content': ' '.join(command[1:])}]
            message = 'Prompt update complete'
            result = await self.post_message(message)

        # Generate docx document from document title and last chatbot response.
        # Save to documents and upload to gdrive
        elif command[0] == '--make-docx':
            result = await document.async_generate(llm_instance, user)
            message = 'Document complete'
            result = await self.post_message(message)
        
        # Restart the model, tokenizer and message chain with the default prompt
        elif command[0] == '--restart':
            llm_instance.restart_model()
            message = 'Model restarted'
            result = await self.post_message(message)

        # Post non-model default generation configuration options to chat
        elif command[0] == '--show-config':
            message = f'{llm_instance.gen_cfg}\n'
            result = await self.post_message(message)

        # Post all generation configurations options to chat
        elif command[0] == '--show-config-full':
            message = f'{llm_instance.gen_cfg.__dict__}\n'
            result = await self.post_message(message)

        # Update generation configuration option with user input
        elif command[0] == '--update-config':

            # Get the initial value for the parameter specified by user
            old_value = getattr(llm_instance.gen_cfg, command[1])

            # Handle string to int or float conversion - some generation
            # configuration parameters take ints and some take floats
            if '.' in command[2]:
                val = float(command[2])
            else:
                val = int(command[2])

            # Set and check the new value
            setattr(llm_instance.gen_cfg, command[1], val)
            new_value = getattr(llm_instance.gen_cfg, command[1])
            message = f'Updated {command[1]} from {old_value} to {new_value}'
            result = await self.post_message(message)

        # Reset generation configuration to model/configuration.py defaults
        elif command[0] == '--reset-config':
            llm_instance.initialize_model_config()
            message = 'Model generation configuration reset'
            result = await self.post_message(message)

        # Post commands to chat
        elif command[0] == '--commands':
            message = '''<strong>Available commands:</strong>\n
            <strong>--commands</strong> Posts this message to chat.
            <strong>--title TITLE</strong> Sets the document title with user input title from chat. The title is used to create the docx output file name: TITLE.docx.
            <strong>--show-prompt</strong> Posts the prompt used to start the current message chain to chat.
            <strong>--update-prompt PROMPT</strong> Updates the prompt with user input PROMPT from chat. Restarts the message chain with new prompt.
            <strong>--make-docx</strong> Generates docx document from bot's last response in chat, uploads to google drive.
            <strong>--restart</strong> Restarts model with defaults from configuration file.
            <strong>--show-config</strong> Posts generation config values that differ from model default configuration to chat.
            <strong>--show-config-full</strong> Posts full generation configuration to chat.
            <strong>--update-config PARAMETER NEW_VALUE</strong> Updates parameter to new value.
            <strong>--reset-config</strong> Resets generation configuration to startup defaults from configuration file.
            '''

            message = message.replace('    ', '')
            result = await self.post_message(message)

        # If we didn't recognize the command, post an error to chat
        else:
            message = f'Unrecognized command: {command[0]}'
            result = await self.post_message(message)

        self.logger.info(f'{message}')