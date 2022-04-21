import logging

logging.basicConfig(level=logging.ERROR)

from discord import Intents
from utils.bot import Bot

from utils import setup
config = setup.config()

intents = Intents.all()

bot = Bot(
    command_prefix=config["prefix"],
    prefix = config["prefix"],
    owner_ids=config["owners"],
    description=config["description"],
    intents=intents
    )

bot.run(config["token"])
