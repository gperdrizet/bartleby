import bartleby.configuration as conf

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
        result = conf.commands

    # Show the current LLM input buffer size
    elif command[0] == '--input-buffer-size':
        result = f'LLM input buffer size: last {user.model_input_buffer_size} messages'

    # Set the LLM input buffer size
    elif command[0] == '--set-input-buffer-size':
        if len(command) == 2:

            user.model_input_buffer_size = int(command[1])
            result = f'LLM input buffer updated to last {user.model_input_buffer_size} messages'

        else:
            result = f'Failed to parse buffer size update command'

    # Post current contents of LLM input buffer
    elif command[0] == '--input-messages':

        # Select last n messages for input to the model
        messages = []

        for message in user.messages[-user.model_input_buffer_size:]:
            messages.append(f"{message['role']}: {message['content']}\n")

        result = '\n' + '\n'.join(messages)

    # Post current prompt to chat
    elif command[0] == '--prompt':
        result = f'Prompt: {user.initial_prompt}'

    # Update prompt with user input and reset message chain
    elif command[0] == '--set-prompt':
        user.initial_prompt = ' '.join(command[1:])
        user.restart_conversation()
        result = 'Prompt update complete, conversation reset'

    # Clear chat history and reinitialize with current initial prompt
    elif command[0] == '--reset-chat':
        user.restart_conversation()
        result = 'Chat history cleared and conversation reset'

    # Show current decoding mode
    elif command[0] == '--decoding-mode':
        result = f'Decoding mode: {user.decoding_mode}'

    # Show available decoding modes
    elif command[0] == '--decoding-modes':
        decoding_modes = ', '.join(conf.decoding_mode.keys())
        result = f'Decoding modes: {decoding_modes}'

    # Set new decoding mode
    elif command[0] == '--set-decoding-mode':
        if len(command) == 2 and command[1] in conf.decoding_mode.keys():
            user.decoding_mode = command[1]
            user.set_decoding_mode()
            result = f'Decoding mode set to {command[1]}'
        
        else:
            result = 'Could not parse decoding mode set command'

    # Post non-model default generation configuration options to chat
    elif command[0] == '--config':
        result = f'{user.generation_configurations[user.model_type]}\n'

    # Post all generation configurations options to chat
    elif command[0] == '--config-full':
        result = f'{user.generation_configurations[user.model_type].__dict__}\n'

    # Update generation configuration option with user input
    elif command[0] == '--set-config':
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

    # Post the current model in chat
    elif command[0] == '--model':
        result = f'Current model: {user.model_type}'

    # List the supported models in chat
    elif command[0] == '--models':
        models = '\n'.join(conf.supported_models)
        result = '\n' + f'{models}'

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
        if len(command) >= 2:
            user.document_title = ' '.join(command[1:])
            result = f'Document title updated'

        else:
            result = 'Failed to parse document title update command'

    # Sets Google Drive folder ID for document upload
    elif command[0] == '--set-gdrive-folder':
        if len(command) == 2:
            # Parse the share link
            gdrive_link = command[1]
            gdrive_id = gdrive_link.split('/')[-1].split('?')[0]
            user.gdrive_folder_id = gdrive_id 
            result = f'Gdrive folder set to {gdrive_id}'

        else:
            result = 'Failed to parse Google Drive folder ID update command'

    # Makes and uploads docx document to Google Drive 
    elif command[0] == '--make-docx':

        # Check to see that the user has set a gdrive folder id
        # If they have, make the document
        if user.gdrive_folder_id != None:

            # If it's a bare generate command with no argument, make the
            # document from the last message in the users chat history
            if len(command) == 1:
                docx_instance.generate(user, 1, None)

            # If the generate command is followed by one argument, use that
            # to select the message to convert into docx
            elif len(command) == 2:
                docx_instance.generate(user, int(command[1]), None)

            # If the generation command is followed by two arguments
            # select a message range to convert to docx
            elif len(command) == 3:
                docx_instance.generate(user, int(command[1]), int(command[2]))

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


def parse_system_agent_command(docx_instance, user, command):

    if command == 'restart chat':
        user.restart_conversation()
        result = 'Chat history cleared and conversation reset'

    elif command == 'show prompt':
        result = f'Prompt: {user.initial_prompt}'

    elif command == 'show config':
        result = f'{user.generation_configurations[user.model_type]}\n'

    elif command == 'buffer size':
        result = f'LLM input buffer size: last {user.model_input_buffer_size} messages'

    elif 'set input buffer' in command:
        user.model_input_buffer_size = int(command.split(' ')[3])
        result = f'LLM input buffer updated to last {user.model_input_buffer_size} messages'

    elif 'output length' in command:

        # Get the new token count as int
        num_tokens = int(command.split(' ')[2])

        # Get the old token count
        old_value = user.generation_configurations[user.model_type].max_new_tokens

        # Set and check the new value
        user.generation_configurations[user.model_type].max_new_tokens = num_tokens
        new_value = user.generation_configurations[user.model_type].max_new_tokens
        result = f"Updated {' '.join(command.split(' ')[:2])} from {old_value} to {new_value}"

    elif 'temperature' in command:

        # Get the new temp as float
        temperature = float(command.split(' ')[1])

        # Get the old temp
        old_value = user.generation_configurations[user.model_type].temperature

        # Set and check the new value
        user.generation_configurations[user.model_type].temperature = temperature
        new_value = user.generation_configurations[user.model_type].temperature
        result = f'Updated {command[0]} from {old_value} to {new_value}'

    elif 'set title' in command:
        doc_title = command.split(' ')[2:]

        user.document_title = ' '.join(doc_title)
        result = f'Document title updated to: {doc_title}'

    elif 'set gdrive folder' in command:
        url = command.split(' ')[3]
        folder_id = url[-2]
        user.gdrive_folder_id = folder_id
        result = f'Gdrive folder id updated: {folder_id}'

    elif command == 'make docx':
        # Check to see that the user has set a gdrive folder id
        # If they have, make the document

        if user.gdrive_folder_id != None:

            # Make the document from the last message in the users chat history
            docx_instance.generate(user, 1, None)

            result = 'Document generated'

        # If they have not set a gdrive folder id, ask them to set one
        # before generating a document
        elif user.gdrive_folder_id == None:
            result = 'Please set a Google Drive folder ID before generating a document for upload'

    elif command == 'supported models':
        models = '\n'.join(conf.supported_models)
        result = '\n' + f'{models}'

    elif command == 'document title':
        result = f'Document title: {user.document_title}'

    elif command.split(' ')[:2] == 'swap model':
        new_model = command.split(' ')[-1]
        user.model_type = new_model
        result = f'Switched to {new_model} model'

    elif command == 'commands':

        result = conf.commands

    # If we didn't recognize the command, post an error to chat
    else:
        result = f'Unrecognized command: {command}'

    return result
