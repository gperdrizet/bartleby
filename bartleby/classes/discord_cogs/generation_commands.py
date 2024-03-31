import discord
import bartleby.configuration as conf

from discord import app_commands
from discord.ext import commands

async def setup(bot):
    await bot.add_cog(Generation_commands(bot))

class Generation_commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None


    ##### Generation configuration commands ################################################
    @app_commands.command()
    async def decoding_mode(self, interaction: discord.Interaction):
        """Posts the current decoding mode"""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in self.bot.bartleby_users.keys():
            self.bot.bartleby_users[user_name] = user.User(user_name)

        # Post the reply and log the interaction
        await interaction.response.send_message(f'```decoding mode: {self.bot.bartleby_users[user_name].decoding_mode}```')
        self.logger.debug(f'Show decoding mode command from: {user_name}')

    @app_commands.command()
    async def decoding_modes(self, interaction: discord.Interaction):
        """Posts available decoding modes"""

        # Get the user name
        user_name = interaction.user

        # Post the reply and log the interaction
        await interaction.response.send_message(f"```Available decoding modes: {', '.join(conf.decoding_mode.keys())}```")
        self.logger.debug(f'Show decoding modes command from: {user_name}')

    @app_commands.command()
    @app_commands.describe(decoding_mode='New decoding mode')
    async def set_decoding_mode(self, interaction: discord.Interaction, decoding_mode: str):
        """Sets the decoding mode during inference."""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in self.bot.bartleby_users.keys():
            self.bot.bartleby_users[user_name] = user.User(user_name)

        # Make the update
        self.bot.bartleby_users[user_name].decoding_mode = decoding_mode
        self.bot.bartleby_users[user_name].set_decoding_mode()

        # Post the reply and log the interaction
        await interaction.response.send_message(f'```Changed decoding mode to {decoding_mode}```')
        self.logger.debug(f'Update decoding mode command from: {user_name}')

    @app_commands.command()
    async def config(self, interaction: discord.Interaction):
        """Posts any non-model-default generation parameter values"""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in self.bot.bartleby_users.keys():
            self.bot.bartleby_users[user_name] = user.User(user_name)

        # Post the reply and log the interaction
        await interaction.response.send_message(f'```Non-model-default generation settings: {self.bot.bartleby_users[user_name].generation_configurations[self.bot.bartleby_users[user_name].model_type]}```')

    @app_commands.command()
    async def config_full(self, interaction: discord.Interaction):
        """Posts all generation parameter values"""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in self.bot.bartleby_users.keys():
            self.bot.bartleby_users[user_name] = user.User(user_name)

        # Post the reply and log the interaction
        await interaction.response.send_message(f'```All available generation settings: {self.bot.bartleby_users[user_name].generation_configurations[self.bot.bartleby_users[user_name].model_type].__dict__}```')

    @app_commands.command()
    @app_commands.describe(parameter='Parameter to update', new_value='New value')
    async def set_config(self, interaction: discord.Interaction, parameter: str, new_value: str):
        """Updates the value of a specific generation configuration parameter."""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in self.bot.bartleby_users.keys():
            self.bot.bartleby_users[user_name] = user.User(user_name)

        # Handle string to int or float conversion - some generation
        # configuration parameters take ints and some take floats
        if '.' in new_value:
            val = float(new_value)
        else:
            val = int(new_value)

        # Set the value
        setattr(self.bot.bartleby_users[user_name].generation_configurations[self.bot.bartleby_users[user_name].model_type], parameter, val)

        # Post the reply and log the interaction
        await interaction.response.send_message(f'```Updated parameter {parameter}: {val}```')
        self.logger.debug(f'Show config parameter command from: {user_name}. {parameter}: {val}')

    @app_commands.command()
    async def model(self, interaction: discord.Interaction):
        """Posts the current model"""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in self.bot.bartleby_users.keys():
            self.bot.bartleby_users[user_name] = user.User(user_name)

        # Post the reply and log the interaction
        await interaction.response.send_message(f'```Current model: {self.bot.bartleby_users[user_name].model_type}```')
        self.logger.debug(f'Show current model command from: {user_name}')

    @app_commands.command()
    async def models(self, interaction: discord.Interaction):
        """Posts the available models"""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in self.bot.bartleby_users.keys():
            self.bot.bartleby_users[user_name] = user.User(user_name)

        # Post the reply and log the interaction
        model_list = '\n' + '\n'.join(conf.supported_models)
        await interaction.response.send_message(f'```{model_list}```')
        self.logger.debug(f'Show supported models command from: {user_name}')

    @app_commands.command()
    @app_commands.describe(model_type='New model type')
    async def swap_model(self, interaction: discord.Interaction, model_type: str):
        """Changes the model type."""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in self.bot.bartleby_users.keys():
            self.bot.bartleby_users[user_name] = user.User(user_name)

        # Check to make sure we have the model the user asked for 
        if model_type in conf.supported_models:

            # Make the update
            self.bot.bartleby_users[user_name].model_type = model_type

            # Post the reply and log the interaction
            await interaction.response.send_message(f'```Switched to {model_type}. Note the next reply may be slow if this model is not cached or already running.```')
            self.logger.debug(f'Swap model command from: {user_name}. New model: {model_type}')

        else:

            # Post the reply and log the interaction
            supported_models = '\n' + '\n'.join(conf.supported_models)
            await interaction.response.send_message(f'```New model must be one of: {supported_models}```')
            self.logger.debug(f'Failed swap model command from: {user_name}. New model: {model_type}')
