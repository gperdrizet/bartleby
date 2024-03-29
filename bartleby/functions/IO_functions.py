import asyncio
import time
import discord
from discord import app_commands
from nio import RoomMessageText

import bartleby.configuration as conf
import bartleby.functions.command_parsing_functions as command_funcs
import bartleby.functions.helper_functions as helper_funcs
import bartleby.classes.llm_class as llm
import bartleby.classes.user_class as user
import bartleby.classes.system_agent_class as system_agent
import bartleby.classes.discord_class as discord_class

def discord_listener(
    bot_token,
    docx_instance,
    users,
    llms,
    generation_queue,
    response_queue,
    logger
):
    # Start system agent
    system_agent_instance = system_agent.System_agent(logger) 

    # Set discord logging settings
    discord_logger=helper_funcs.start_discord_logger()

    # Set intents and start the discord client
    intents=discord.Intents.default()
    intents.message_content=True
    intents.members=True
    intents.typing=False
    intents.presences=True
    client=discord_class.LLMClient(logger, response_queue, command_prefix='/', intents=intents)

    @client.event
    async def on_ready():
        logger.info(f'Logged into Discord as {client.user}')

    @client.event
    async def on_message(message):
        if message.author != client.user:

            # Before we respond, we need to take a look a the channel the message came from.
            # The logic goes like this: if there is only one user present, respond to the
            # message. If there is more than one user present, only respond to the message
            # if it mentions bartleby or is a reply to one of bartleby's messages.

            # Set a flag for mentions containing bartleby
            mentions_bartleby = False

            # Set a flag for replies to bartleby
            reply_to_bartleby = False

            # Check if bartleby was mentioned
            mentions = []

            for mention in message.mentions:
                user = client.get_user(mention.id)
                mentions.append(user.name)

            if 'bartleby' in mentions or 'everyone' in mentions:
                mentions_bartleby = True

            # Check if the message is a reply to bartleby
            reference = message.reference

            if reference != None:
                referenced_message_id = reference.message_id
                reference_channel_id = reference.channel_id
                reference_channel = client.get_channel(reference_channel_id)
                reference_message = await reference_channel.fetch_message(referenced_message_id)
                sender = reference_message.author
                sender_name = sender.name

                if sender_name == 'bartleby':
                    reply_to_bartleby = True

                logger.debug(f'Message reference: {reference}')
                logger.debug(f'Referenced message ID: {referenced_message_id}')
                logger.debug(f'Original sender: {sender_name}')

            # Find out how many not offline users are in the channel that the message came from
            # Get the channel id from the message
            channel = client.get_channel(message.channel.id)

            # Get the number of not offline users in the channel - this is better than
            # getting it from the guild because in a server of x members a channel can have
            # x - n members if it is private

            online_channel_members = 0

            for member in channel.members:
                logger.debug(f'{member}: {member.status}')
                if str(member.status) != 'offline':
                    online_channel_members += 1

            # OK, now we have everything we need to decide if we should respond to the message!
            if online_channel_members > 2 and mentions_bartleby == False and reply_to_bartleby == False:

                # If there are more than bartleby + 1 people in the channel, but bartleby was not
                # mentioned in the message and it wasn't a reply to bartleby, ignore it - it must
                # be people in the channel talking to each other, not bartleby.
                logger.info('Ignoring message')

            # Otherwise, respond
            else:

                # Get the username and deal with initializing them or their LLM
                # As needed
                user_name=message.author
                message_time=helper_funcs.setup_user(logger, user_name, users, llms)

                # Get body of user message
                user_message = message.content

                # If we are reading this message because it was a reply to bartleby,
                # split off the mentioned user ID at the closing '> ' and take
                # whatever comes after
                if mentions_bartleby == True:
                    user_message = user_message.split('> ')[-1]

                logger.debug(f'+{round(time.time() - message_time, 2)}s: User message: {user_message}')

                # Check to see if it's a command message, if so, send it to the command parser
                if user_message[:2] == '--' or user_message[:1] == '–':

                    result = command_funcs.parse_command_message(docx_instance, users[user_name], user_message)
                    result = result.replace('        \r  <b>', '')
                    result = result.replace('</b>', '')
                    result = result.replace('<b>', '')
                    result = result.replace('\n\n', '\n')

                    # Post the result and log
                    await message.channel.send(f'```{result}```')
                    logger.debug(result)

                # If it's not a --command, send it to the system agent
                else:

                    # Check to see if the user's message translates to a known command
                    command = system_agent_instance.translate_command(user_message)

                    # If the user message translates to a command send it to the
                    # system agent's parser for execution
                    if command != 'None':

                        result = command_funcs.parse_system_agent_command(docx_instance, users[user_name], command)
                        result = result.replace('        \r  <b>', '')
                        result = result.replace('</b>', '')
                        result = result.replace('<b>', '')
                        result = result.replace('\n\n', '\n')

                        # Post the result and log
                        await message.channel.send(f'```{result}```')
                        logger.debug(result)

                    # If the message does not translate to a command the system agent
                    # recognizes, add it to the conversation put the user in the LLM
                    # in the LLM queue for a response
                    else:

                        users[user_name].messages.append({
                            'role': 'user',
                            'content': user_message
                        })

                        # Add the message object and time for easy parsing later on
                        users[user_name].message_object=message
                        users[user_name].message_time=message_time

                        # Use system agent to pick short or long output and set the corresponding parameters
                        output_size = system_agent_instance.select_output_size(user_message)

                        if users[user_name].decoding_mode == 'beam_search':

                            if output_size == 'long response':
                                logger.debug(f'Generating long response with beam search')
                                users[user_name].generation_configurations[users[user_name].model_type].length_penalty=conf.long_length_penalty
                            
                            elif output_size == 'short response':
                                logger.debug(f'Generating short response with beam search')
                                users[user_name].generation_configurations[users[user_name].model_type].length_penalty=conf.short_length_penalty

                        else:

                            if output_size == 'long response':
                                logger.debug(f'Generating long response with {users[user_name].decoding_mode}')
                                long_start_index = int(users[user_name].generation_configurations[users[user_name].model_type].max_new_tokens * 0.75)
                                users[user_name].generation_configurations[users[user_name].model_type].exponential_decay_length_penalty=(long_start_index, conf.long_decay_factor)
                            
                            elif output_size == 'short response':
                                logger.debug(f'Generating short response with {users[user_name].decoding_mode}')
                                users[user_name].generation_configurations[users[user_name].model_type].exponential_decay_length_penalty=(conf.short_start_index, conf.short_decay_factor)

                        # Put the user into the llm's queue
                        generation_queue.put(users[user_name])
                        logger.info(f'+{round(time.time() - message_time, 2)}s: Added {user_name} to generation queue')


    ##### System commands ################################################
    @client.tree.command()
    async def commands(interaction: discord.Interaction):
        """Posts available chat commands"""

        # Get the user name
        user_name = interaction.user

        # Get the command reference from the config file
        result = conf.commands
        result = result.replace('        \r  <b>', '')
        result = result.replace('</b>', '')
        result = result.replace('<b>', '')
        result = result.replace('\n\n', '\n')

        # Post the reply and log the interaction
        await interaction.response.send_message(f'```{result}```')
        logger.debug(f'Show commands from: {user_name}')

    @client.tree.command()
    async def input_buffer_size(interaction: discord.Interaction):
        """Posts the current LLM input buffer size."""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in users.keys():
            users[user_name] = user.User(user_name)

        # Post the reply and log the interaction
        await interaction.response.send_message(f'```LLM using last {conf.model_input_buffer_size} messages as input```')
        logger.debug(f'Show input buffer size command from: {user_name}')

    @client.tree.command()
    @app_commands.describe(buffer_size='New input buffer size')
    async def set_input_buffer_size(interaction: discord.Interaction, buffer_size: int):
        """Updates the LLM input buffer size."""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in users.keys():
            users[user_name] = user.User(user_name)

        # Make the update
        users[user_name].model_input_buffer_size = buffer_size

        # Post the reply and log the interaction
        await interaction.response.send_message(f'```Changed model input buffer to last {buffer_size} messages```')
        logger.debug(f'Update input buffer size to {buffer_size} command from: {user_name}')

    @client.tree.command()
    async def input_messages(interaction: discord.Interaction):
        """Post contents of LLM input buffer to chat."""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in users.keys():
            users[user_name] = user.User(user_name)

        # Select last n messages for input to the model
        messages = []

        for message in users[user_name].messages[-users[user_name].model_input_buffer_size:]:
            messages.append(f"{message['role']}: {message['content']}")

        result = '\n'.join(messages)

        # Post the reply and log the interaction
        await interaction.response.send_message(f'```{result}```')
        logger.debug(f'Show input buffer command from: {user_name}')

    @client.tree.command()
    async def prompt(interaction: discord.Interaction):
        """Post the generation prompt."""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in users.keys():
            users[user_name] = user.User(user_name)

        # Post the reply and log the interaction
        await interaction.response.send_message(f'```Generation prompt: {users[user_name].initial_prompt}```')
        logger.debug(f'Show prompt command from: {user_name}')

    @client.tree.command()
    @app_commands.describe(initial_prompt='New generation prompt')
    async def set_prompt(interaction: discord.Interaction, initial_prompt: str):
        """Updates the generation prompt."""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in users.keys():
            users[user_name] = user.User(user_name)

        # Make the update
        users[user_name].initial_prompt = initial_prompt
        users[user_name].restart_conversation()

        # Post the reply and log the interaction
        await interaction.response.send_message(f'```Updated generation prompt: {initial_prompt}```')
        logger.debug(f'Update prompt command from: {user_name}. New prompt: {initial_prompt}')

    @client.tree.command()
    async def reset_chat(interaction: discord.Interaction):
        """Clear the message buffer and restart the chat"""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in users.keys():
            users[user_name] = user.User(user_name)

        # Make the update
        users[user_name].restart_conversation()

        # Post the reply and log the interaction
        await interaction.response.send_message(f'```Conversation reset```')
        logger.debug(f'Restart chat command from: {user_name}')
            

    ##### Generation configuration commands ################################################
    @client.tree.command()
    async def decoding_mode(interaction: discord.Interaction):
        """Posts the current decoding mode"""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in users.keys():
            users[user_name] = user.User(user_name)

        # Post the reply and log the interaction
        await interaction.response.send_message(f'```decoding mode: {users[user_name].decoding_mode}```')
        logger.debug(f'Show decoding mode command from: {user_name}')

    @client.tree.command()
    async def decoding_modes(interaction: discord.Interaction):
        """Posts available decoding modes"""

        # Get the user name
        user_name = interaction.user

        # Post the reply and log the interaction
        await interaction.response.send_message(f"```Available decoding modes: {', '.join(conf.decoding_mode.keys())}```")
        logger.debug(f'Show decoding modes command from: {user_name}')

    @client.tree.command()
    @app_commands.describe(decoding_mode='New decoding mode')
    async def set_decoding_mode(interaction: discord.Interaction, decoding_mode: str):
        """Sets the decoding mode during inference."""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in users.keys():
            users[user_name] = user.User(user_name)

        # Make the update
        users[user_name].decoding_mode = decoding_mode
        users[user_name].set_decoding_mode()

        # Post the reply and log the interaction
        await interaction.response.send_message(f'```Changed decoding mode to {decoding_mode}```')
        logger.debug(f'Update decoding mode command from: {user_name}')

    @client.tree.command()
    async def config(interaction: discord.Interaction):
        """Posts any non-model-default generation parameter values"""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in users.keys():
            users[user_name] = user.User(user_name)

        # Post the reply and log the interaction
        await interaction.response.send_message(f'```Non-model-default generation settings: {users[user_name].generation_configurations[users[user_name].model_type]}```')

    @client.tree.command()
    async def config_full(interaction: discord.Interaction):
        """Posts all generation parameter values"""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in users.keys():
            users[user_name] = user.User(user_name)

        # Post the reply and log the interaction
        await interaction.response.send_message(f'```All available generation settings: {users[user_name].generation_configurations[users[user_name].model_type].__dict__}```')

    @client.tree.command()
    @app_commands.describe(parameter='Parameter to update', new_value='New value')
    async def set_config(interaction: discord.Interaction, parameter: str, new_value: str):
        """Updates the value of a specific generation configuration parameter."""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in users.keys():
            users[user_name] = user.User(user_name)

        # Handle string to int or float conversion - some generation
        # configuration parameters take ints and some take floats
        if '.' in new_value:
            val = float(new_value)
        else:
            val = int(new_value)

        # Set the value
        setattr(users[user_name].generation_configurations[users[user_name].model_type], parameter, val)

        # Post the reply and log the interaction
        await interaction.response.send_message(f'```Updated parameter {parameter}: {val}```')
        logger.debug(f'Show config parameter command from: {user_name}. {parameter}: {val}')

    @client.tree.command()
    async def model(interaction: discord.Interaction):
        """Posts the current model"""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in users.keys():
            users[user_name] = user.User(user_name)

        # Post the reply and log the interaction
        await interaction.response.send_message(f'```Current model: {users[user_name].model_type}```')
        logger.debug(f'Show current model command from: {user_name}')

    @client.tree.command()
    async def models(interaction: discord.Interaction):
        """Posts the available models"""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in users.keys():
            users[user_name] = user.User(user_name)

        # Post the reply and log the interaction
        model_list = '\n' + '\n'.join(conf.supported_models)
        await interaction.response.send_message(f'```{model_list}```')
        logger.debug(f'Show supported models command from: {user_name}')

    @client.tree.command()
    @app_commands.describe(model_type='New model type')
    async def swap_model(interaction: discord.Interaction, model_type: str):
        """Changes the model type."""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in users.keys():
            users[user_name] = user.User(user_name)

        # Check to make sure we have the model the user asked for 
        if model_type in conf.supported_models:

            # Make the update
            users[user_name].model_type = model_type

            # Post the reply and log the interaction
            await interaction.response.send_message(f'```Switched to {model_type}. Note the next reply may be slow if this model is not cached or already running.```')
            logger.debug(f'Swap model command from: {user_name}. New model: {model_type}')

        else:

            # Post the reply and log the interaction
            supported_models = '\n' + '\n'.join(conf.supported_models)
            await interaction.response.send_message(f'```New model must be one of: {supported_models}```')
            logger.debug(f'Failed swap model command from: {user_name}. New model: {model_type}')


    ##### document commands ################################################
    @client.tree.command()
    @app_commands.describe(gdrive_link='Google drive folder share link')
    async def set_gdrive_folder(interaction: discord.Interaction, gdrive_link: str):
        """Specify gdrive shared folder for document uploads."""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in users.keys():
            users[user_name] = user.User(user_name)

        # Parse the share link
        gdrive_id = gdrive_link.split('/')[-1].split('?')[0]

        # Update it
        users[user_name].gdrive_folder_id = gdrive_id

        # Post the reply and log the interaction
        await interaction.response.send_message(f'```gdrive folder ID: {gdrive_id}```')
        logger.debug(f'Set gdrive folder command from: {user_name}')

    @client.tree.command()
    async def show_document_title(interaction: discord.Interaction):
        """Posts the current title/filename used to save documents to gdrive."""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in users.keys():
            users[user_name] = user.User(user_name)

        # Post the reply and log the interaction
        await interaction.response.send_message(f'```Document title: {users[user_name].document_title}```')
        logger.debug(f'Show document title command from: {user_name}')

    @client.tree.command()
    @app_commands.describe(document_title='Google drive document title')
    async def set_document_title(interaction: discord.Interaction, document_title: str):
        """Specify title/filename used to save documents to gdrive."""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in users.keys():
            users[user_name] = user.User(user_name)

        # Do the update
        users[user_name].document_title = document_title

        # Post the reply and log the interaction
        await interaction.response.send_message(f'```Document title: {document_title}```')
        logger.debug(f'Set document title command from: {user_name}')

    @client.tree.command()
    async def make_docx(interaction: discord.Interaction):
        """Save last message to gdrive as docx"""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in users.keys():
            users[user_name] = user.User(user_name)

        # Check to see that the user has set a gdrive folder id
        # If they have, make the document
        if users[user_name].gdrive_folder_id != None:
            
            # Make the document
            docx_instance.generate(users[user_name], 1, None)
            
            # Post the reply and log the interaction
            await interaction.response.send_message(f'```Document generated```')
            logger.debug(f'Got make docx command from: {user_name}')

        # If they have not set a gdrive folder id, ask them to set one
        # before generating a document
        elif users[user_name].gdrive_folder_id == None:

            await interaction.response.send_message(f'```Please set a gdrive folder generating a document```')
            logger.debug(f'Got make docx command without gdrive folder id from: {user_name}')

    # Context menu command to generate document via left click on message
    @client.tree.context_menu(name='Save to gdrive')
    async def save_message(interaction: discord.Interaction, message: discord.Message):

        # Get the user name
        user_name = interaction.user

        # Get the message text
        text = message.content

        # If this is the first interaction from this user, onboard them
        if user_name not in users.keys():
            users[user_name] = user.User(user_name)

        # Check to see that the user has set a gdrive folder id
        # If they have, make the document
        if users[user_name].gdrive_folder_id != None:
            
            # Make the document
            docx_instance.generate_from_text(users[user_name], text)
            
            # Post the reply and log the interaction
            await interaction.response.send_message(f'```Document generated```')
            logger.debug(f'Got make docx command from: {user_name}')

        # If they have not set a gdrive folder id, ask them to set one
        # before generating a document
        elif users[user_name].gdrive_folder_id == None:

            await interaction.response.send_message(f'```Please set a gdrive folder generating a document```')
            logger.debug(f'Got make docx command without gdrive folder id from: {user_name}')

    client.run(bot_token, log_handler=None)

