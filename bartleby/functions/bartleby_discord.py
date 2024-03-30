# import asyncio
import time
import discord
from discord import app_commands
# from nio import RoomMessageText
import logging

from logging.handlers import RotatingFileHandler

import bartleby.configuration as conf
import bartleby.functions.command_parsing_functions as command_funcs
import bartleby.functions.helper_functions as helper_funcs
# import bartleby.classes.llm_class as llm
# import bartleby.classes.user_class as user
import bartleby.classes.system_agent_class as system_agent
import bartleby.classes.discord_class as discord_class
# import bartleby.classes.discord_commands_cog as command_cog

def start_discord_logger():
    '''Sets up logging for discord.py'''

    logger = logging.getLogger('discord')
    logger.setLevel(conf.LOG_LEVEL)
    logging.getLogger('discord.http').setLevel(logging.INFO)

    handler = RotatingFileHandler(
        f'{conf.LOG_PATH}/discord.log',
        encoding='utf-8',
        maxBytes=32 * 1024 * 1024,  # 32 MiB
        backupCount=5,  # Rotate through 5 files
    )

    dt_fmt = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

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
    discord_logger=start_discord_logger()

    # Set intents and start the discord client
    intents=discord.Intents.default()
    intents.message_content=True
    intents.members=True
    intents.typing=False
    intents.presences=True
    client=discord_class.LLMbot(logger, response_queue, users, command_prefix='/', intents=intents)

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
    
    client.run(bot_token, log_handler=None)
