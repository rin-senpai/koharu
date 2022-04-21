import discord
import os
from discord.ext.commands import AutoShardedBot

class Bot(AutoShardedBot):
    def __init__(self,  *args, prefix=None, **kwargs):
         super().__init__(*args, **kwargs)
         self.prefix = prefix

    async def setup_hook(self):
        for file in os.listdir("cogs"):
            if file.endswith(".py"):
                name = file[:-3]
                await self.load_extension(f"cogs.{name}")

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
        await self.change_presence(activity = discord.Game('with my kouhai'))

    async def on_message(self, msg):
        if not self.is_ready() or msg.author.bot:
            return
        
        if msg.content.startswith('¥') and await self.is_owner(msg.author):
            msg.content = msg.content.replace('¥', 'senpai say -h ')

        await self.process_commands(msg)
