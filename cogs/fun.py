import discord
from discord import ui, app_commands
from discord.ext import commands
from utils.owner_only import owner_only
from typing import Literal
from owoify import owoify
import asyncio
import random
import re
import asyncio
from async_timeout import timeout
import aiohttp

bad_words = []

class Fun(commands.Cog, description='Commands that are fun. I know, it\'s a bit hard to guess what these categories are for.'):
    def __init__(self, bot):
        self.GUILD_ID = 722386163356270662
        self.EMOJI_CHANNEL_ID = 1067822653655748718
        
        self.bot = bot
        
        self.auto_removed_chars = [' ', '\n']
        self.invalid_chars = [';', ':', '`']
        
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
                return await interaction.response.send_message('Nyaoww~ that\'s an icky word! Hmpf, nyu don\'t know that I\'m a good little kitty-nya', ephemeral=hide)
            
        await interaction.response.defer(ephemeral=hide)
            
        emojis = []
        if ';' in message:
            guild = await self.bot.fetch_guild(self.GUILD_ID)
            emoji_ids = []
            prev_was_emoji = False
            stickering_escaped = False
            split_message = message.split(';')
            for i in range(1, len(split_message)):
                if len(split_message) != 1:
                    if split_message[i-1][-1:] == '\\' and split_message[i-1][-2:] != '\\\\':
                        stickering_escaped = True
                    else:
                        stickering_escaped = False
                
                sticker = None
                if not stickering_escaped and i != len(split_message) - 1:
                    if split_message[i] != '':
                        if split_message[i][:1] not in self.auto_removed_chars and split_message[i][-1:] not in self.auto_removed_chars:
                            for invalid_char in self.invalid_chars:
                                if invalid_char not in split_message[i]:
                                    sticker = await self.bot.db.fetchval('SELECT (sticker_id, name) FROM users_stickers WHERE user_id = $1 AND (name = $2 OR $2 = ANY(aliases))', interaction.user.id, split_message[i])
                
                if sticker is None:
                    if not prev_was_emoji:
                        split_message[i] = ';' + split_message[i]
                    prev_was_emoji = False
                    continue

                prev_was_emoji = True

                message_id = await self.bot.db.fetchval('SELECT emoji_message_id FROM stickers WHERE sticker_id = $1', sticker[0])
                emoji_channel = await self.bot.fetch_channel(self.EMOJI_CHANNEL_ID)
                message = await emoji_channel.fetch_message(message_id)
                emoji_url = message.attachments[0].url
                filtered_name = re.sub(r'[^a-zA-Z0-9_]+', '_', sticker[1])
                if filtered_name == '_':
                    filtered_name = 'emoji'

                async with aiohttp.ClientSession() as session:
                    async with session.get(emoji_url) as resp:
                        image = await resp.read()
                if sticker[0] not in emoji_ids:
                    try:
                        async with timeout(4):
                            emoji = await guild.create_custom_emoji(name=f'{sticker[0]}_{filtered_name}', image=image)
                    except discord.HTTPException as e:
                        for emoji in emojis:
                            await guild.delete_emoji(emoji)
                        if e.code == 50138: # too big
                            return await interaction.followup.send(f'Uhh {sticker[1]} is too big')
                        elif e.code == 30008: # reached max number of emojis
                            return await interaction.followup.send(f'too many emojis in that server')
                        else:
                            return await interaction.followup.send(e)
                    except asyncio.TimeoutError: # rate limited
                        for emoji in emojis:
                            await guild.delete_emoji(emoji)
                        return await interaction.followup.send('idk youprobably got rate limited or were timed out for other reasons like upload speeds?')
                    emojis.append(emoji)
                    emoji_ids.append(sticker[0])
                else:
                    emoji = emojis[emoji_ids.index(sticker[0])]
                split_message[i] = str(emoji)
            
            message = ''.join(split_message)

        if hide:
            await interaction.followup.send('Nyaoww~ I\'m a good little kitty-nya')
            await interaction.delete_original_response()
            if attachment is not None:
                await interaction.channel.send(message, file = await attachment.to_file())
            else:
                await interaction.channel.send(message)
        else:
            if attachment is not None:
                await interaction.followup.send(message, file = await attachment.to_file())
            else:
                await interaction.followup.send(message)
                
        if len(emojis) != 0:
            for emoji in emojis:
                await guild.delete_emoji(emoji)

    @say.error
    async def say_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            return await interaction.response.send_message('You are not my *true* kouhai.', ephemeral=True)

    @app_commands.check(owner_only)
    async def reply(self, interaction: discord.Interaction, message: discord.Message):
        await interaction.response.send_modal(reply_modal(message=message, bot=self.bot, guild_id=self.GUILD_ID, emoji_channel_id=self.EMOJI_CHANNEL_ID))

    @app_commands.command(name='owoify', description='I echo the words of my *true* kouhai except owo')
    @app_commands.check(owner_only)
    async def owoify(self, interaction: discord.Interaction, message: str, level: Literal['owo', 'uwu', 'uvu'] = 'owo', hide: bool = True, attachment: discord.Attachment = None):
        for bad_word in bad_words:
            if bad_word in message.lower():
                return await interaction.response.send_message('Nyaoww~ that\'s an icky word! Hmpf, nyu don\'t know that I\'m a good little kitty-nya', ephemeral=hide)
            
        await interaction.response.defer(ephemeral=hide)
            
        emojis = []
        if ';' in message:
            guild = await self.bot.fetch_guild(self.GUILD_ID)
            emoji_ids = []
            prev_was_emoji = False
            stickering_escaped = False
            split_message = message.split(';')
            for i in range(1, len(split_message)):
                if len(split_message) != 1:
                    if split_message[i-1][-1:] == '\\' and split_message[i-1][-2:] != '\\\\':
                        stickering_escaped = True
                    else:
                        stickering_escaped = False
                
                sticker = None
                if not stickering_escaped and i != len(split_message) - 1:
                    if split_message[i] != '':
                        if split_message[i][:1] not in self.auto_removed_chars and split_message[i][-1:] not in self.auto_removed_chars:
                            for invalid_char in self.invalid_chars:
                                if invalid_char not in split_message[i]:
                                    sticker = await self.bot.db.fetchval('SELECT (sticker_id, name) FROM users_stickers WHERE user_id = $1 AND (name = $2 OR $2 = ANY(aliases))', interaction.user.id, split_message[i])
                
                if sticker is None:
                    if not prev_was_emoji:
                        split_message[i] = ';' + split_message[i]
                    prev_was_emoji = False
                    continue

                prev_was_emoji = True

                message_id = await self.bot.db.fetchval('SELECT emoji_message_id FROM stickers WHERE sticker_id = $1', sticker[0])
                emoji_channel = await self.bot.fetch_channel(self.EMOJI_CHANNEL_ID)
                message = await emoji_channel.fetch_message(message_id)
                emoji_url = message.attachments[0].url
                filtered_name = re.sub(r'[^a-zA-Z0-9_]+', '_', sticker[1])
                if filtered_name == '_':
                    filtered_name = 'emoji'

                async with aiohttp.ClientSession() as session:
                    async with session.get(emoji_url) as resp:
                        image = await resp.read()
                if sticker[0] not in emoji_ids:
                    try:
                        async with timeout(4):
                            emoji = await guild.create_custom_emoji(name=f'{sticker[0]}_{filtered_name}', image=image)
                    except discord.HTTPException as e:
                        for emoji in emojis:
                            await guild.delete_emoji(emoji)
                        if e.code == 50138: # too big
                            return await interaction.followup.send(f'Uhh {sticker[1]} is too big')
                        elif e.code == 30008: # reached max number of emojis
                            return await interaction.followup.send(f'too many emojis in that server')
                        else:
                            return await interaction.followup.send(e)
                    except asyncio.TimeoutError: # rate limited
                        for emoji in emojis:
                            await guild.delete_emoji(emoji)
                        return await interaction.followup.send('idk youprobably got rate limited or were timed out for other reasons like upload speeds?')
                    emojis.append(emoji)
                    emoji_ids.append(sticker[0])
                else:
                    emoji = emojis[emoji_ids.index(sticker[0])]
                split_message[i] = str(emoji)
            
            message = ''.join(split_message)

        if hide:
            await interaction.followup.send('Nyaoww~ I\'m a good little kitty-nya', ephemeral=True)
            await interaction.delete_original_response()
            if attachment is not None:
                await interaction.channel.send(owoify(message, level), file = await attachment.to_file())
            else:
                await interaction.channel.send(owoify(message, level))
        else:
            if attachment is not None:
                await interaction.followup.send(owoify(message, level), file = await attachment.to_file())
            else:
                await interaction.followup.send(owoify(message, level))
                
        if len(emojis) != 0:
            for emoji in emojis:
                await guild.delete_emoji(emoji)
    
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
    def __init__(self, message, bot, guild_id, emoji_channel_id):
        super().__init__()
        self.message = message
        self.bot = bot
        self.GUILD_ID = guild_id
        self.EMOJI_CHANNEL_ID = emoji_channel_id
        
        self.auto_removed_chars = [' ', '\n']
        self.invalid_chars = [';', ':', '`']

    reply = ui.TextInput(label = 'Message', style = discord.TextStyle.long, required = True)
    mode = ui.TextInput(label = 'OwO?', style = discord.TextStyle.short, required = False)

    async def on_submit(self, interaction: discord.Interaction):
        for bad_word in bad_words:
            if bad_word in self.reply.value.lower():
                return await interaction.response.send_message('Nyaoww~ that\'s an icky word! Hmpf, nyu don\'t know that I\'m a good little kitty-nya', ephemeral=True)
            
        await interaction.response.defer(ephemeral=True)
            
        emojis = []
        if ';' in self.reply.value:
            guild = await self.bot.fetch_guild(self.GUILD_ID)
            emoji_ids = []
            prev_was_emoji = False
            stickering_escaped = False
            split_message = self.reply.value.split(';')
            for i in range(1, len(split_message)):
                if len(split_message) != 1:
                    if split_message[i-1][-1:] == '\\' and split_message[i-1][-2:] != '\\\\':
                        stickering_escaped = True
                    else:
                        stickering_escaped = False
                
                sticker = None
                if not stickering_escaped and i != len(split_message) - 1:
                    if split_message[i] != '':
                        if split_message[i][:1] not in self.auto_removed_chars and split_message[i][-1:] not in self.auto_removed_chars:
                            for invalid_char in self.invalid_chars:
                                if invalid_char not in split_message[i]:
                                    sticker = await self.bot.db.fetchval('SELECT (sticker_id, name) FROM users_stickers WHERE user_id = $1 AND (name = $2 OR $2 = ANY(aliases))', interaction.user.id, split_message[i])
                
                if sticker is None:
                    if not prev_was_emoji:
                        split_message[i] = ';' + split_message[i]
                    prev_was_emoji = False
                    continue

                prev_was_emoji = True

                message_id = await self.bot.db.fetchval('SELECT emoji_message_id FROM stickers WHERE sticker_id = $1', sticker[0])
                emoji_channel = await self.bot.fetch_channel(self.EMOJI_CHANNEL_ID)
                message = await emoji_channel.fetch_message(message_id)
                emoji_url = message.attachments[0].url
                filtered_name = re.sub(r'[^a-zA-Z0-9_]+', '_', sticker[1])
                if filtered_name == '_':
                    filtered_name = 'emoji'

                async with aiohttp.ClientSession() as session:
                    async with session.get(emoji_url) as resp:
                        image = await resp.read()
                if sticker[0] not in emoji_ids:
                    try:
                        async with timeout(4):
                            emoji = await guild.create_custom_emoji(name=f'{sticker[0]}_{filtered_name}', image=image)
                    except discord.HTTPException as e:
                        for emoji in emojis:
                            await guild.delete_emoji(emoji)
                        if e.code == 50138: # too big
                            return await interaction.followup.send(f'Uhh {sticker[1]} is too big')
                        elif e.code == 30008: # reached max number of emojis
                            return await interaction.followup.send(f'too many emojis in that server')
                        else:
                            return await interaction.followup.send(e)
                    except asyncio.TimeoutError: # rate limited
                        for emoji in emojis:
                            await guild.delete_emoji(emoji)
                        return await interaction.followup.send('idk youprobably got rate limited or were timed out for other reasons like upload speeds?')
                    emojis.append(emoji)
                    emoji_ids.append(sticker[0])
                else:
                    emoji = emojis[emoji_ids.index(sticker[0])]
                split_message[i] = str(emoji)
            
            message = ''.join(split_message)
        else:
            message = self.reply.value
        
        followup = await interaction.followup.send('Nyaoww~ I\'m a good little kitty-nya', wait=True, ephemeral=True)
        await followup.delete()
        if self.mode.value == 'owo' or self.mode.value == 'uwu' or self.mode.value == 'uvu':
            await self.message.reply(owoify(message))
        else:
            await self.message.reply(message)
            
        if len(emojis) != 0:
            for emoji in emojis:
                await guild.delete_emoji(emoji)

async def setup(bot):
    await bot.add_cog(Fun(bot))
