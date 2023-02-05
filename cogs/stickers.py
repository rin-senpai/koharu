import discord
from discord import ui, app_commands
from discord.ext import commands
import requests
from .utils.image import resize, is_image_url

class Stickers(commands.Cog, description='only took multiple years (I think?)'):
    def __init__(self, bot):
        self.bot = bot
        self.steal_ctx_menu = app_commands.ContextMenu(
            name='Steal',
            callback=self.steal
        )
        self.bot.tree.add_command(self.steal_ctx_menu)

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

        guild = await self.bot.fetch_guild(722386163356270662)
        emoji_channel = await guild.fetch_channel(1067822653655748718)
        sticker_channel = await guild.fetch_channel(1067821745379225663)

        emoji_message = await emoji_channel.send(file=emoji)
        sticker_message = await sticker_channel.send(file=sticker)

        emoji_url = emoji_message.attachments[0].url
        sticker_url = sticker_message.attachments[0].url

        await self.bot.db.execute('INSERT INTO stickers (sticker_id, sticker_url, emoji_url) VALUES (DEFAULT, $1, $2)', sticker_url, emoji_url)
        sticker_id = await self.bot.db.fetchval('SELECT sticker_id FROM stickers WHERE sticker_url = $1', sticker_url)
        await self.bot.db.execute('INSERT INTO users_stickers (user_id, sticker_id, name, aliases) VALUES ($1, $2, $3, $4)', interaction.user.id, sticker_id, name, aliases_list)

        await interaction.followup.send(embed=generate_confirmation_embed('Added', name, aliases_breakdown, aliases_success, sticker_url), ephemeral=True)

    @sticker.command(name='send', description='Sends a sticker from your collection')
    async def send(self, interaction: discord.Interaction, name: str):
        name = name.replace('\n', ' ')
        sticker_id = await self.bot.db.fetchval('SELECT sticker_id FROM users_stickers WHERE user_id = $1 AND (name = $2 OR $2 = ANY(aliases))', interaction.user.id, name)
        if sticker_id is None:
            return await interaction.response.send_message('Unreal bro!!', ephemeral=True)
        sticker_url = await self.bot.db.fetchval('SELECT sticker_url FROM stickers WHERE sticker_id = $1', sticker_id)

        webhook = await interaction.channel.create_webhook(name='Impostor')
        await webhook.send(content=sticker_url, username=interaction.user.nick, avatar_url=interaction.user.display_avatar)
        await webhook.delete()

        await interaction.response.send_message('Pain required response.', ephemeral=True)
        await interaction.delete_original_response()

    @sticker.command(name='delete', description='Deletes stickers from your collection')
    async def delete(self, interaction: discord.Interaction, names: str = ''):
        if names == '':
            options = []
            stickers = await self.bot.db.fetch('SELECT name, sticker_id FROM users_stickers WHERE user_id = $1', interaction.user.id)
            if stickers == []:
                return await interaction.response.send_message('You have no stickers to delete silly!', ephemeral=True)
            i = 1
            for sticker in stickers:
                if i > 25:
                    break
                options.append(discord.SelectOption(label=sticker[0], value=sticker[1]))
                i += 1
            await interaction.response.send_message(view=DeleteView(options, self.bot.db, interaction), ephemeral=True)
        else:
            successful_deletes = []
            names_list = names.split(';')
            for name in names_list:
                status = await self.bot.db.execute('DELETE FROM users_stickers WHERE user_id = $1 AND (name = $2 OR $2 = ANY(aliases))', interaction.user.id, name)
                if status != 'DELETE 0':
                    successful_deletes.append(name)
            embed = discord.Embed(title=f'{len(successful_deletes)} stickers removed successfully!', description=f'```{" ; ".join(successful_deletes)}```', color=0xeb4969)
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @sticker.command(name='view', description='View stickers from yours or others collections')
    async def view(self, interaction: discord.Interaction, user: discord.User = None):
        if user is None:
            sticker_user = interaction.user
        else:
            sticker_user = user
        stickers = await self.bot.db.fetch('SELECT name, sticker_id FROM users_stickers WHERE user_id = $1', sticker_user.id)
        if stickers == []:
            if sticker_user.id == interaction.user.id:
                return await interaction.response.send_message('You have no stickers to view silly!', ephemeral=True)
            else:
                return await interaction.response.send_message('They have no stickers to view smh!', ephemeral=True)
        pages = []
        grid_pages = []
        options = []
        i = 0
        for sticker in stickers:
            sticker_url = await self.bot.db.fetchval('SELECT sticker_url FROM stickers WHERE sticker_id = $1', sticker[1])
            pages.append(discord.Embed(
                type='image',
                title=sticker[0],
                color=0xef5a93
            ).set_image(url=sticker_url).set_author(name=sticker_user.display_name, icon_url=sticker_user.display_avatar))
            if i < 25:
                options.append(discord.SelectOption(label=sticker[0], value=i))
            if i % 4 == 0:
                grid_pages.append([discord.Embed(color=0xef5a93, url='https://ko-fi.com/voxeldev').set_image(url=sticker_url).set_author(name=sticker_user.display_name, icon_url=sticker_user.display_avatar)])
            else:
                grid_pages[-1].append(discord.Embed(url='https://ko-fi.com/voxeldev').set_image(url=sticker_url))
            i += 1
        
        await interaction.response.send_message(embed=pages[0], view=ViewView(pages, grid_pages, options, self.bot.db, interaction))

    @sticker.command(name='edit', description='Edit stickers from your collection')
    async def edit(self, interaction: discord.Interaction, name: str = ''):
        if name == '':
            stickers = await self.bot.db.fetch('SELECT name, sticker_id, aliases FROM users_stickers WHERE user_id = $1', interaction.user.id)
            if stickers == []:
                return await interaction.response.send_message('You have no stickers to edit silly!', ephemeral=True)
            pages = []
            options = []
            i = 0
            for sticker in stickers:
                sticker_url = await self.bot.db.fetchval('SELECT sticker_url FROM stickers WHERE sticker_id = $1', sticker[1])
                if sticker[2] is not None and sticker[2] != []:
                    alias_description = f'```{" ; ".join(sticker[2])}```'
                    pages.append(discord.Embed(
                        type='image',
                        title=sticker[0],
                        description=alias_description,
                        color=0xef5a93
                    ).set_image(url=sticker_url))
                else:
                    pages.append(discord.Embed(
                        type='image',
                        title=sticker[0],
                        color=0xef5a93
                    ).set_image(url=sticker_url))
                if i < 25:
                    options.append(discord.SelectOption(label=sticker[0], value=i))
                i += 1

            await interaction.response.send_message(embed=pages[0], view=EditView(pages, options, interaction, self.bot.db), ephemeral=True)
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

    async def steal(self, interaction: discord.Interaction, message: discord.Message):
        if message.webhook_id is not None and is_image_url(message.content):
            sticker_id = await self.bot.db.fetchval('SELECT sticker_id FROM stickers WHERE sticker_url = $1', message.content)
            if sticker_id is None:
                return await interaction.response.send_message('This isn\'t a sticker xd', ephemeral=True)
            if await self.bot.db.fetchval('SELECT sticker_id FROM users_stickers WHERE user_id = $1 AND sticker_id = $2', interaction.user.id, sticker_id) is not None:
                return await interaction.response.send_message('You already have that sticker', ephemeral=True)
            return await interaction.response.send_modal(StealModal(sticker_id, self.bot.db))
        await interaction.response.send_message('the frick is this disappointing garbage nya?', ephemeral=True)
                

    """ @commands.Cog.listener()
    async def on_message(self, message):
        if ';' in message.content:
            guild = await self.bot.fetch_guild(722386163356270662)
            emojis = []
            split_message = (message.content).split(';')
            skip = False
            for i in range(1, len(split_message) - 1):
                if skip:
                    skip = False
                    continue
                split_message[i] = split_message[i].strip().replace('\n', ' ')
                sticker = await self.bot.db.fetchval('SELECT (sticker_id, name) FROM users_stickers WHERE user_id = $1 AND (name = $2 OR ((ARRAY_TO_STRING(aliases, $4) LIKE $3)))', message.author.id, split_message[i], '%' + split_message[i] + '%', ';')
                if sticker is None:
                    continue
                sticker_url = await self.bot.db.fetchval('SELECT sticker_url FROM stickers WHERE sticker_id = $1', sticker[0])
                emoji = await guild.create_custom_emoji(name=f'{sticker[0]}_{sticker[1]}', image=requests.get(sticker_url).content)
                emojis.append(emoji)
                split_message[i] = str(emoji)
                skip = True
            
            emoji_message = ''.join(split_message)

            if emojis == []:
                return

            webhook = await message.channel.create_webhook(name='Impostor')
            await webhook.send(content=emoji_message, username=message.author.nick, avatar_url= message.author.display_avatar)
            await message.delete()
            await webhook.delete()

            for emoji in emojis:
                await guild.delete_emoji(emoji)

            # I DOUBT THIS WILL HELP BUT CHECK IF IT'S FASTER ON MOBILE HOTSPOT """

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
        super().__init__(timeout=120)
        self.latest_interaction = interaction
        self.add_item(DeleteSelect(options, db))

    async def interaction_check(self, interaction: discord.Interaction):
        result = interaction.user.id == self.author.id
        self.latest_interaction = interaction
        return result

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.latest_interaction.edit_original_response(view=self)

