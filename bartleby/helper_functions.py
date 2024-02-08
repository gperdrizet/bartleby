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
        result = f'Prompt: {llm_instance.messages[0]["content"]}'

    # Update prompt with user input and reset message chain
    elif command[0] == '--update-prompt':
        llm_instance.messages = [{'role': 'system', 'content': ' '.join(command[1:])}]
        result = 'Prompt update complete'

    # Generate docx document from document title and last chatbot response.
    # Save to documents and upload to gdrive
    elif command[0] == '--make-docx':
        _ = document.generate(llm_instance)
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
        commands = '''<strong>Available commands:</strong>\n
        <strong>--commands</strong> Posts this message to chat.\n
        <strong>--title TITLE</strong> Sets the document title with user input title from chat. The title is used to create the docx output file name: TITLE.docx.\n
        <strong>--show-prompt</strong> Posts the prompt used to start the current message chain to chat.\n
        <strong>--update-prompt PROMPT</strong> Updates the prompt with user input PROMPT from chat. Restarts the message chain with new prompt.\n
        <strong>--make-docx</strong> Generates docx document from bot's last response in chat, uploads to google drive.\n
        <strong>--restart</strong> Restarts model with defaults from configuration file.\n
        <strong>--show-config</strong> Posts generation config values that differ from model default configuration to chat.\n
        <strong>--show-config-full</strong> Posts full generation configuration to chat.\n
        <strong>--update-config PARAMETER NEW_VALUE</strong> Updates parameter to new value.\n
        <strong>--reset-config</strong> Resets generation configuration to startup defaults from configuration file.\n
        '''

        commands = commands.replace('    ', '')
        result = commands

    # If we didn't recognize the command, post an error to chat
    else:
        result = f'Unrecognized command: {command[0]}'

    return result