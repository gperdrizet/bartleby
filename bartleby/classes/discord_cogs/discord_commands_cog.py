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