class DeleteSelect(ui.Select):
    def __init__(self, options, db):
        self.db = db
        if len(options) < 25:
            max = len(options)
        else:
            max = 25
        super().__init__(placeholder='Choose stickers to delete', min_values=1, max_values=max, options=options)

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
        super().__init__(timeout=120)
        self.pages = pages
        self.grid = False
        self.current_page = 0
        self.options = options
        self.author = interaction.user
        self.add_item(StickerSelect(options))
        self.latest_interaction = interaction

    @ui.button(emoji='<:previous:967665422633689138>', style=discord.ButtonStyle.primary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.grid:
            if self.current_page == 0:
                self.current_page = len(self.pages) - 1
            else:
                self.current_page = self.current_page - 1
            await interaction.response.edit_message(embed=self.pages[self.current_page])
        else:
            if self.current_page == 0:
                self.current_page = len(self.grid_pages) - 1
            else:
                self.current_page = self.current_page - 1
            await interaction.response.edit_message(embeds=self.grid_pages[self.current_page])

    @ui.button(emoji='<:next:967665404589801512>', style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.grid:
            if self.current_page == len(self.pages) - 1:
                self.current_page = 0
            else:
                self.current_page = self.current_page + 1
            await interaction.response.edit_message(embed=self.pages[self.current_page])
        else:
            if self.current_page == len(self.grid_pages) - 1:
                self.current_page = 0
            else:
                self.current_page = self.current_page + 1
            await interaction.response.edit_message(embeds=self.grid_pages[self.current_page])
    
    async def interaction_check(self, interaction: discord.Interaction):
        result = interaction.user.id == self.author.id
        self.latest_interaction = interaction
        return result

    async def on_timeout(self):
        if len(self.pages) != 0:
            for child in self.children:
                child.disabled = True
            self.pages[self.current_page].color = None
            await self.latest_interaction.edit_original_response(embed=self.pages[self.current_page], view=self)
        return

class StickerSelect(ui.Select):
    def __init__(self, options):
        super().__init__(placeholder='Choose a sticker to view', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        self.view.current_page = int(self.values[0])
        await interaction.response.edit_message(embed=self.view.pages[self.view.current_page])

class ViewView(StickerView):
    def __init__(self, pages, grid_pages, options, db, interaction):
        super().__init__(pages=pages, options=options, interaction=interaction)
        self.grid_pages = grid_pages
        self.db = db
        if interaction.user.nick != pages[0].author.name:
            self.add_item(StealButton(self))

    @ui.button(label='Grid', style=discord.ButtonStyle.secondary)
    async def grid_view(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.grid = not self.grid
        if self.grid:
            self.current_page = self.current_page // 4
            self.remove_item(self.children[-1])
            if interaction.user.nick != self.pages[0].author.name:
                self.remove_item(self.children[-1])
            button.label='Single'
            await interaction.response.edit_message(embeds=self.grid_pages[self.current_page], view=self)
        else:
            self.current_page = self.current_page * 4
            self.add_item(StickerSelect(self.options))
            if interaction.user.nick != self.pages[0].author.name:
                self.add_item(StealButton(self))
            button.label='Grid'
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

class StealButton(ui.Button):
    def __init__(self, parent):
        super().__init__(label='Steal', style=discord.ButtonStyle.secondary)
        self.parent = parent

    async def callback(self, interaction: discord.Interaction):
        sticker_id = int(self.parent.pages[self.parent.current_page].image.url.split('/')[-1].split('.')[0])
        name = self.parent.pages[self.parent.current_page].title
        await interaction.response.send_modal(StealModal(sticker_id, self.parent.db, name))

class EditView(StickerView):
    def __init__(self, pages, options, interaction, db):
        super().__init__(pages=pages, options=options, interaction=interaction)
        self.db = db

    @ui.button(label='Edit', style=discord.ButtonStyle.secondary)
    async def edit_sticker(self, interaction: discord.Interaction, button: discord.ui.Button):
        name = self.pages[self.current_page].title
        sticker_id = await self.db.fetchval('SELECT sticker_id FROM users_stickers WHERE user_id = $1 AND name = $2', interaction.user.id, name)
        if self.pages[self.current_page].description is None:
            sticker_aliases = ''
        else:
            aliases = self.pages[self.current_page].description[3:-3].split(' ; ')
            sticker_aliases = '\n'.join(aliases)
        await interaction.response.send_modal(EditModal(sticker_id, name, sticker_aliases, self.db, self))

    @ui.button(label='Delete', style=discord.ButtonStyle.danger)
    async def delete_sticker(self, interaction: discord.Interaction, button: discord.ui.Button):
        name = self.pages[self.current_page].title
        status = await self.db.execute('DELETE FROM users_stickers WHERE user_id = $1 AND name = $2', interaction.user.id, name)
        if status == 'DELETE 0':
            await interaction.response.send_message('idk something went wrong', ephemeral=True)
        else:
            self.pages.pop(self.current_page)
            self.children[4].options.pop(self.current_page)
            for i in range(self.current_page, len(self.children[4].options)):
                self.children[4].options[i].value  = str(int(self.children[4].options[i].value) - 1)

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
            self.parent.children[4].options[self.parent.current_page].label = name
            await interaction.response.edit_message(embed=self.parent.pages[self.parent.current_page], view=self.parent)

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

async def setup(bot):
    await bot.add_cog(Stickers(bot), guilds=[discord.Object(id=752052271935914064), discord.Object(id=722386163356270662)])
