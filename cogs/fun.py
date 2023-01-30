import discord
from discord import ui, app_commands
from discord.ext import commands
from utils.owner_only import owner_only
from typing import Literal
from owoify import owoify
import asyncio
import random

bad_words = ['frick', 'heck']

class Fun(commands.Cog, description='Commands that are fun. I know, it\'s a bit hard to guess what these categories are for.'):
    def __init__(self, bot):
        self.bot = bot
        self.reply_ctx_menu = app_commands.ContextMenu(
            name='Reply',
            callback=self.reply
        )
        self.bot.tree.add_command(self.reply_ctx_menu)

    @app_commands.command(name='say', description='I echo the words of my *true* kouhai')
    @app_commands.check(owner_only)
    async def say(self, interaction: discord.Interaction, message: str, hide: bool = True, attachment: discord.Attachment = None):
        for bad_word in bad_words:
            if bad_word in message.lower():
                return await interaction.response.send_message('Nyaoww~ that\'s an icky word! Hmpf, nyu don\'t know that I\'m a good little kitty-nya')
        if hide:
            await interaction.response.send_message('Nyaoww~ I\'m a good little kitty-nya', ephemeral=True)
            await interaction.delete_original_response()
            if attachment is not None:
                await interaction.channel.send(message, file = await attachment.to_file())
            else:
                await interaction.channel.send(message)
        else:
            if attachment is not None:
                await interaction.response.send_message(message, file = await attachment.to_file())
            else:
                await interaction.response.send_message(message)

    @say.error
    async def say_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            return await interaction.response.send_message('You are not my *true* kouhai.', ephemeral=True)

    @app_commands.check(owner_only)
    async def reply(self, interaction: discord.Interaction, message: discord.Message):
        await interaction.response.send_modal(reply_modal(message=message))

    @app_commands.command(name='owoify', description='I echo the words of my *true* kouhai except owo')
    @app_commands.check(owner_only)
    async def owoify(self, interaction: discord.Interaction, message: str, level: Literal['owo', 'uwu', 'uvu'] = 'owo', hide: bool = True, attachment: discord.Attachment = None):
        for bad_word in bad_words:
            if bad_word in message.lower():
                return await interaction.response.send_message('Nyaoww~ that\'s an icky word! Hmpf, nyu don\'t know that I\'m a good little kitty-nya')
        if hide:
            await interaction.response.send_message('Nyaoww~ I\'m a good little kitty-nya', ephemeral=True)
            await interaction.delete_original_response()
            if attachment is not None:
                await interaction.channel.send(owoify(message, level), file = await attachment.to_file())
            else:
                await interaction.channel.send(owoify(message, level))
        else:
            if attachment is not None:
                await interaction.response.send_message(owoify(message, level), file = await attachment.to_file())
            else:
                await interaction.response.send_message(owoify(message, level))
    
    @owoify.error
    async def owoify_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            return await interaction.response.send_message('U are nywot my *twue* kouhai.', ephemeral=True)

    @app_commands.command(name='roulette', description='Play some Russian roulette and have a chance of getting yourself kicked from the server!') # help='You have a 1/6 chance of getting the better option.'
    @app_commands.guild_only()
    async def roulette(self, interaction: discord.Interaction):
        await interaction.response.send_message('**Spinning...**\nhttps://i.imgur.com/lPFgRP7.gif')
        await asyncio.sleep(3)
        if random.randint(1, 6) == 2:
            try:
                await interaction.guild.kick(interaction.user, reason='They were unlucky.')
            except Exception:
                return await interaction.edit_original_response(content='You seem to be too powerful\nhttps://tenor.com/view/fraz-bradford-meme-world-of-tanks-albania-gif-20568566')
            await interaction.edit_original_response(content='Omae wa mou shindeiru~\nhttps://i.imgur.com/uTMawPi.gif')
        else:
            await interaction.edit_original_response(content='Niice!\nhttps://i.imgur.com/KFvEtfj.gif')

    @app_commands.command(name='suicide', description='Feeling down? Go kick yourself')
    @app_commands.guild_only()
    async def suicide(self, interaction: discord.Interaction):
        try:
            await interaction.guild.kick(interaction.author, reason='Ah what a beautiful way to go')
        except Exception:
            return await interaction.response.send_message('You seem to be too powerful\nhttps://tenor.com/view/fraz-bradford-meme-world-of-tanks-albania-gif-20568566')
        await interaction.response.send_message('Sayo-nara\nhttps://tenor.com/view/gigachad-chad-gif-20773266')

class reply_modal(ui.Modal, title = 'How shall I reply?'):
    def __init__(self, message):
        super().__init__()
        self.message = message

    reply = ui.TextInput(label = 'Message', style = discord.TextStyle.long, required = True)
    mode = ui.TextInput(label = 'OwO?', style = discord.TextStyle.short, required = False)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message('Nyaoww~ I\'m a good little kitty-nya', ephemeral=True)
        await interaction.delete_original_response()
        if self.mode.value == 'owo' or self.mode.value == 'uwu' or self.mode.value == 'uvu':
            await self.message.reply(owoify(self.reply.value))
        else:
            await self.message.reply(self.reply.value)

async def setup(bot):
    await bot.add_cog(Fun(bot), guilds=[discord.Object(id=752052271935914064), discord.Object(id=722386163356270662)])
