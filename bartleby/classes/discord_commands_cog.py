import discord
import bartleby.configuration as conf
from discord.ext import commands
from discord import app_commands

async def setup(bot):
    await bot.add_cog(System_commands(bot))

class System_commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    ##### System commands ################################################
    @app_commands.command()
    async def commands(self, interaction: discord.Interaction):
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
        self.logger.debug(f'Show commands from: {user_name}')

    # @client.tree.command()
    # async def input_buffer_size(interaction: discord.Interaction):
    #     """Posts the current LLM input buffer size."""

    #     # Get the user name
    #     user_name = interaction.user

    #     # If this is the first interaction from this user, onboard them
    #     if user_name not in users.keys():
    #         users[user_name] = user.User(user_name)

    #     # Post the reply and log the interaction
    #     await interaction.response.send_message(f'```LLM using last {conf.model_input_buffer_size} messages as input```')
    #     logger.debug(f'Show input buffer size command from: {user_name}')

    # @client.tree.command()
    # @app_commands.describe(buffer_size='New input buffer size')
    # async def set_input_buffer_size(interaction: discord.Interaction, buffer_size: int):
    #     """Updates the LLM input buffer size."""

    #     # Get the user name
    #     user_name = interaction.user

    #     # If this is the first interaction from this user, onboard them
    #     if user_name not in users.keys():
    #         users[user_name] = user.User(user_name)

    #     # Make the update
    #     users[user_name].model_input_buffer_size = buffer_size

    #     # Post the reply and log the interaction
    #     await interaction.response.send_message(f'```Changed model input buffer to last {buffer_size} messages```')
    #     logger.debug(f'Update input buffer size to {buffer_size} command from: {user_name}')

    # @client.tree.command()
    # async def input_messages(interaction: discord.Interaction):
    #     """Post contents of LLM input buffer to chat."""

    #     # Get the user name
    #     user_name = interaction.user

    #     # If this is the first interaction from this user, onboard them
    #     if user_name not in users.keys():
    #         users[user_name] = user.User(user_name)

    #     # Select last n messages for input to the model
    #     messages = []

    #     for message in users[user_name].messages[-users[user_name].model_input_buffer_size:]:
    #         messages.append(f"{message['role']}: {message['content']}")

    #     result = '\n'.join(messages)

    #     # Post the reply and log the interaction
    #     await interaction.response.send_message(f'```{result}```')
    #     logger.debug(f'Show input buffer command from: {user_name}')

    # @client.tree.command()
    # async def prompt(interaction: discord.Interaction):
    #     """Post the generation prompt."""

    #     # Get the user name
    #     user_name = interaction.user

    #     # If this is the first interaction from this user, onboard them
    #     if user_name not in users.keys():
    #         users[user_name] = user.User(user_name)

    #     # Post the reply and log the interaction
    #     await interaction.response.send_message(f'```Generation prompt: {users[user_name].initial_prompt}```')
    #     logger.debug(f'Show prompt command from: {user_name}')

    # @client.tree.command()
    # @app_commands.describe(initial_prompt='New generation prompt')
    # async def set_prompt(interaction: discord.Interaction, initial_prompt: str):
    #     """Updates the generation prompt."""

    #     # Get the user name
    #     user_name = interaction.user

    #     # If this is the first interaction from this user, onboard them
    #     if user_name not in users.keys():
    #         users[user_name] = user.User(user_name)

    #     # Make the update
    #     users[user_name].initial_prompt = initial_prompt
    #     users[user_name].restart_conversation()

    #     # Post the reply and log the interaction
    #     await interaction.response.send_message(f'```Updated generation prompt: {initial_prompt}```')
    #     logger.debug(f'Update prompt command from: {user_name}. New prompt: {initial_prompt}')

    # @client.tree.command()
    # async def reset_chat(interaction: discord.Interaction):
    #     """Clear the message buffer and restart the chat"""

    #     # Get the user name
    #     user_name = interaction.user

    #     # If this is the first interaction from this user, onboard them
    #     if user_name not in users.keys():
    #         users[user_name] = user.User(user_name)

    #     # Make the update
    #     users[user_name].restart_conversation()

    #     # Post the reply and log the interaction
    #     await interaction.response.send_message(f'```Conversation reset```')
    #     logger.debug(f'Restart chat command from: {user_name}')
            

    # ##### Generation configuration commands ################################################
    # @client.tree.command()
    # async def decoding_mode(interaction: discord.Interaction):
    #     """Posts the current decoding mode"""

    #     # Get the user name
    #     user_name = interaction.user

    #     # If this is the first interaction from this user, onboard them
    #     if user_name not in users.keys():
    #         users[user_name] = user.User(user_name)

    #     # Post the reply and log the interaction
    #     await interaction.response.send_message(f'```decoding mode: {users[user_name].decoding_mode}```')
    #     logger.debug(f'Show decoding mode command from: {user_name}')

    # @client.tree.command()
    # async def decoding_modes(interaction: discord.Interaction):
    #     """Posts available decoding modes"""

    #     # Get the user name
    #     user_name = interaction.user

    #     # Post the reply and log the interaction
    #     await interaction.response.send_message(f"```Available decoding modes: {', '.join(conf.decoding_mode.keys())}```")
    #     logger.debug(f'Show decoding modes command from: {user_name}')

    # @client.tree.command()
    # @app_commands.describe(decoding_mode='New decoding mode')
    # async def set_decoding_mode(interaction: discord.Interaction, decoding_mode: str):
    #     """Sets the decoding mode during inference."""

    #     # Get the user name
    #     user_name = interaction.user

    #     # If this is the first interaction from this user, onboard them
    #     if user_name not in users.keys():
    #         users[user_name] = user.User(user_name)

    #     # Make the update
    #     users[user_name].decoding_mode = decoding_mode
    #     users[user_name].set_decoding_mode()

    #     # Post the reply and log the interaction
    #     await interaction.response.send_message(f'```Changed decoding mode to {decoding_mode}```')
    #     logger.debug(f'Update decoding mode command from: {user_name}')

    # @client.tree.command()
    # async def config(interaction: discord.Interaction):
    #     """Posts any non-model-default generation parameter values"""

    #     # Get the user name
    #     user_name = interaction.user

    #     # If this is the first interaction from this user, onboard them
    #     if user_name not in users.keys():
    #         users[user_name] = user.User(user_name)

    #     # Post the reply and log the interaction
    #     await interaction.response.send_message(f'```Non-model-default generation settings: {users[user_name].generation_configurations[users[user_name].model_type]}```')

    # @client.tree.command()
    # async def config_full(interaction: discord.Interaction):
    #     """Posts all generation parameter values"""

    #     # Get the user name
    #     user_name = interaction.user

    #     # If this is the first interaction from this user, onboard them
    #     if user_name not in users.keys():
    #         users[user_name] = user.User(user_name)

    #     # Post the reply and log the interaction
    #     await interaction.response.send_message(f'```All available generation settings: {users[user_name].generation_configurations[users[user_name].model_type].__dict__}```')

    # @client.tree.command()
    # @app_commands.describe(parameter='Parameter to update', new_value='New value')
    # async def set_config(interaction: discord.Interaction, parameter: str, new_value: str):
    #     """Updates the value of a specific generation configuration parameter."""

    #     # Get the user name
    #     user_name = interaction.user

    #     # If this is the first interaction from this user, onboard them
    #     if user_name not in users.keys():
    #         users[user_name] = user.User(user_name)

    #     # Handle string to int or float conversion - some generation
    #     # configuration parameters take ints and some take floats
    #     if '.' in new_value:
    #         val = float(new_value)
    #     else:
    #         val = int(new_value)

    #     # Set the value
    #     setattr(users[user_name].generation_configurations[users[user_name].model_type], parameter, val)

    #     # Post the reply and log the interaction
    #     await interaction.response.send_message(f'```Updated parameter {parameter}: {val}```')
    #     logger.debug(f'Show config parameter command from: {user_name}. {parameter}: {val}')

    # @client.tree.command()
    # async def model(interaction: discord.Interaction):
    #     """Posts the current model"""

    #     # Get the user name
    #     user_name = interaction.user

    #     # If this is the first interaction from this user, onboard them
    #     if user_name not in users.keys():
    #         users[user_name] = user.User(user_name)

    #     # Post the reply and log the interaction
    #     await interaction.response.send_message(f'```Current model: {users[user_name].model_type}```')
    #     logger.debug(f'Show current model command from: {user_name}')

    # @client.tree.command()
    # async def models(interaction: discord.Interaction):
    #     """Posts the available models"""

    #     # Get the user name
    #     user_name = interaction.user

    #     # If this is the first interaction from this user, onboard them
    #     if user_name not in users.keys():
    #         users[user_name] = user.User(user_name)

    #     # Post the reply and log the interaction
    #     model_list = '\n' + '\n'.join(conf.supported_models)
    #     await interaction.response.send_message(f'```{model_list}```')
    #     logger.debug(f'Show supported models command from: {user_name}')

    # @client.tree.command()
    # @app_commands.describe(model_type='New model type')
    # async def swap_model(interaction: discord.Interaction, model_type: str):
    #     """Changes the model type."""

    #     # Get the user name
    #     user_name = interaction.user

    #     # If this is the first interaction from this user, onboard them
    #     if user_name not in users.keys():
    #         users[user_name] = user.User(user_name)

    #     # Check to make sure we have the model the user asked for 
    #     if model_type in conf.supported_models:

    #         # Make the update
    #         users[user_name].model_type = model_type

    #         # Post the reply and log the interaction
    #         await interaction.response.send_message(f'```Switched to {model_type}. Note the next reply may be slow if this model is not cached or already running.```')
    #         logger.debug(f'Swap model command from: {user_name}. New model: {model_type}')

    #     else:

    #         # Post the reply and log the interaction
    #         supported_models = '\n' + '\n'.join(conf.supported_models)
    #         await interaction.response.send_message(f'```New model must be one of: {supported_models}```')
    #         logger.debug(f'Failed swap model command from: {user_name}. New model: {model_type}')


    # ##### document commands ################################################
    # @client.tree.command()
    # @app_commands.describe(gdrive_link='Google drive folder share link')
    # async def set_gdrive_folder(interaction: discord.Interaction, gdrive_link: str):
    #     """Specify gdrive shared folder for document uploads."""

    #     # Get the user name
    #     user_name = interaction.user

    #     # If this is the first interaction from this user, onboard them
    #     if user_name not in users.keys():
    #         users[user_name] = user.User(user_name)

    #     # Parse the share link
    #     gdrive_id = gdrive_link.split('/')[-1].split('?')[0]

    #     # Update it
    #     users[user_name].gdrive_folder_id = gdrive_id

    #     # Post the reply and log the interaction
    #     await interaction.response.send_message(f'```gdrive folder ID: {gdrive_id}```')
    #     logger.debug(f'Set gdrive folder command from: {user_name}')

    # @client.tree.command()
    # async def show_document_title(interaction: discord.Interaction):
    #     """Posts the current title/filename used to save documents to gdrive."""

    #     # Get the user name
    #     user_name = interaction.user

    #     # If this is the first interaction from this user, onboard them
    #     if user_name not in users.keys():
    #         users[user_name] = user.User(user_name)

    #     # Post the reply and log the interaction
    #     await interaction.response.send_message(f'```Document title: {users[user_name].document_title}```')
    #     logger.debug(f'Show document title command from: {user_name}')

    # @client.tree.command()
    # @app_commands.describe(document_title='Google drive document title')
    # async def set_document_title(interaction: discord.Interaction, document_title: str):
    #     """Specify title/filename used to save documents to gdrive."""

    #     # Get the user name
    #     user_name = interaction.user

    #     # If this is the first interaction from this user, onboard them
    #     if user_name not in users.keys():
    #         users[user_name] = user.User(user_name)

    #     # Do the update
    #     users[user_name].document_title = document_title

    #     # Post the reply and log the interaction
    #     await interaction.response.send_message(f'```Document title: {document_title}```')
    #     logger.debug(f'Set document title command from: {user_name}')

    # @client.tree.command()
    # async def make_docx(interaction: discord.Interaction):
    #     """Save last message to gdrive as docx"""

    #     # Get the user name
    #     user_name = interaction.user

    #     # If this is the first interaction from this user, onboard them
    #     if user_name not in users.keys():
    #         users[user_name] = user.User(user_name)

    #     # Check to see that the user has set a gdrive folder id
    #     # If they have, make the document
    #     if users[user_name].gdrive_folder_id != None:
            
    #         # Make the document
    #         docx_instance.generate(users[user_name], 1, None)
            
    #         # Post the reply and log the interaction
    #         await interaction.response.send_message(f'```Document generated```')
    #         logger.debug(f'Got make docx command from: {user_name}')

    #     # If they have not set a gdrive folder id, ask them to set one
    #     # before generating a document
    #     elif users[user_name].gdrive_folder_id == None:

    #         await interaction.response.send_message(f'```Please set a gdrive folder generating a document```')
    #         logger.debug(f'Got make docx command without gdrive folder id from: {user_name}')

    # # Context menu command to generate document via left click on message
    # @client.tree.context_menu(name='Save to gdrive')
    # async def save_message(interaction: discord.Interaction, message: discord.Message):

    #     # Get the user name
    #     user_name = interaction.user

    #     # Get the message text
    #     text = message.content

    #     # If this is the first interaction from this user, onboard them
    #     if user_name not in users.keys():
    #         users[user_name] = user.User(user_name)

    #     # Check to see that the user has set a gdrive folder id
    #     # If they have, make the document
    #     if users[user_name].gdrive_folder_id != None:
            
    #         # Make the document
    #         docx_instance.generate_from_text(users[user_name], text)
            
    #         # Post the reply and log the interaction
    #         await interaction.response.send_message(f'```Document generated```')
    #         logger.debug(f'Got make docx command from: {user_name}')

    #     # If they have not set a gdrive folder id, ask them to set one
    #     # before generating a document
    #     elif users[user_name].gdrive_folder_id == None:

    #         await interaction.response.send_message(f'```Please set a gdrive folder generating a document```')
    #         logger.debug(f'Got make docx command without gdrive folder id from: {user_name}')
