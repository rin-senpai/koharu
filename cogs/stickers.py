import discord
from discord import ui, app_commands
from discord.ext import commands
import requests
from .utils.image import resize, is_image_url, url_to_file
from emoji import emoji_count
import re
import asyncio
import aiohttp
from async_timeout import timeout
import math

class Stickers(commands.Cog, description='only took multiple years (I think?)'):
    def __init__(self, bot):
        self.GUILD_ID = 722386163356270662
        self.STICKER_CHANNEL_ID = 1067821745379225663
        self.EMOJI_CHANNEL_ID = 1067822653655748718
        
        self.bot = bot
        self.db = bot.db
        
        self.auto_removed_chars = [' ', '\n']
        self.invalid_chars = [';', ':', '`']
        
        self.sticker_reply_ctx_menu = app_commands.ContextMenu(
            name='Sticker Reply',
            callback=self.reply
        )
        self.react_ctx_menu = app_commands.ContextMenu(
            name='React',
            callback=self.react
        )
        self.steal_ctx_menu = app_commands.ContextMenu(
            name='Steal',
            callback=self.steal
        )
        self.bot.tree.add_command(self.sticker_reply_ctx_menu)
        self.bot.tree.add_command(self.react_ctx_menu)
        self.bot.tree.add_command(self.steal_ctx_menu)
        
    async def fetch_sticker_url(self, message_id):
        sticker_channel = await self.bot.fetch_channel(self.STICKER_CHANNEL_ID)
        message = await sticker_channel.fetch_message(message_id)
        return message.attachments[0].url
    
    async def fetch_emoji_url(self, message_id):
        emoji_channel = await self.bot.fetch_channel(self.EMOJI_CHANNEL_ID)
        message = await emoji_channel.fetch_message(message_id)
        return message.attachments[0].url
    

    sticker = app_commands.Group(name='sticker', description='Finally, a sticker system')

    @sticker.command(name='add', description='Adds a sticker to your collection')
    async def add(self, interaction: discord.Interaction, name: str, image: discord.Attachment = None, image_url: str = '', aliases: str = ''):
        await interaction.response.defer(ephemeral=True, thinking=True)

        name_cleanup = await cleanup_name(name, self.bot.db, interaction.user.id)
        if name_cleanup[0] is None:
            return await interaction.followup.send(name_cleanup[1])
        else:
            name = name_cleanup[0]

        if aliases == '':
            if name.lower() != name:
                aliases_list = [name.lower()]
            else:
                aliases_list = []
        else:
            if name.lower() != name:
                aliases_list = [name.lower()] + aliases.split(';')
            else:
                aliases_list = aliases.split(';')

        aliases_cleanup = await cleanup_aliases(aliases_list, self.bot.db, interaction.user.id)
        aliases_list = aliases_cleanup[0]
        aliases_breakdown = aliases_cleanup[1]
        aliases_success = aliases_cleanup[2]

        if await self.bot.db.fetchval('SELECT user_id FROM users WHERE user_id = $1', interaction.user.id) is None:
            await self.bot.db.execute('INSERT INTO users (user_id) VALUES ($1)', interaction.user.id)

        if image is None and not is_image_url(image_url):
            return await interaction.followup.send('No images?', ephemeral=True)
        elif image is not None:
            if not image.content_type.startswith('image'):
                return await interaction.followup.send('No images?', ephemeral=True)

        prev_sticker_id = await self.bot.db.fetchval('SELECT sticker_id FROM stickers ORDER BY sticker_id DESC LIMIT 1')

        if prev_sticker_id is None:
            sticker_id = 72
        else:
            sticker_id = prev_sticker_id + 1

        try:
            if image is not None:
                if image.content_type.startswith('image'):
                    if image.content_type.startswith('image/gif'):
                        emoji = resize(await image.read(), f'{sticker_id}.gif', 128, 128)
                        sticker = resize(await image.read(), f'{sticker_id}.gif', 160, 160)
                    elif image.content_type.startswith('image/webp'):
                        emoji = resize(await image.read(), f'{sticker_id}.webp', 128, 128)
                        sticker = resize(await image.read(), f'{sticker_id}.webp', 160, 160)
                    else:
                        emoji = resize(await image.read(), f'{sticker_id}.png', 128, 128)
                        sticker = resize(await image.read(), f'{sticker_id}.png', 160, 160)
            elif is_image_url(image_url):
                response = requests.get(image_url)
                if response.headers.get('content-type').startswith('image/gif'):
                    emoji = resize(response.content, f'{sticker_id}.gif', 128, 128)
                    sticker = resize(response.content, f'{sticker_id}.gif', 160, 160)
                else:
                    emoji = resize(response.content, f'{sticker_id}.png', 128, 128)
                    sticker = resize(response.content, f'{sticker_id}.png', 160, 160)
        except:
            return await interaction.followup.send('The frick did you do...', ephemeral=True)

        guild = await self.bot.fetch_guild(self.GUILD_ID)
        sticker_channel = await guild.fetch_channel(self.STICKER_CHANNEL_ID)
        emoji_channel = await guild.fetch_channel(self.EMOJI_CHANNEL_ID)

        emoji_message = await emoji_channel.send(file=emoji)
        sticker_message = await sticker_channel.send(file=sticker)

        sticker_message_id = sticker_message.id
        emoji_message_id = emoji_message.id

        await self.bot.db.execute('INSERT INTO stickers (sticker_id, sticker_message_id, emoji_message_id) VALUES (DEFAULT, $1, $2)', sticker_message_id, emoji_message_id)
        sticker_id = await self.bot.db.fetchval('SELECT sticker_id FROM stickers WHERE sticker_message_id = $1', sticker_message_id)
        await self.bot.db.execute('INSERT INTO users_stickers (user_id, sticker_id, name, aliases) VALUES ($1, $2, $3, $4)', interaction.user.id, sticker_id, name, aliases_list)

        await interaction.followup.send(embed=generate_confirmation_embed('Added', name, aliases_breakdown, aliases_success, sticker_message.attachments[0].url), ephemeral=True)

    @sticker.command(name='send', description='Sends a sticker from your collection')
    async def send(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer(ephemeral=True)
        name = name.replace('\n', ' ')
        sticker_id = await self.bot.db.fetchval('SELECT sticker_id FROM users_stickers WHERE user_id = $1 AND (name = $2 OR $2 = ANY(aliases))', interaction.user.id, name)
        if sticker_id is None:
            return await interaction.followup.send('Unreal bro!!', ephemeral=True)
        message_id = await self.bot.db.fetchval('SELECT sticker_message_id FROM stickers WHERE sticker_id = $1', sticker_id)
        
        sticker_url = await self.fetch_sticker_url(message_id)

        webhook = await interaction.channel.create_webhook(name='Impostor')
        await webhook.send(content=sticker_url, username=interaction.user.display_name, avatar_url=interaction.user.display_avatar)
        await webhook.delete()

        await interaction.followup.send('Pain required response.', ephemeral=True)
        await interaction.delete_original_response()

    async def reply(self, interaction: discord.Interaction, message: discord.Message):
        await interaction.response.send_modal(ReplyModal(message, self))
        
    async def react(self, interaction: discord.Interaction, message: discord.Message):
        await interaction.response.send_modal(ReactModal(message, self))

    @sticker.command(name='delete', description='Deletes stickers from your collection')
    async def delete(self, interaction: discord.Interaction, names: str = ''):
        await interaction.response.defer(ephemeral=True)
        if names == '':
            options = []
            stickers = await self.bot.db.fetch('SELECT name, sticker_id FROM users_stickers WHERE user_id = $1', interaction.user.id)
            if stickers == []:
                return await interaction.followup.send('You have no stickers to delete silly!', ephemeral=True)
            i = 1
            for sticker in stickers:
                options.append(discord.SelectOption(label=sticker[0], value=sticker[1]))
                i += 1
            await interaction.followup.send(view=DeleteView(options, self.bot.db, interaction), ephemeral=True)
        else:
            successful_deletes = []
            names_list = names.split(';')
            for name in names_list:
                sticker_name = await self.bot.db.fetchval('SELECT name FROM users_stickers WHERE user_id = $1 AND (name = $2 OR $2 = ANY(aliases))', interaction.user.id, name)
                status = await self.bot.db.execute('DELETE FROM users_stickers WHERE user_id = $1 AND (name = $2 OR $2 = ANY(aliases))', interaction.user.id, name)
                if status != 'DELETE 0':
                    successful_deletes.append(sticker_name)
            embed = discord.Embed(title=f'{len(successful_deletes)} stickers removed successfully!', description=f'```{" ; ".join(successful_deletes)}```', color=0xeb4969)
            await interaction.followup.send(embed=embed, ephemeral=True)

    @sticker.command(name='view', description='View stickers from yours or others collections')
    async def view(self, interaction: discord.Interaction, user: discord.User = None, shown: bool = False):
        await interaction.response.defer(ephemeral = not shown)
        if user is None:
            sticker_user = interaction.user
        else:
            sticker_user = user
        stickers = await self.bot.db.fetch('SELECT name, sticker_id, aliases FROM users_stickers WHERE user_id = $1', sticker_user.id)
        if stickers == []:
            if sticker_user.id == interaction.user.id:
                return await interaction.followup.send('You have no stickers to view silly!', ephemeral=True)
            else:
                return await interaction.followup.send('They have no stickers to view smh!', ephemeral=True)
        pages = []
        grid_pages = []
        options = []
        i = 0
        for sticker in stickers:
            message_id = await self.bot.db.fetchval('SELECT sticker_message_id FROM stickers WHERE sticker_id = $1', sticker[1])
            sticker_url = await self.fetch_sticker_url(message_id)
            pages.append(discord.Embed(
                type='image',
                title=sticker[0],
                color=0xef5a93
            ).set_image(url=sticker_url).set_author(name=sticker_user.display_name, icon_url=sticker_user.display_avatar).set_footer(text=f'Page {i + 1}/{len(stickers)}'))
            options.append(discord.SelectOption(label=sticker[0], value=i))
            if i % 4 == 0:
                grid_pages.append([discord.Embed(color=0xef5a93, url='https://ko-fi.com/voxeldev').set_image(url=sticker_url).set_author(name=sticker_user.display_name, icon_url=sticker_user.display_avatar).set_footer(text=f'Page {i//4 + 1}/{math.ceil(len(stickers) / 4)}')])
            else:
                grid_pages[-1].append(discord.Embed(url='https://ko-fi.com/voxeldev').set_image(url=sticker_url))
            i += 1

        list_pages = await self.generate_list(stickers)
        
        await interaction.followup.send(embed=pages[0], view=ViewView(pages, grid_pages, list_pages, options, self.bot, interaction, sticker_user.id != interaction.user.id), ephemeral=not shown)

    @sticker.command(name='edit', description='Edit stickers from your collection')
    async def edit(self, interaction: discord.Interaction, name: str = ''):
        if name == '':
            await interaction.response.defer(ephemeral=True)
            stickers = await self.bot.db.fetch('SELECT name, sticker_id, aliases FROM users_stickers WHERE user_id = $1', interaction.user.id)
            if stickers == []:
                return await interaction.followup.send('You have no stickers to edit silly!', ephemeral=True)
            pages = []
            options = []
            i = 0
            for sticker in stickers:
                message_id = await self.bot.db.fetchval('SELECT sticker_message_id FROM stickers WHERE sticker_id = $1', sticker[1])
                sticker_url = await self.fetch_sticker_url(message_id)
                if sticker[2] is not None and sticker[2] != []:
                    alias_description = f'```{" ; ".join(sticker[2])}```'
                    pages.append(discord.Embed(
                        type='image',
                        title=sticker[0],
                        description=alias_description,
                        color=0xef5a93
                    ).set_image(url=sticker_url).set_footer(text=f'Page {i + 1}/{len(stickers)}'))
                else:
                    pages.append(discord.Embed(
                        type='image',
                        title=sticker[0],
                        color=0xef5a93
                    ).set_image(url=sticker_url).set_footer(text=f'Page {i + 1}/{len(stickers)}'))
                options.append(discord.SelectOption(label=sticker[0], value=i))
                i += 1

            await interaction.followup.send(embed=pages[0], view=EditView(pages, options, interaction, self.bot.db), ephemeral=True)
        else:
            name = name.replace('\n', ' ')
            sticker_id = await self.bot.db.fetchval('SELECT sticker_id FROM users_stickers WHERE user_id = $1 AND (name = $2 OR $2 = ANY(aliases))', interaction.user.id, name)
            if sticker_id is None:
                return await interaction.response.send_message('Unreal bro!!', ephemeral=True)
            sticker_name = await self.bot.db.fetchval('SELECT name FROM users_stickers WHERE user_id = $1 AND sticker_id = $2', interaction.user.id, sticker_id)
            aliases = await self.bot.db.fetchval('SELECT aliases FROM users_stickers WHERE user_id = $1 AND sticker_id = $2', interaction.user.id, sticker_id)
            if aliases is None:
                sticker_aliases = ''
            else:
                sticker_aliases = '\n'.join(aliases)
            await interaction.response.send_modal(EditModal(sticker_id, sticker_name, sticker_aliases, self.bot.db))

    @sticker.command(name='share', description='Shares a sticker from your collection')
    async def share(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer(ephemeral=True)
        name = name.replace('\n', ' ')
        sticker_details = await self.bot.db.fetchval('SELECT (sticker_id, name) FROM users_stickers WHERE user_id = $1 AND (name = $2 OR $2 = ANY(aliases))', interaction.user.id, name)
        if sticker_details[0] is None:
            return await interaction.followup.send('Unreal bro!!', ephemeral=True)
        message_id = await self.bot.db.fetchval('SELECT sticker_message_id FROM stickers WHERE sticker_id = $1', sticker_details[0])
        sticker_url = await self.fetch_sticker_url(message_id)

        embed = discord.Embed(
            type='image',
            title=sticker_details[1],
            color=0xef5a93
        ).set_image(url=sticker_url).set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar)

        await interaction.followup.send(embed=embed, view=ShareView(sticker_details[0], sticker_details[1], self.bot.db, interaction.user.id))


    async def steal(self, interaction: discord.Interaction, message: discord.Message):
        if message.webhook_id is not None and is_image_url(message.content):
            sticker_id = int(message.content.split('/')[-1].split('.')[0])
            if sticker_id is None:
                return await interaction.followup.send('This isn\'t a sticker xd', ephemeral=True)
            if await self.bot.db.fetchval('SELECT sticker_id FROM users_stickers WHERE user_id = $1 AND sticker_id = $2', interaction.user.id, sticker_id) is not None:
                return await interaction.response.send_message('You already have that sticker', ephemeral=True)
            return await attempt_steal(sticker_id, self.bot.db, interaction)
        await interaction.followup.send('the frick is this disappointing garbage nya?', ephemeral=True)

    async def generate_list(self, stickers):
        line_limit = 16
        length_limit = 48
        pages = []
        pages_num = len(stickers)//line_limit+1
        for i in range(0, len(stickers), line_limit):
            page = ''
            for sticker in stickers[i:i+line_limit]:
                if sticker[2] is not None and sticker[2] != []:
                    # arigatou min

                    temp_string = f'`{"` `".join(sticker[2])}`'
                    temp_visible_chars = 0
                    temp_index = 0
                    temp_optimise_limit = length_limit - len(sticker[0])
                    temp_optimise_strlen = len(temp_string)
                    while temp_visible_chars < temp_optimise_limit and temp_index < temp_optimise_strlen:
                        if temp_string[temp_index] != '`':
                            temp_visible_chars += 1
                        temp_index += 1
                    temp_string = temp_string[:temp_index]
                    if temp_string.count('`') % 2 == 1:
                        if temp_string[-1] == '`':
                            temp_string = temp_string[:-2]
                        elif temp_string[-2] == '`':
                            temp_string = temp_string[:-3]
                        else:
                            temp_string = temp_string[:-1] + '…`'
                    temp_optimise_more = int(len(sticker[2]) - temp_string.count('`') / 2)
                    if temp_optimise_more > 0:
                        temp_string += f' `+{temp_optimise_more}`'
                    page += f'{sticker[0]} {temp_string}\n'
                else:
                    page += f'{sticker[0]}\n'
            pages.append(discord.Embed(
                type='rich',
                title='Your Stickers',
                description=page,
                color=0xef5a93
            ).set_footer(text=f'Page {i//line_limit+1}/{pages_num}'))

        return pages
                

    @commands.Cog.listener()
    async def on_message(self, message):
        if ';' in message.content:
            guild = await self.bot.fetch_guild(self.GUILD_ID)
            emojis = []
            emoji_ids = []
            prev_was_emoji = False
            stickering_escaped = False
            split_message = (message.content).split(';')
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
                                    sticker = await self.bot.db.fetchval('SELECT (sticker_id, name) FROM users_stickers WHERE user_id = $1 AND (name = $2 OR $2 = ANY(aliases))', message.author.id, split_message[i])
                
                if sticker is None:
                    if not prev_was_emoji:
                        split_message[i] = ';' + split_message[i]
                    prev_was_emoji = False
                    continue

                prev_was_emoji = True

                message_id = await self.bot.db.fetchval('SELECT emoji_message_id FROM stickers WHERE sticker_id = $1', sticker[0])
                emoji_url = await self.fetch_emoji_url(message_id)
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
                            return await message.reply(f'Uhh {sticker[1]} is too big')
                        elif e.code == 30008: # reached max number of emojis
                            return await message.reply('too many emojis in that server')
                        elif e.code == 50035: # ????????
                            return await message.reply('it\'s the thing...')
                        else:
                            return await message.reply(e)
                    except asyncio.TimeoutError: # rate limited
                        for emoji in emojis:
                            await guild.delete_emoji(emoji)
                        return await message.reply('idk youprobably got rate limited or something')
                    emojis.append(emoji)
                    emoji_ids.append(sticker[0])
                else:
                    emoji = emojis[emoji_ids.index(sticker[0])]
                split_message[i] = str(emoji)
            
            emoji_message = ''.join(split_message)

            if emojis == []:
                return

            try:
                await message.delete()
            except:
                pass

            webhook = await message.channel.create_webhook(name='Impostor')
            await webhook.send(content=emoji_message, username=message.author.display_name, avatar_url= message.author.display_avatar, wait=True)
            await webhook.delete()

            for emoji in emojis:
                await guild.delete_emoji(emoji)
            
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id != self.bot.user.id and re.match(r'\d+_.+', payload.emoji.name):
            channel = await self.bot.fetch_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            try:
                await message.remove_reaction(payload.emoji, self.bot.user)
            except:
                pass
            
            

async def cleanup_name(name, db, user_id, prev_name = ''):
    breakdown = ''
    
    name = name.strip().replace('\n', ' ')
    if name == '':
        breakdown = 'You can\'t have an empty name...'
        return (None, breakdown)
    if ';' in name:
        breakdown = 'No semicolons!!'
        return (None, breakdown)
    if ':' in name:
        breakdown = 'No colons!!'
        return (None, breakdown)
    if '`' in name:
        breakdown = 'No backticks!!'
        return (None, breakdown)
    if emoji_count(name) > 0:
        breakdown = 'No emojis!!'
        return (None, breakdown)
    if len(name) > 100:
        breakdown = 'Exceeds 100 character!!'
        return(None, breakdown)
    
    if prev_name != name:
        while await db.fetchval('SELECT name FROM users_stickers WHERE user_id = $1 AND (name = $2 OR $2 = ANY(aliases))', user_id, name) is not None:
                if name[-2] == '~':
                    name = name[:-1] + str(int(name[-1]) + 1)
                else:
                    name = name + '~1'

    return (name, breakdown)

async def cleanup_aliases(aliases_list, db, user_id, prev_list=[]):
    cleaned_list = []
    breakdown = []
    success = 'All aliases were added successfully!'
    success_amount = 0
    alias_amount = len(aliases_list)
    for i in range(len(aliases_list)):
        if i == 16:
            break
        aliases_list[i] = aliases_list[i].strip().replace('\n', ' ')
        if aliases_list[i] != '' and aliases_list[i] not in cleaned_list:
            if aliases_list[i] not in prev_list:
                while await db.fetchval('SELECT name FROM users_stickers WHERE user_id = $1 AND (name = $2 OR $2 = ANY(aliases))', user_id, aliases_list[i]) is not None:
                    if aliases_list[i][-2] == '~':
                        aliases_list[i] = aliases_list[i][:-1] + str(int(aliases_list[i][-1]) + 1)
                    else:
                        aliases_list[i] = aliases_list[i] + '~1'
            
            if len(aliases_list[i]) > 50:
                alias_display = aliases_list[i][:50] + '...'
            else:
                alias_display = aliases_list[i]
            if ';' in aliases_list[i]:
                breakdown.append([alias_display, '❎ No semicolons!!'])
                success = 'Some aliases were rejected...'
            elif ':' in aliases_list[i]:
                breakdown.append([alias_display, '❎ No colons!!'])
                success = 'Some aliases were rejected...'
            elif '`' in aliases_list[i]:
                breakdown.append([alias_display, '❎ No backticks!!'])
                success = 'Some aliases were rejected...'
            elif emoji_count(aliases_list[i]) > 0:
                breakdown.append([alias_display, '❎ No emojis!!'])
                success = 'Some aliases were rejected...'
            elif len(aliases_list[i]) > 100:
                breakdown.append([alias_display,'❎ Exceeds 100 characters!!'])
                success = 'Some aliases were rejected...'
            else:
                success_amount += 1
                cleaned_list.append(aliases_list[i])
                if aliases_list[i] not in prev_list:
                    breakdown.append([alias_display, '✅'])
        else:
            alias_amount -= 1

    if success_amount != alias_amount:
        if success_amount == 0:
            success = 'All aliases were rejected...'
        elif alias_amount > 15:
            success = f'Only {success_amount} of {alias_amount} aliases were added successfully as you passed the limit of 15...'
        else:
            success = f'{success_amount} of {alias_amount} aliases were added successfully!'
    
    return (cleaned_list, breakdown, success)

def generate_confirmation_embed(confirmation_type, name, alias_breakdown, alias_success, sticker_url=None, color=0x9beba0):
    embed = discord.Embed(title=f'{confirmation_type} {name}!', color=color)
    embed.description = alias_success
    for breakdown in alias_breakdown:
        embed.add_field(name=breakdown[0], value=breakdown[1])

    if sticker_url is not None:
        embed.set_image(url=sticker_url)

    return embed

class DeleteView(ui.View):
    def __init__(self, options, db, interaction):
        super().__init__(timeout=60)
        self.latest_interaction = interaction
        self.current_select_page = 0
        self.options = options
        self.select = DeleteSelect(options[:25], db)
        self.add_item(self.select)
    
    @ui.button(emoji='<:previous:967665422633689138>', style=discord.ButtonStyle.secondary, row=1)
    async def previous_options(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_select_page == 0:
            self.current_select_page = len(self.options) // 25
        else:
            self.current_select_page = self.current_select_page - 1
        self.update_select()
        await interaction.response.edit_message(view=self)

    @ui.button(emoji='<:next:967665404589801512>', style=discord.ButtonStyle.secondary, row=1)
    async def next_options(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_select_page == len(self.options) // 25:
            self.current_select_page = 0
        else:
            self.current_select_page = self.current_select_page + 1
        self.update_select()
        await interaction.response.edit_message(view=self)

    def update_select(self):
        self.select.options = self.options[self.current_select_page * 25:(self.current_select_page + 1) * 25]
        self.select.max_values = len(self.select.options)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.latest_interaction.edit_original_response(view=self)

class DeleteSelect(ui.Select):
    def __init__(self, options, db):
        self.db = db
        max = len(options)
        super().__init__(placeholder='Choose stickers to delete', min_values=1, max_values=max, options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        successful_deletes = []
        for sticker_id in self.values:
            sticker_name = await self.db.fetchval('SELECT name FROM users_stickers WHERE user_id = $1 AND sticker_id = $2', interaction.user.id, int(sticker_id))
            await self.db.execute('DELETE FROM users_stickers WHERE user_id = $1 AND sticker_id = $2', interaction.user.id, int(sticker_id))
            successful_deletes.append(sticker_name)
        embed = discord.Embed(title=f'{len(successful_deletes)} stickers removed successfully!', description=f'```{" ; ".join(successful_deletes)}```', color=0xeb4969)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        self.view.stop()

class StickerView(ui.View):
    def __init__(self, pages, options, interaction):
        super().__init__(timeout=60)
        self.pages = pages
        self.grid = False
        self.list = False
        self.current_page = 0
        if options is not None:
            self.options = options
            self.select = StickerSelect(options[:25])
            self.current_select_page = 0
            self.add_item(self.select)
        else:
            self.remove_item(self.prevous_options)
            self.remove_item(self.next_options)
        self.author = interaction.user
        self.latest_interaction = interaction

    @ui.button(emoji='<:previousprevious:1097398096985604196>', style=discord.ButtonStyle.secondary, row=0)
    async def previous_options(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_select_page == 0:
            self.current_select_page = len(self.options) // 25
        else:
            self.current_select_page = self.current_select_page - 1
        self.update_select()
        self.current_page = self.current_select_page * 25
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @ui.button(emoji='<:previous:967665422633689138>', style=discord.ButtonStyle.primary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.grid:
            if self.current_page == 0:
                self.current_page = len(self.grid_pages) - 1
            else:
                self.current_page = self.current_page - 1
            await interaction.response.edit_message(embeds=self.grid_pages[self.current_page])
        elif self.list:
            if self.current_page == 0:
                self.current_page = len(self.list_pages) - 1
            else:
                self.current_page = self.current_page - 1
            await interaction.response.edit_message(embed=self.list_pages[self.current_page])
        else:
            if self.current_page == 0:
                self.current_page = len(self.pages) - 1
                self.current_select_page = (len(self.options) - 1) // 25
                self.update_select()
            else:
                if self.current_page % 25 == 0:
                    self.current_select_page = self.current_select_page - 1
                    self.update_select()
                self.current_page = self.current_page - 1
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @ui.button(emoji='<:next:967665404589801512>', style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.grid:
            if self.current_page == len(self.grid_pages) - 1:
                self.current_page = 0
            else:
                self.current_page = self.current_page + 1
            await interaction.response.edit_message(embeds=self.grid_pages[self.current_page])
        elif self.list:
            if self.current_page == len(self.list_pages) - 1:
                self.current_page = 0
            else:
                self.current_page = self.current_page + 1
            await interaction.response.edit_message(embed=self.list_pages[self.current_page])
        else:
            if self.current_page == len(self.pages) - 1:
                self.current_select_page = 0
                self.update_select()
                self.current_page = 0
            else:
                self.current_page = self.current_page + 1
                if self.current_page % 25 == 0:
                    self.current_select_page = self.current_select_page + 1
                    self.update_select()
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @ui.button(emoji='<:nextnext:1097397983265431552>', style=discord.ButtonStyle.secondary, row=0)
    async def next_options(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_select_page == len(self.options) // 25:
            self.current_select_page = 0
        else:
            self.current_select_page = self.current_select_page + 1
        self.update_select()
        self.current_page = self.current_select_page * 25
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    def update_select(self):
        self.select.options = self.options[self.current_select_page * 25:(self.current_select_page + 1) * 25]
    
    async def interaction_check(self, interaction: discord.Interaction):
        result = interaction.user.id == self.author.id
        self.latest_interaction = interaction
        return result

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.grid:
            self.grid_pages[self.current_page][0].color = None
            await self.latest_interaction.edit_original_response(embeds=self.grid_pages[self.current_page], view=self)
        elif self.list:
            self.list_pages[self.current_page].color = None
            await self.latest_interaction.edit_original_response(embed=self.list_pages[self.current_page], view=self)
        else:
            self.pages[self.current_page].color = None
            await self.latest_interaction.edit_original_response(embed=self.pages[self.current_page], view=self)
        return

class StickerSelect(ui.Select):
    def __init__(self, options):
        super().__init__(placeholder='Choose a sticker to view', min_values=1, max_values=1, options=options, row=1)

    async def callback(self, interaction: discord.Interaction):
        self.view.current_page = int(self.values[0])
        await interaction.response.edit_message(embed=self.view.pages[self.view.current_page])

class ViewView(StickerView):
    def __init__(self, pages, grid_pages, list_pages, options, bot, interaction, steal):
        super().__init__(pages=pages, options=options, interaction=interaction)
        self.grid_pages = grid_pages
        self.list_pages = list_pages
        self.bot = bot
        self.db = bot.db
        self.steal = steal
        self.STICKER_CHANNEL_ID = 1067821745379225663
        self.remove_item(self.single_view)
        if steal:
            self.steal = StealButton(self)
            self.add_item(self.steal)
        else:
            self.send = SendButton(self)
            self.add_item(self.send)

    @ui.button(label='Single', style=discord.ButtonStyle.secondary, row=2)
    async def single_view(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.remove_item(self.single_view)

        if self.grid:
            self.current_page = self.current_page * 4
            self.remove_item(self.list_view)
            self.add_item(self.grid_view)
            self.add_item(self.list_view)
            self.grid = False
        else:
            self.current_page = self.current_page * 16
            self.add_item(self.list_view)
            self.list = False
        
        self.add_item(self.select)
        self.remove_item(self.next_page)
        self.remove_item(self.previous_page)
        self.add_item(self.previous_options)
        self.add_item(self.previous_page)
        self.add_item(self.next_page)
        self.add_item(self.next_options)
        if self.steal:
            self.add_item(self.steal)
        else:
            self.add_item(self.send)

        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @ui.button(label='Grid', style=discord.ButtonStyle.secondary, row=2)
    async def grid_view(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.remove_item(self.grid_view)

        if self.list:
            self.current_page = self.current_page * 4
            self.add_item(self.list_view)
        else:
            if self.steal:
                self.remove_item(self.steal)
            else:
                self.remove_item(self.send)
            self.current_page = self.current_page // 4
            self.remove_item(self.select)
            self.remove_item(self.previous_options)
            self.remove_item(self.next_options)
            self.remove_item(self.list_view)
            self.add_item(self.single_view)
            self.add_item(self.list_view)
            
        self.grid = True
        self.list = False

        await interaction.response.edit_message(embeds=self.grid_pages[self.current_page], view=self)

    @ui.button(label='List', style=discord.ButtonStyle.secondary, row=2)
    async def list_view(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.remove_item(self.list_view)

        if self.grid:
            self.current_page = self.current_page // 4
            self.add_item(self.grid_view)
            self.grid = False
        else:
            if self.steal:
                self.remove_item(self.steal)
            else:
                self.remove_item(self.send)
            self.current_page = self.current_page // 16
            self.remove_item(self.select)
            self.remove_item(self.previous_options)
            self.remove_item(self.next_options)
            self.remove_item(self.grid_view)
            self.add_item(self.single_view)
            self.add_item(self.grid_view)
        self.list = True

        await interaction.response.edit_message(embed=self.list_pages[self.current_page], view=self)

class ShareView(ui.View):
    def __init__(self, sticker_id, name, db, user_id):
        super().__init__()
        self.user_id = user_id
        self.add_item(SingleStealButton(sticker_id, name, db))

    async def interaction_check(self, interaction: discord.Interaction):
        result = interaction.user.id != self.user_id
        return result
    
    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.latest_interaction.edit_original_response(view=self)
        return

class SingleStealButton(ui.Button):
    def __init__(self, sticker_id, name, db):
        super().__init__(label='Steal', style=discord.ButtonStyle.green)
        self.sticker_id = sticker_id
        self.name = name
        self.db = db
    
    async def callback(self, interaction: discord.Interaction):
        await attempt_steal(self.sticker_id, self.db, interaction, name=self.name)

class StealButton(ui.Button):
    def __init__(self, parent):
        super().__init__(label='Steal', style=discord.ButtonStyle.green, row=2)
        self.parent = parent

    async def callback(self, interaction: discord.Interaction):
        sticker_id = int(self.parent.pages[self.parent.current_page].image.url.split('/')[-1].split('.')[0])
        name = self.parent.pages[self.parent.current_page].title
        await attempt_steal(sticker_id, self.parent.db, interaction, name)
        
class SendButton(ui.Button):
    def __init__(self, parent):
        super().__init__(label='Send', style=discord.ButtonStyle.green, row=2)
        self.parent = parent

    async def callback(self, interaction: discord.Interaction):
        sticker_id = int(self.parent.pages[self.parent.current_page].image.url.split('/')[-1].split('.')[0])
        
        message_id = await self.parent.db.fetchval('SELECT sticker_message_id FROM stickers WHERE sticker_id = $1', sticker_id)
        
        sticker_channel = await self.parent.bot.fetch_channel(self.parent.STICKER_CHANNEL_ID)
        message = await sticker_channel.fetch_message(message_id)
        sticker_url = message.attachments[0].url

        webhook = await interaction.channel.create_webhook(name='Impostor')
        await webhook.send(content=sticker_url, username=interaction.user.display_name, avatar_url=interaction.user.display_avatar)
        await webhook.delete()

class EditView(StickerView):
    def __init__(self, pages, options, interaction, db):
        super().__init__(pages=pages, options=options, interaction=interaction)
        self.db = db

    @ui.button(label='Edit', style=discord.ButtonStyle.secondary, row=2)
    async def edit_sticker(self, interaction: discord.Interaction, button: discord.ui.Button):
        name = self.pages[self.current_page].title
        sticker_id = await self.db.fetchval('SELECT sticker_id FROM users_stickers WHERE user_id = $1 AND name = $2', interaction.user.id, name)
        if self.pages[self.current_page].description is None:
            sticker_aliases = ''
        else:
            aliases = self.pages[self.current_page].description[3:-3].split(' ; ')
            sticker_aliases = '\n'.join(aliases)
        await interaction.response.send_modal(EditModal(sticker_id, name, sticker_aliases, self.db, self))

    @ui.button(label='Delete', style=discord.ButtonStyle.danger, row=2)
    async def delete_sticker(self, interaction: discord.Interaction, button: discord.ui.Button):
        name = self.pages[self.current_page].title
        status = await self.db.execute('DELETE FROM users_stickers WHERE user_id = $1 AND name = $2', interaction.user.id, name)
        if status == 'DELETE 0':
            await interaction.response.send_message('idk something went wrong', ephemeral=True)
        else:
            self.pages.pop(self.current_page)
            self.select.options.pop(self.current_page % 25)
            self.options.pop(self.current_page)
            for i in range(self.current_page % 25, len(self.select.options)):
                self.select.options[i].value = str(int(self.select.options[i].value) - 1)
            for i in range(self.current_page, len(self.options)):
                self.options[i].value = str(int(self.options[i].value) - 1)

            if self.current_page > len(self.pages) - 1:
                self.current_page = 0
            if len(self.pages) == 0:
                await interaction.response.edit_message(embed=discord.Embed(title='You have no stickers!'), view=None)
            else:
                await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)
            embed=discord.Embed(title=f'{name} has been removed from your collection!')
            await interaction.followup.send(embed=embed, ephemeral=True)


class EditModal(ui.Modal, title='Edit Sticker'):
    def __init__(self, sticker_id, name, aliases, db, parent = None):
        super().__init__()
        self.sticker_id = sticker_id
        self.db = db
        self.prev_name = name
        self.prev_aliases = aliases
        self.parent = parent

        self.name_input = ui.TextInput(label='Name', style = discord.TextStyle.short, required=True, min_length=1, max_length=100, default=name)
        self.add_item(self.name_input)
        self.aliases_input = ui.TextInput(label='Aliases', style = discord.TextStyle.long, required=False, min_length=0, max_length=1500, default=aliases)
        self.add_item(self.aliases_input)

    async def on_submit(self, interaction: discord.Interaction):
        name_cleanup = await cleanup_name(self.name_input.value, self.db, interaction.user.id, self.prev_name)
        if name_cleanup[0] is None:
            return await interaction.response.send_message(name_cleanup[1])
        else:
            name = name_cleanup[0]

        if self.aliases_input.value == '' or self.aliases_input.value is None:
            aliases_list = []
        else:
            aliases_list = self.aliases_input.value.split('\n')

        aliases_cleanup = await cleanup_aliases(aliases_list, self.db, interaction.user.id, self.prev_aliases)
        aliases_list = aliases_cleanup[0]
        aliases_breakdown = aliases_cleanup[1]
        aliases_success = aliases_cleanup[2]

        await self.db.execute('UPDATE users_stickers SET name = $1, aliases = $2 WHERE user_id = $3 AND sticker_id = $4', name, aliases_list, interaction.user.id, self.sticker_id)

        if self.parent is None:
            await interaction.response.send_message(embed=generate_confirmation_embed('Edited', name, aliases_breakdown, aliases_success, color=0xa7cdfa), ephemeral=True)
        else:
            if aliases_list is None or aliases_list == []:
                alias_description = None
            else:
                alias_description = f'```{" ; ".join(aliases_list)}```'

            self.parent.pages[self.parent.current_page].title = name
            self.parent.pages[self.parent.current_page].description = alias_description
            self.parent.select.options[self.parent.current_page % 25].label = name
            self.parent.options[self.parent.current_page].label = name
            await interaction.response.edit_message(embed=self.parent.pages[self.parent.current_page], view=self.parent)

async def attempt_steal(sticker_id, db, interaction, name = '', ):
    if await db.fetchval('SELECT EXISTS(SELECT 1 FROM users_stickers WHERE user_id = $1 AND sticker_id = $2)', interaction.user.id, sticker_id):
        return await interaction.response.send_message('You already have this sticker!', ephemeral=True)
    await interaction.response.send_modal(StealModal(sticker_id, db, name))

class StealModal(ui.Modal, title='Steal Sticker'):
    def __init__(self, sticker_id, db, name = ''):
        super().__init__()
        self.sticker_id = sticker_id
        self.db = db
        
        self.name_input = ui.TextInput(label='Name', style = discord.TextStyle.short, required=True, min_length=1, max_length=100, default=name)
        self.add_item(self.name_input)
        self.aliases_input = ui.TextInput(label='Aliases', style = discord.TextStyle.long, required=False, min_length=0, max_length=1500)
        self.add_item(self.aliases_input)

    async def on_submit(self, interaction: discord.Interaction):
        name_cleanup = await cleanup_name(self.name_input.value, self.db, interaction.user.id)
        if name_cleanup[0] is None:
            return await interaction.response.send_message(name_cleanup[1], ephemeral=True)
        else:
            name = name_cleanup[0]

        if self.aliases_input.value == '' or self.aliases_input.value is None:
            if name.lower() != name:
                aliases_list = [name.lower()]
            else:
                aliases_list = []
        else:
            aliases_list = [name.lower()] + self.aliases_input.value.split('\n')

        aliases_cleanup = await cleanup_aliases(aliases_list, self.db, interaction.user.id)
        aliases_list = aliases_cleanup[0]
        aliases_breakdown = aliases_cleanup[1]
        aliases_success = aliases_cleanup[2]

        if await self.db.fetchval('SELECT user_id FROM users WHERE user_id = $1', interaction.user.id) is None:
            await self.db.execute('INSERT INTO users (user_id) VALUES ($1)', interaction.user.id)

        await self.db.execute('INSERT INTO users_stickers (user_id, sticker_id, name, aliases) VALUES ($1, $2, $3, $4)', interaction.user.id, self.sticker_id, name, aliases_list)

        await interaction.response.send_message(embed=generate_confirmation_embed('Stole', name, aliases_breakdown, aliases_success, color=0xd19cf0), ephemeral=True)

class ReplyModal(ui.Modal, title='Reply'):
    def __init__(self, message: discord.Message, stickers):
        super().__init__()
        self.message = message
        self.stickers = stickers
        self.db = stickers.db

        self.name_input = ui.TextInput(label='Sticker Name', style = discord.TextStyle.short, required=True, min_length=1, max_length=100)
        self.add_item(self.name_input)

    async def on_submit(self, interaction: discord.Interaction):
        name = self.name_input.value.replace('\n', ' ')
        sticker_id = await self.db.fetchval('SELECT sticker_id FROM users_stickers WHERE user_id = $1 AND (name = $2 OR $2 = ANY(aliases))', interaction.user.id, name)
        if sticker_id is None:
            return await interaction.response.send_message('Unreal bro!!', ephemeral=True)
        message_id = await self.db.fetchval('SELECT sticker_message_id FROM stickers WHERE sticker_id = $1', sticker_id)
        sticker_url = await self.stickers.fetch_sticker_url(message_id)

        await interaction.response.send_message('Pain required response.', ephemeral=True)
        await interaction.delete_original_response()

        webhook = await interaction.channel.create_webhook(name='Impostor')
        file = await url_to_file(sticker_url, sticker_url.split('/')[-1])
        await webhook.send(content=self.message.jump_url, file=file, username=interaction.user.display_name, avatar_url=interaction.user.display_avatar)
        await webhook.delete()
        
class ReactModal(ui.Modal, title='React'):
    def __init__(self, message: discord.Message, stickers):
        super().__init__()
        self.message = message
        self.stickers = stickers
        self.bot = stickers.bot
        self.db = stickers.bot.db
        self.GUILD_ID = stickers.GUILD_ID
        
        self.emojis = ui.TextInput(
            label='Emojis',
            style=discord.TextStyle.short,
            required=True,
            min_length=1,
            max_length=100
        )
        self.add_item(self.emojis)
        
    async def on_submit(self, interaction: discord.Interaction):
        guild = await self.bot.fetch_guild(self.GUILD_ID)
        emojis = []
        emoji_ids = []
        emoji_input = re.split(r'\n|;', self.emojis.value)
        
        await interaction.response.send_message('Pain required response.', ephemeral=True)
        await interaction.delete_original_response()
        
        for emoji_name in emoji_input:
            sticker = await self.db.fetchval('SELECT (sticker_id, name) FROM users_stickers WHERE user_id = $1 AND (name = $2 OR $2 = ANY(aliases))', interaction.user.id, emoji_name.strip())
            if sticker is None:
                continue
            message_id = await self.db.fetchval('SELECT emoji_message_id FROM stickers WHERE sticker_id = $1', sticker[0])
            emoji_url = await self.stickers.fetch_emoji_url(message_id)
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
                    print(e)
                except asyncio.TimeoutError:
                    continue
                emojis.append(emoji)
                emoji_ids.append(sticker[0])
            
        if emojis == []:
            return
        
        for emoji in emojis:
            await self.message.add_reaction(emoji)
            await guild.delete_emoji(emoji)
            
        await asyncio.sleep(60)
        
        for emoji in emojis:
            try:
                await self.message.remove_reaction(emoji, self.bot.user)
            except:
                pass
        
async def setup(bot):
    await bot.add_cog(Stickers(bot))
