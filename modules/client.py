from modules.gpt import generate_argument_response, is_argument
import discord
from discord import TextChannel
from datetime import datetime, timedelta
from discord.ext import tasks
import os

TARGET_ID = int(os.getenv("GREG_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
THRESHOLD = int(os.getenv("WORD_THRESHOLD"))

class Client(discord.Client):
    counter = 0
    replied_messages = set()

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        self.greg_check.start()
    

    def is_message_from_greg(self, message: discord.Message) -> bool:
        if message.author.id == TARGET_ID:
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

    def is_message_from_me(self, message: discord.Message) -> bool:
        return message.author.id == self.user.id
    
    def already_responded_to(self, message: discord.Message) -> bool:
        return message.id not in self.replied_messages

    
    def collate_messages(self, messages: list[discord.Message]) -> str:
        return "\n".join([msg.content for msg in messages])

    
    def generate_chat_log(self, messages: list[discord.Message]) -> list[str]:
        chat_log = []
        for msg in messages:
            if msg.author.id == self.user.id:
                chat_log.append(f"Me: {msg.content}")
            else:
                chat_log.append(f"{msg.author.display_name}: {msg.content}")
        
        return chat_log


    @tasks.loop(seconds=32)
    async def greg_check(self):
        print("\n" + "-" * 50)
        user = await self.fetch_user(TARGET_ID)
        channel = await self.fetch_channel(CHANNEL_ID)
        print(f"Checking For {user} in {channel.name}!")
        if not isinstance(channel, TextChannel):
            print("  Could not find channel")
            return

        recent_timestamp = datetime.now() - timedelta(hours=6)
        search = channel.history(limit=10, after=recent_timestamp)
        recent_messages: list[discord.Message] = [msg async for msg in search]
        recent_messages.sort(key=lambda msg: msg.created_at, reverse=True)
        
        if len(recent_messages) == 0:
            print("\tNo Recent Messages")
            return
        
        if self.is_message_from_me(recent_messages[0]):
            print("\tLast message was from me :O")
            return
        
        target_messages = list(filter(self.is_message_from_greg, recent_messages))
        target_messages = list(filter(self.is_message_text, target_messages))
        target_messages = list(filter(self.already_responded_to, target_messages))

        if len(target_messages) == 0:
            print(f"\t{user.display_name.title()} hasn't said anything in the last {len(recent_messages)} messages.")
            return


        last_greg_message = target_messages[0]
        self.replied_messages.update([msg.id for msg in target_messages])
        greg_text = self.collate_messages(target_messages)
        chat_log = self.generate_chat_log(recent_messages)

        word_count = len(greg_text.split(" "))
        if word_count < THRESHOLD:
            print(f"\tNot Reach Full Greg, he's only said {word_count} words.")
            return
        
        if not is_argument(chat_log):
            print("\tGreg isn't arguing")
            return
        
        print("\tGenerating Response!")
        async with channel.typing():
            response_word_count = len(last_greg_message.content) // 2
            response = generate_argument_response(messages=chat_log, target=user.display_name, word_count=response_word_count)
        
        print("Generating response from chat:")
        for msg in chat_log:
            print("\t" + msg.replace("\n", "\n\t"))
        print(f"\tAttemtped Word Count: {response_word_count}")
        print(f"\tActual Word Count: {len(response.split(' '))}")
        print(f"\tResponse: {response}")
        await last_greg_message.reply(response)


    @greg_check.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()  # wait until the bot logs in
