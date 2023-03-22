from modules.gpt import generate_response
import discord
from discord import TextChannel
from datetime import datetime, timedelta
from discord.ext import tasks
import os

GREG_ID = int(os.getenv("GREG_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

class Client(discord.Client):
    counter = 0

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
        self.greg_check.start()
    

    def is_message_from_greg(self, message: discord.Message) -> bool:
        if message.author and message.author.id == GREG_ID:
            return True
        else:
            return False


    def is_message_text(self, message: discord.Message) -> bool:
        if "http" in message.content:
            return False
        if len(message.attachments) > 0:
            return False
        else:
            return True


    @tasks.loop(minutes=13, seconds=36)
    async def greg_check(self):
        channel = await self.fetch_channel(CHANNEL_ID)  # type: ignore
        if not isinstance(channel, TextChannel):
            print("Could not find channel")
            return

        recent_timestamp = datetime.now() - timedelta(days=1)
        search = channel.history(limit=10)
        recent_messages: list[discord.Message] = [msg async for msg in search]
        
        if len(recent_messages) == 0:
            return

        greg_messages = list(
            filter(self.is_message_from_greg,
                filter(self.is_message_text, recent_messages)
            )
        )
        greg_messages = list()
        if len(greg_messages) < 3:
            return


        last_message = recent_messages[0]
        if last_message.author.id == self.user.id:
            return
        
        chat_log = []
        for msg in recent_messages:
            if msg.author.id == self.user.id:
                chat_log.append(f"Me: {msg.content}")
            else:
                chat_log.append(f"{msg.author.display_name}: {msg.content}")

        response = generate_response(chat_log)
        
        print("Generating response from chat:")
        print("\n\t".join(chat_log))
        print(f"Response: {response}")
        # await channel.send(response)


    @greg_check.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()  # wait until the bot logs in
