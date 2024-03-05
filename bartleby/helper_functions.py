import glob
import logging
import os
import bartleby.configuration as conf
from logging.handlers import RotatingFileHandler

def start_logger():
    '''Sets up logging, returns logger'''

    # Clear logs if asked
    if conf.CLEAR_LOGS == True:
        for file in glob.glob(f'{conf.LOG_PATH}/*.log*'):
            os.remove(file)

    # Create logger
    logger = logging.getLogger(__name__)
    handler = RotatingFileHandler(f'{conf.LOG_PATH}/bartleby.log', maxBytes=20000, backupCount=10)
    formatter = logging.Formatter(conf.LOG_PREFIX, datefmt='%Y-%m-%d %I:%M:%S %p')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(conf.LOG_LEVEL)

    logger.info('############################################### ')
    logger.info('############## Starting bartleby ############## ')
    logger.info('############################################### ')

    return logger

def parse_command_message(docx_instance, user, command_message):
    '''Takes a user message that contains a command and runs the 
    command'''

    # Fix long dash that sometimes gets substituted for two short
    # dashes by autocorrect
    formatted_command_message = command_message.replace('–', '--')

    # Split the command message into words
    command = formatted_command_message.split(' ')

    # Post commands to chat
    if command[0] == '--commands':
        
        commands = '''\n<b>Available commands:</b>\n
        \r  <b>--commands</b>                      Posts this message to chat.
        \r  <b>--input-buffer-size</b>             Post size of LLM input buffer.
        \r  <b>--update-input-buffer N</b>         Updates LLM input buffer to last N messages.
        \r  <b>--show-input-messages</b>           Posts current content of LLM input buffer.
        \r  <b>--show-prompt</b>                   Post the current system prompt to chat.
        \r  <b>--update-prompt PROMPT</b>          Updates the system prompt to PROMPT and restarts chat history.
        \r  <b>--restart-chat</b>                  Clears and restarts chat history.
        \r  <b>--show-config</b>                   Post generation configuration parameters not set to model default.
        \r  <b>--show-config-full</b>              Show all available generation configuration parameters.
        \r  <b>--show-config-value PARAMETER</b>   Show the value of generation configuration PARAMETER.
        \r  <b>--update-config PARAMETER VALUE</b> Updates generation configuration PARAMETER to VALUE.
        \r  <b>--swap-model MODEL</b>              Change the model type used for generation.
        \r  <b>--document-title</b>                Posts current Google Doc document title to chat.
        \r  <b>--set-document-title</b>            Updates Google Doc document title.
        \r  <b>--set-gdrive-folder FOLDER</b>      Set Google Drive folder ID for document upload. 
        \r  <b>--make-docx N</b>                   Makes and uploads docx document to Google Drive where N is the reverse index in chat history, e.g. 1 is the last message, 2 the second to last etc. If N is omitted, defaults to last message.
        '''

        result = commands

    # Show the current LLM input buffer size
    elif command[0] == '--input-buffer-size':
        result = f'LLM input buffer size: last {user.model_input_buffer_size} messages'

    # Set the LLM input buffer size
    elif command[0] == '--update-input-buffer':
        if len(command) == 2:

            user.model_input_buffer_size = int(command[1])
            result = f'LLM input buffer updated to last {user.model_input_buffer_size} messages'

        else:
            result = f'Failed to parse buffer size update command'

    # Post current contents of LLM input buffer
    elif command[0] == '--show-input-messages':

        # Select last n messages for input to the model
        messages = []

        for message in user.messages[-user.model_input_buffer_size:]:
            messages.append(f"{message['role']}: {message['content']}")

        result = '\n' + '\n'.join(messages)

    # Post current prompt to chat
    elif command[0] == '--show-prompt':
        result = f'Prompt: {user.initial_prompt}'

    # Update prompt with user input and reset message chain
    elif command[0] == '--update-prompt':
        user.initial_prompt = ' '.join(command[1:])
        user.restart_conversation()
        result = 'Prompt update complete, conversation reset'

    # Clear chat history and reinitialize with current initial prompt
    elif command[0] == '--restart-chat':
        user.restart_conversation()
        result = 'Chat history cleared and conversation reset'

    # Post non-model default generation configuration options to chat
    elif command[0] == '--show-config':
        result = f'{user.generation_configurations[user.model_type]}\n'

    # Post all generation configurations options to chat
    elif command[0] == '--show-config-full':
        result = f'{user.generation_configurations[user.model_type].__dict__}\n'

    # Post value of specific generation configuration command to output
    elif command[0] == '--show-config-value':
        if len(command) == 2:
            value = getattr(user.generation_configurations[user.model_type], command[1])
            result = f'{command[1]}: {value}'

    # Update generation configuration option with user input
    elif command[0] == '--update-config':
        if len(command) == 3:

            # Get the initial value for the parameter specified by user
            old_value = getattr(user.generation_configurations[user.model_type], command[1])

            # Handle string to int or float conversion - some generation
            # configuration parameters take ints and some take floats
            if '.' in command[2]:
                val = float(command[2])
            else:
                val = int(command[2])

            # Set and check the new value
            setattr(user.generation_configurations[user.model_type], command[1], val)
            new_value = getattr(user.generation_configurations[user.model_type], command[1])
            result = f'Updated {command[1]} from {old_value} to {new_value}'

        else:
            result = f'Failed to parse generation configuration update command'

    # Update model used for generation
    elif command[0] == '--swap-model':
        if len(command) == 2:
            user.model_type = command[1]
            result = f'Switched to {command[1]} model. Next response may be slow if this model type is not already running or in the cache.'

        else:
            result = 'Failed to parse model update command'

    # Posts current Google Docs document title to chat
    elif command[0] == '--document-title':
        result = f'Document title: {user.document_title}'

    # Sets document title
    elif command[0] == '--set-document-title':
        if len(command) == 2:
            user.document_title = command[1]
            result = f'Document title updated'

        else:
            result = 'Failed to parse document title update command'

    # Sets Google Drive folder ID for document upload
    elif command[0] == '--set-gdrive-folder':
        if len(command) == 2:
            user.gdrive_folder_id = command[1]
            result = 'Gdrive folder updated'

        else:
            result = 'Failed to parse Google Drive folder ID update command'

    # Makes and uploads docx document to Google Drive 
    elif command[0] == '--make-docx':

        # Check to see that the user has set a gdrive folder id
        # If they have, make the document
        if user.gdrive_folder_id != None:

            # If it's a bare generate command with no argument, make the
            # document from the last message in the users chant history
            if len(command) == 1:
                _ = docx_instance.generate(user, 1)

            # If the generate command is followed by an argument, use that
            # to select the message to convert into docx
            elif len(command) == 2:
                _ = docx_instance.generate(user, int(command[1]))

            else:
                result = 'Failed to parse document generation command'

            result = 'Document generated'

        # If they have not set a gdrive folder id, ask them to set one
        # before generating a document
        elif user.gdrive_folder_id == None:
            result = 'Please set a Google Drive folder ID before generating a document for upload'

        
    # If we didn't recognize the command, post an error to chat
    else:
        result = f'Unrecognized command: {command[0]}'

    return result