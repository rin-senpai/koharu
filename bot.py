import discord
from discord.ext import commands
from discord.ext.commands import AutoShardedBot
import os
import traceback
import sys

class Bot(AutoShardedBot):
    def __init__(self, prefix, *args, **kwargs):
         super().__init__(command_prefix=prefix, *args, **kwargs)
         self.db = kwargs.pop('db')

    async def setup_hook(self):
        for file in os.listdir('cogs'):
            if file.endswith('.py'):
                name = file[:-3]
                await self.load_extension(f'cogs.{name}')

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
        await self.change_presence(activity = discord.Game('with my kouhai'))

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.DisabledCommand):
            await ctx.reply('Sorry. This command is disabled and cannot be used.')
        elif isinstance(error, commands.NotOwner):
            await ctx.reply('H-hey! Nyor not my kouhai-nya!')
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.reply('This command can only be used in servers.')
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.reply('This command can only be used in DMs.')
        elif isinstance(error, commands.NSFWChannelRequired):
            await ctx.reply('This command can only used in cultured channels.')
        elif isinstance(error, commands.MissingRole):
            await ctx.reply(f'You require the role(s): `{", ".join(error.missing_role)}` to use this command.')
        elif isinstance(error, commands.MissingPermissions):
            await ctx.reply(f'You require the permission(s): `{", ".join(error.missing_permissions)}` to use this command.')
        elif isinstance(error, commands.MissingAnyRole):
            await ctx.reply(f'You require one of the following roles to use this command: `{", ".join(error.missing_roles)}`')
        elif isinstance(error, commands.BotMissingRole):
            await ctx.reply(f'I require require the role(s): `{", ".join(error.missing_role)}` to execute this command.')
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.reply(f'I require the permission(s): `{", ".join(error.missing_permissions)}` to execute this command.')
        elif isinstance(error, commands.BotMissingAnyRole):
            await ctx.reply(f'I require one of the following roles to execute this command: `{", ".join(error.missing_roles)}`')
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(f'This command is on cooldown. Try again in {error.retry_after:.2f}s.')
        elif isinstance(error, commands.CheckFailure):
            await ctx.reply('You don\'t have permission to use this command.')
        elif isinstance(error, commands.CommandInvokeError):
            original = error.original
            if not isinstance(original, discord.HTTPException):
                print(f'In {ctx.command.qualified_name}:', file=sys.stderr)
                traceback.print_tb(original.__traceback__)
                print(f'{original.__class__.__name__}: {original}', file=sys.stderr)
        elif isinstance(error, commands.ArgumentParsingError):
            await ctx.send(error)
