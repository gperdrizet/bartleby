import discord
import bartleby.configuration as conf

from discord import app_commands
from discord.ext import commands

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

    @app_commands.command()
    async def input_buffer_size(self, interaction: discord.Interaction):
        """Posts the current LLM input buffer size."""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in self.bot.bartleby_users.keys():
            self.bot.bartleby_users[user_name] = self.user.User(user_name)

        # Post the reply and log the interaction
        await interaction.response.send_message(f'```LLM using last {conf.model_input_buffer_size} messages as input```')
        self.logger.debug(f'Show input buffer size command from: {user_name}')

    @app_commands.command()
    @app_commands.describe(buffer_size='New input buffer size')
    async def set_input_buffer_size(self, interaction: discord.Interaction, buffer_size: int):
        """Updates the LLM input buffer size."""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in self.bot.bartleby_users.keys():
            self.bot.bartleby_users[user_name] = user.User(user_name)

        # Make the update
        self.bot.bartleby_users[user_name].model_input_buffer_size = buffer_size

        # Post the reply and log the interaction
        await interaction.response.send_message(f'```Changed model input buffer to last {buffer_size} messages```')
        self.logger.debug(f'Update input buffer size to {buffer_size} command from: {user_name}')

    @app_commands.command()
    async def input_messages(self, interaction: discord.Interaction):
        """Post contents of LLM input buffer to chat."""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in self.bot.bartleby_users.keys():
            self.bot.bartleby_users[user_name] = user.User(user_name)

        # Select last n messages for input to the model
        messages = []

        for message in self.bot.bartleby_users[user_name].messages[-self.bot.bartleby_users[user_name].model_input_buffer_size:]:
            messages.append(f"{message['role']}: {message['content']}")

        result = '\n'.join(messages)

        # Post the reply and log the interaction
        await interaction.response.send_message(f'```{result}```')
        self.logger.debug(f'Show input buffer command from: {user_name}')

    @app_commands.command()
    async def prompt(self, interaction: discord.Interaction):
        """Post the generation prompt."""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in self.bot.bartleby_users.keys():
            self.bot.bartleby_users[user_name] = user.User(user_name)

        # Post the reply and log the interaction
        await interaction.response.send_message(f'```Generation prompt: {self.bot.bartleby_users[user_name].initial_prompt}```')
        self.logger.debug(f'Show prompt command from: {user_name}')

    @app_commands.command()
    @app_commands.describe(initial_prompt='New generation prompt')
    async def set_prompt(self, interaction: discord.Interaction, initial_prompt: str):
        """Updates the generation prompt."""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in self.bot.bartleby_users.keys():
            self.bot.bartleby_users[user_name] = user.User(user_name)

        # Make the update
        self.bot.bartleby_users[user_name].initial_prompt = initial_prompt
        self.bot.bartleby_users[user_name].restart_conversation()

        # Post the reply and log the interaction
        await interaction.response.send_message(f'```Updated generation prompt: {initial_prompt}```')
        self.logger.debug(f'Update prompt command from: {user_name}. New prompt: {initial_prompt}')

    @app_commands.command()
    async def reset_chat(self, interaction: discord.Interaction):
        """Clear the message buffer and restart the chat"""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in self.bot.bartleby_users.keys():
            self.bot.bartleby_users[user_name] = user.User(user_name)

        # Make the update
        self.bot.bartleby_users[user_name].restart_conversation()

        # Post the reply and log the interaction
        await interaction.response.send_message(f'```Conversation reset```')
        self.logger.debug(f'Restart chat command from: {user_name}')