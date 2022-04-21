import logging
logging.basicConfig(level=logging.ERROR)

from discord import Intents
from cogs.utils.bot import Bot#, Help

from cogs.utils import setup
config = setup.config()

intents = Intents.all()

bot = Bot(
    command_prefix=config["prefix"],
    prefix = config["prefix"],
    owner_ids=config["owners"],
    # help_command=Help(),
    description=config["description"],
    intents=intents
    )

bot.run(config["token"])
