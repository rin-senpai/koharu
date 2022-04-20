from ast import arg
import logging

logging.basicConfig(level=logging.ERROR)

import discord
from discord.ext import commands

from utils import setup
config = setup.config()

from cogs.fun import Fun

intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix=config["prefix"],
    owner_ids=config["owners"],
    description=config["description"],
    intents=intents)

@bot.event
async def on_ready():
    await bot.add_cog(Fun(bot))
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    await bot.change_presence(activity = discord.Game('with my kouhai'))


bot.run(config["token"])