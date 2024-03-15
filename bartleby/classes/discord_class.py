from discord.ext import tasks
import discord
import time
class LLMClient(discord.Client):
    '''Custom discord client class with background task to 
    check the LLM response queue and post any new generated 
    responses'''

    def __init__(self, logger, response_queue, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add logger and LLM's response queue
        self.logger = logger
        self.response_queue = response_queue

    async def setup_hook(self) -> None:

        # Start the task to run in the background
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

            for member in channel.members:
                self.logger.debug(f'{member}: {member.status}')
                if str(member.status) != 'offline':
                    online_channel_members += 1

            self.logger.debug(f'Not-offline count {online_channel_members}')

            # If it is just bartleby and one other user, forgo replies and mentions
            # and just post bare messages as if it were a DM
            if online_channel_members <= 2:
                await channel.send(queued_user.messages[-1]['content'])

            # If there is more than one user, i.e. bartleby + 2 users = 3 members,
            # use replies
            if online_channel_members > 2:
                await queued_user.message_object.reply(queued_user.messages[-1]['content'])
            
            self.logger.info(f'+{round(time.time() - queued_user.message_time, 2)}s: Posted reply to {queued_user.user_name} in chat')

    # Wait until the bot is logged in to start the task
    @check_response_queue.before_loop
    async def before_my_task(self):
        
        await self.wait_until_ready()