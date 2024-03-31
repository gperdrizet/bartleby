import discord
import time
import textwrap
from discord.ext import tasks, commands

class LLMbot(commands.Bot):
    '''Custom discord bot class with background task to 
    check the LLM response queue and post any new generated 
    responses'''

    def __init__(self, logger, response_queue, users, docx_instance, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add logger and LLM's response queue
        self.logger = logger
        self.response_queue = response_queue

        # Add list of user class instances
        self.bartleby_users = users

        # Add docx_instance
        self.docx_instance = docx_instance

    async def setup_hook(self) -> None:
        
        # Load the command cogs
        cog_import_path = 'bartleby.classes.discord_cogs'
        await self.load_extension(f'{cog_import_path}.system_commands')
        await self.load_extension(f'{cog_import_path}.generation_commands')
        await self.load_extension(f'{cog_import_path}.document_commands')

        # # Sync global command tree
        # await self.tree.sync()

        # Copy global tree to guild and sync (syncs faster)
        MY_GUILD = discord.Object(id=755533103065333911)
        self.tree.copy_global_to(guild=MY_GUILD)

        await self.tree.sync(guild=MY_GUILD)

        # Start the LLM response queue check task to run in the background
        self.check_response_queue.start()

    @tasks.loop(seconds=5)  # Frequency with which to run the task
    async def check_response_queue(self):

        # Check the response queue
        if self.response_queue.empty() == False:

            # Get the next user from the responder queue
            queued_user = self.response_queue.get()

            # Immediately mark this queued user as done so that
            # the job is not still sitting in the queue while we
            # generate the response. Otherwise the background task
            # will pick it up again on the next check.
            self.response_queue.task_done()
            self.logger.info(f'+{round(time.time() - queued_user.message_time, 2)}s: Responder got {queued_user.user_name} from generator')

            # Get the channel from the channel id in the queued user's message object
            channel = self.get_channel(queued_user.message_object.channel.id)

            # Get the number of not offline users in the channel - this is better than
            # getting it from the guild because in a server of x members a channel can have
            # x - n members if it is private
            online_channel_members = 0

            # Loop on channel members checking status and counting 
            # members which are not offline
            for member in channel.members:
                self.logger.debug(f'{member}: {member.status}')
                if str(member.status) != 'offline':
                    online_channel_members += 1

            # Log result
            self.logger.debug(f'Not-offline count {online_channel_members}')

            # If it is just bartleby and one other user, forgo replies and mentions
            # and just post bare messages as if it were a DM
            if online_channel_members <= 2:

                # Make sure we don't hit discord's character limit
                if len(queued_user.messages[-1]['content']) < 2000:
                    await channel.send(queued_user.messages[-1]['content'])

                # If the reply is too long, split it up and post the chunks
                else:
                    chunks = textwrap.wrap(queued_user.messages[-1]['content'], 2000)

                    for chunk in chunks:
                        await channel.send(chunk)


            # If there is more than one user, i.e. bartleby + 2 users = 3 members,
            # use replies
            if online_channel_members > 2:

                # Make sure we don't hit discord's character limit
                if len(queued_user.messages[-1]['content']) < 2000:
                    await queued_user.message_object.reply(queued_user.messages[-1]['content'])

                # If the reply is too long, split it up and post the chunks
                else:
                    chunks = textwrap.wrap(queued_user.messages[-1]['content'], 2000)

                    for chunk in chunks:
                        await queued_user.message_object.reply(chunk)
            
            # Log response time
            self.logger.info(f'+{round(time.time() - queued_user.message_time, 2)}s: Posted reply to {queued_user.user_name} in chat')

    # Wait until the bot is logged in to start the LLM response queue check task
    @check_response_queue.before_loop
    async def before_my_task(self):
        
        await self.wait_until_ready()