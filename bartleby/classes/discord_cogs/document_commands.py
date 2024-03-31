import discord
import bartleby.configuration as conf

from discord import app_commands
from discord.ext import commands

async def setup(bot):
    await bot.add_cog(Document_commands(bot))

class Document_commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None            

    ##### document commands ################################################
    @app_commands.command()
    @app_commands.describe(gdrive_link='Google drive folder share link')
    async def set_gdrive_folder(self, interaction: discord.Interaction, gdrive_link: str):
        """Specify gdrive shared folder for document uploads."""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in self.bot.bartleby_users.keys():
            self.bot.bartleby_users[user_name] = user.User(user_name)

        # Parse the share link
        gdrive_id = gdrive_link.split('/')[-1].split('?')[0]

        # Update it
        self.bot.bartleby_users[user_name].gdrive_folder_id = gdrive_id

        # Post the reply and log the interaction
        await interaction.response.send_message(f'```gdrive folder ID: {gdrive_id}```')
        self.logger.debug(f'Set gdrive folder command from: {user_name}')

    @app_commands.command()
    async def show_document_title(self, interaction: discord.Interaction):
        """Posts the current title/filename used to save documents to gdrive."""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in self.bot.bartleby_users.keys():
            self.bot.bartleby_users[user_name] = user.User(user_name)

        # Post the reply and log the interaction
        await interaction.response.send_message(f'```Document title: {self.bot.bartleby_users[user_name].document_title}```')
        self.logger.debug(f'Show document title command from: {user_name}')

    @app_commands.command()
    @app_commands.describe(document_title='Google drive document title')
    async def set_document_title(self, interaction: discord.Interaction, document_title: str):
        """Specify title/filename used to save documents to gdrive."""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in self.bot.bartleby_users.keys():
            self.bot.bartleby_users[user_name] = user.User(user_name)

        # Do the update
        self.bot.bartleby_users[user_name].document_title = document_title

        # Post the reply and log the interaction
        await interaction.response.send_message(f'```Document title: {document_title}```')
        self.logger.debug(f'Set document title command from: {user_name}')

    @app_commands.command()
    async def make_docx(self, interaction: discord.Interaction):
        """Save last message to gdrive as docx"""

        # Get the user name
        user_name = interaction.user

        # If this is the first interaction from this user, onboard them
        if user_name not in self.bot.bartleby_users.keys():
            self.bot.bartleby_users[user_name] = user.User(user_name)

        # Check to see that the user has set a gdrive folder id
        # If they have, make the document
        if self.bot.bartleby_users[user_name].gdrive_folder_id != None:
            
            # Make the document
            self.bot.docx_instance.generate(self.bot.bartleby_users[user_name], 1, None)
            
            # Post the reply and log the interaction
            await interaction.response.send_message(f'```Document generated```')
            self.logger.debug(f'Got make docx command from: {user_name}')

        # If they have not set a gdrive folder id, ask them to set one
        # before generating a document
        elif self.bot.bartleby_users[user_name].gdrive_folder_id == None:

            await interaction.response.send_message(f'```Please set a gdrive folder generating a document```')
            self.logger.debug(f'Got make docx command without gdrive folder id from: {user_name}')

    # # Context menu command to generate document via left click on message
    # @app_commands.context_menu(name='Save to gdrive')
    # async def save_message(self, interaction: discord.Interaction, message: discord.Message):

    #     # Get the user name
    #     user_name = interaction.user

    #     # Get the message text
    #     text = message.content

    #     # If this is the first interaction from this user, onboard them
    #     if user_name not in self.bot.bartleby_users.keys():
    #         self.bot.bartleby_users[user_name] = user.User(user_name)

    #     # Check to see that the user has set a gdrive folder id
    #     # If they have, make the document
    #     if self.bot.bartleby_users[user_name].gdrive_folder_id != None:
            
    #         # Make the document
    #         self.bot.docx_instance.generate_from_text(self.bot.bartleby_users[user_name], text)
            
    #         # Post the reply and log the interaction
    #         await interaction.response.send_message(f'```Document generated```')
    #         self.logger.debug(f'Got make docx command from: {user_name}')

    #     # If they have not set a gdrive folder id, ask them to set one
    #     # before generating a document
    #     elif self.bot.bartleby_users[user_name].gdrive_folder_id == None:

    #         await interaction.response.send_message(f'```Please set a gdrive folder generating a document```')
    #         self.logger.debug(f'Got make docx command without gdrive folder id from: {user_name}')
