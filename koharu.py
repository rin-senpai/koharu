import logging
logging.basicConfig(level=logging.ERROR)

from discord import Intents
from bot import Bot

from utils import setup
config = setup.config()

intents = Intents.all()

bot = Bot(
    command_prefix=config['prefix'],
    prefix = config['prefix'],
    owner_id=config['owner'],
    description=config['description'],
    intents=intents
)

bot.run(config['token'])