async def matrix_listener_loop(
    docx_instance, 
    matrix_instance, 
    users, 
    llms, 
    generation_queue, 
    response_queue, 
    logger
):
    '''Watches for messages from users in the matrix room, when it finds
    one, handles routing that user to an LLM'''

    system_agent_instance = system_agent.System_agent(logger) 

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
                    logger.info(f'0.00 s: Caught message from {user_name} mentioning bartleby')

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
                        logger.info(f"+{round(time.time() - message_time, 2)} s: Initialized {users[user_name].model_type} model for {user_name}")

                    else:
                        logger.info(f"+{round(time.time() - message_time, 2)} s: Already have {users[user_name].model_type} running for {user_name}")

                    # Check if the user has a configuration set for this type of model
                    if users[user_name].model_type not in users[user_name].generation_configurations.keys():

                        # If not, get the default generation configuration that came from 
                        # the model's initialization and give it to the user so they can have their
                        # own copy to modify at will
                        model_default_generation_configuration = llms[users[user_name].model_type].default_generation_configuration
                        users[user_name].generation_configurations[users[user_name].model_type] = model_default_generation_configuration
                        users[user_name].set_generation_mode()
                        logger.info(f'+{round(time.time() - message_time, 2)} s: Set generation configuration for {user_name} with {users[user_name].generation_mode} defaults')

                    # Get body of user message
                    user_message = await matrix_instance.catch_message(event)
                    logger.debug(f'+{round(time.time() - message_time, 2)} s: User message: {user_message}')

                    # Check to see if it's a command message, if so, send it to the command parser
                    if user_message[:2] == '--' or user_message[:1] == '–':

                        result = command_funcs.parse_command_message(docx_instance, users[user_name], user_message)
                        _ = await matrix_instance.post_system_message(result, user_name)

                    # If it's not a --command, send it to the system agent
                    else:

                        # Check to see if the user's message translates to a known command
                        command = system_agent_instance.translate_command(user_message)

                        # If the user message translates to a command send it to the
                        # system agent's parser for execution
                        if command != 'None':

                            result = command_funcs.parse_system_agent_command(docx_instance, users[user_name], command)
                            _ = await matrix_instance.post_system_message(result, user_name)
                            
                        # If the users message does not translate to a command, add it
                        # to their message history and send them to the model for inference
                        elif command == 'None':

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
            logger.info(f'+{round(time.time() - message_time, 2)} s: Responder got {queued_user.user_name} from generator')

            # Post the new response from the users conversation
            _ = await matrix_instance.post_message(queued_user)
            response_queue.task_done()
            logger.info(f'+{round(time.time() - message_time, 2)} s: Posted reply to {queued_user.user_name} in chat')


def generator(llms, generation_queue, response_queue, logger):
    '''Takes a user from the listener and generates a reply.
    Sends the reply to the responder.'''

    # Do this forever
    while True:
        
        # Get the next user from the generation input queue
        queued_user = generation_queue.get()

        # Send the user for generation
        _ = llms[queued_user.model_type].prompt_model(queued_user)
        generation_queue.task_done()

        # Send the user to responder to post the LLM's response
        response_queue.put(queued_user)

# Wrapper function to start the matrix listener loop via asyncIO in a thread
def matrix_listener(docx_instance, matrix_instance, users, llms, generation_queue, response_queue, logger):
    asyncio.run(matrix_listener_loop(docx_instance, matrix_instance, users, llms, generation_queue, response_queue, logger))
