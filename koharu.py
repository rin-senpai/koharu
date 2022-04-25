import logging
logging.basicConfig(level=logging.ERROR)

from discord import Intents
from bot import Bot

import asyncio
import asyncpg

from utils import setup
config = setup.config()

intents = Intents.all()

async def run():
    db = await asyncpg.create_pool(**config['db_credentials'])
    bot = Bot(
        default_prefix=config['prefix'],
        owner_id = config['owner'],
        description = config['description'],
        intents = intents,
        db = db
    )
    try:
        await bot.start(config['token'])
    except KeyboardInterrupt:
        await db.close()
        await bot.logout()

loop = asyncio.get_event_loop()
loop.run_until_complete(run())
