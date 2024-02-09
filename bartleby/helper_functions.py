def parse_command_message(llm_instance, document, command_message):
    '''Takes a user message that contains a command and runs the 
    command'''

    # Fix long dash that sometimes gets substituted for two short
    # dashes by autocorrect
    formatted_command_message = command_message.replace('–', '--')

    # Split the command message into words
    command = formatted_command_message.split(' ')

    # Update docx document title
    if command[0] == '--title':
        document.title = ' '.join(command[1:])
        result = f'Document title set to: {document.title}'

    # Post current prompt to chat
    elif command[0] == '--show-prompt':
        result = f'Prompt:\n{llm_instance.messages[0]["content"]}'

    # Update prompt with user input and reset message chain
    elif command[0] == '--update-prompt':
        llm_instance.messages = [{'role': 'system', 'content': ' '.join(command[1:])}]
        result = 'Prompt update complete'

    # Show the current number of messages in the buffer
    elif command[0] == '--buffer-length':
        result = f'Chat buffer contains {len(llm_instance.messages)} messages'

    # Generate docx document from document title and last n chatbot responses.
    # Save to documents and upload to gdrive
    elif command[0] == '--make-docx':
        _ = document.generate(llm_instance, int(command[1]))
        result = 'Document complete'
    
    # Restart the model, tokenizer and message chain with the default prompt
    elif command[0] == '--restart':
        llm_instance.restart_model()
        result = 'Model restarted'

    # Post non-model default generation configuration options to chat
    elif command[0] == '--show-config':
        result = f'{llm_instance.gen_cfg}\n'

    # Post all generation configurations options to chat
    elif command[0] == '--show-config-full':
        result = f'{llm_instance.gen_cfg.__dict__}\n'

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
        result = f'Updated {command[1]} from {old_value} to {new_value}'

    # Reset generation configuration to model/configuration.py defaults
    elif command[0] == '--reset-config':
        llm_instance.initialize_model_config()
        result = 'Model generation configuration reset'

    # Post commands to chat
    elif command[0] == '--commands':
        
        commands = '''\nAvailable commands:\n
        \r  --commands                   Posts this message to chat.
        \r  --title TITLE                Sets the document title with user input title from chat.
        \r  --show-prompt                Posts the prompt used to start the current message chain to chat.
        \r  --update-prompt PROMPT       Updates the prompt with user input PROMPT from chat. 
        \r                               Restarts the message chain with new prompt.
        \r  --buffer-length              Prints the number of messages currently in the buffer.
        \r  --make-docx N                Generates docx document on google drive containing the last N
        \r                               messages from the buffer.
        \r  --restart                    Restarts model with defaults from configuration file.
        \r  --show-config                Posts generation config values that differ from model default 
        \r                               configuration to chat.
        \r  --show-config-full           Posts full generation configuration to chat.
        \r  --update-config PARAM VALUE  Updates parameter to value.
        \r  --reset-config               Resets generation configuration to startup defaults from 
        \r                               configuration file.
        '''
        result = commands

    # If we didn't recognize the command, post an error to chat
    else:
        result = f'Unrecognized command: {command[0]}'

    return result