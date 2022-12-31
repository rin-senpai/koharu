import logging
logging.basicConfig(level=logging.INFO)

from typing import Literal, Optional

import discord
from discord import app_commands, Intents
from discord.ext import commands
from discord.ext.commands import Greedy, Context
from bot import Bot
from tree import Tree

import asyncio
import asyncpg

from utils import setup
config = setup.config()

intents = Intents.all()


async def run():
    db = await asyncpg.create_pool(**config['db_credentials'])
    bot = Bot(
        prefix=config['prefix'],
        tree_cls=Tree,
        owner_id=config['owner'],
        description=config['description'],
        intents=intents,
        db=db
    )

    @bot.command()
    @commands.guild_only()
    @commands.is_owner()
    async def sync(
    ctx: Context, guilds: Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:
        if not guilds:
            if spec == "~":
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                ctx.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                ctx.bot.tree.clear_commands(guild=ctx.guild)
                await ctx.bot.tree.sync(guild=ctx.guild)
                synced = []
            else:
                synced = await ctx.bot.tree.sync()

            await ctx.send(
                f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
            )
            return

        ret = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")

    try:
        await bot.start(config['token'])
    except KeyboardInterrupt:
        await db.close()
        await bot.logout()

asyncio.run(run())
