from discord.ext import tasks
import discord
import time


class MyClient(discord.Client):
    def __init__(self, logger, response_queue, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.logger = logger
        self.response_queue = response_queue

    async def setup_hook(self) -> None:
        # start the task to run in the background
        self.my_background_task.start()

    @tasks.loop(seconds=1)  # task runs every 1 seconds
    async def my_background_task(self):
        self.logger.debug('Checking LLM response queue.')

        if self.response_queue.empty() == False:

            # Get the next user from the responder queue
            queued_user = self.response_queue.get()
            self.logger.info(f'+{round(time.time() - queued_user.message_time, 2)}s: Responder got {queued_user.user_name} from generator')

            # Post the new response from the users conversation
            channel = self.get_channel(1217620182663696394)
            await channel.send(queued_user.messages[-1]['content'])
            self.response_queue.task_done()
            self.logger.info(f'+{round(time.time() - queued_user.message_time, 2)}s: Posted reply to {queued_user.user_name} in chat')


    @my_background_task.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()  # wait until the bot logs in