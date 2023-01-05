from discord import ui, app_commands
import discord
from discord.ext import commands
import requests
import asyncio
from .utils.image import resize, is_image_url
from .utils.embeds import generate_embed

title = None
description = None
color = 0xef5a93
footer = None
image = None
thumbnail = None
author = None
author_image = None
footer_image = None
fields = None

embed_preview = None
selected_field = None
field_view = None
field_interaction = None

class Utility(commands.Cog, description='Only my *true* kouhai can use me, but I don\'t mind if others find utility in me. 👉 👈'):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['colour'], description='Sets your role color.', help='This uses discord\'s implementation of colors. As such, hex codes must be prefixed with `#`. Additionally, you can use pre-specified colors such as `red` or `blue` etc.')
    async def color(self, ctx, color: discord.Colour):
        role = discord.utils.get(ctx.guild.roles, name=f'{ctx.author.id}')
        if role is None:
            role = await ctx.guild.create_role(name=f'{ctx.author.id}', color=color)
            await ctx.author.add_roles(role)
            return await ctx.send(f'Your role has been created and updated to {color}.')
        await role.edit(colour=color)
        if role not in ctx.author.roles:
            await ctx.author.add_roles(role)
        await ctx.send(f'Your role has been updated to {color}.')

    @color.error
    async def color_error(self, ctx, error):
        if isinstance(error, commands.BadColourArgument):
            await ctx.reply('That doesn\'t seem to be a valid color.')

    @commands.hybrid_command(aliases=['pfp'], description='Sends the profile picture of the specified user.', help='If no user is specified, your own profile picture will be sent.')
    async def avatar(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author
        embed = discord.Embed(title=f'{member.name}\'s Avatar', url=member.avatar.url)
        embed.set_image(url=member.avatar.url)
        await ctx.send(embed=embed)

    @commands.group(aliases=['im', 'img'], description='Manipulates images.')
    async def image(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.reply('Where valid subcommand. (I should probably make these also do senpai nani group command in the future)')

    @image.command(aliases=['rs'], description='Resizes an image.', help='You may attach and link as many images as desired. Note that everything is validated, as such invalid (not) images are ignored.')
    async def resize(self, ctx, width: int, height: int, *urls: str):
        files = []
        for url in urls:
            if is_image_url(url):
                files.append(resize(requests.get(url).content, url.split('/')[-1], width, height))
        for file in ctx.message.attachments:
            if file.content_type.startswith('image'):
                files.append(resize(await file.read(), file.filename, width, height))
        if files == []:
            return await ctx.reply('No images?')
        try:
            await ctx.send(files=files)
        except discord.HTTPException:
            await ctx.reply('There\'s just no way that thing will fit!')

    @app_commands.command(name='embed', description='Generates an embed')
    @app_commands.default_permissions(manage_guild=True)
    async def embed(self, interaction: discord.Interaction):
        global title
        global description
        global color
        global footer
        global image
        global thumbnail
        global author
        global author_image
        global footer_image
        global fields
        global embed_preview

        title = None
        description = None
        color = 0xef5a93
        footer = None
        image = None
        thumbnail = None
        author = None
        author_image = None
        footer_image = None
        fields = None
        embed_preview = None

        await interaction.response.send_modal(customise_embed(True))

class customise_embed(ui.Modal, title = 'Customise Embed'):
    def __init__(self, initial = False):
        super().__init__()
        self.initial = initial

        global title
        global author
        global description
        global footer

        self.title_input = ui.TextInput(label = 'Title', style = discord.TextStyle.short, required = True, default=title)
        self.add_item(self.title_input)
        self.author_input = ui.TextInput(label = 'Author', style = discord.TextStyle.short, required = False, default=author)
        self.add_item(self.author_input)
        self.description_input = ui.TextInput(label = 'Description', style = discord.TextStyle.long, required = True, default=description)
        self.add_item(self.description_input)
        self.footer_input = ui.TextInput(label = 'Footer', style = discord.TextStyle.short, required = False, default=footer)
        self.add_item(self.footer_input)

    async def on_submit(self, interaction: discord.Interaction):
        global title
        global author
        global description
        global footer

        global embed_preview

        title = self.title_input.value
        author = self.author_input.value
        description = self.description_input.value
        footer = self.footer_input.value

        if self.initial:
            await interaction.response.send_message(embed=generate_embed(title, description, color, footer, image, thumbnail, author, author_image, footer_image, fields), view=EmbedConfigure(), ephemeral=True)
            embed_preview = await interaction.original_response()
        else:
            await embed_preview.edit(embed=generate_embed(title, description, color, footer, image, thumbnail, author, author_image, footer_image, fields))
            await interaction.response.send_message('Text successfully set', ephemeral=True)
            await asyncio.sleep(1)
            await interaction.delete_original_response()

class customise_embed_images(ui.Modal, title = 'Customise Embed'):
    def __init__(self):
        super().__init__()

        global thumbnail
        global image
        global author_image
        global footer_image
        
        global author
        global footer

        self.thumbnail_input = ui.TextInput(label = 'Thumbnail', style = discord.TextStyle.short, required = False, default=thumbnail)
        self.add_item(self.thumbnail_input)
        self.image_input = ui.TextInput(label = 'Image', style = discord.TextStyle.short, required = False, default=image)
        self.add_item(self.image_input)
        if author != '' and author is not None:
            self.author_image_input = ui.TextInput(label = 'Author Image', style = discord.TextStyle.short, required = False, default=author_image)
            self.add_item(self.author_image_input)
        if footer != '' and footer is not None:
            self.footer_image_input = ui.TextInput(label = 'Footer Image', style = discord.TextStyle.short, required = False, default=footer_image)
            self.add_item(self.footer_image_input)

    async def on_submit(self, interaction: discord.Interaction):
        global thumbnail
        global image
        global author_image
        global footer_image

        global embed_preview

        thumbnail = self.thumbnail_input.value
        image = self.image_input.value
        if author != '' and author is not None:
            author_image = self.author_image_input.value
        if footer != '' and footer is not None:
            footer_image = self.footer_image_input.value

        await embed_preview.edit(embed=generate_embed(title, description, color, footer, image, thumbnail, author, author_image, footer_image, fields))
        await interaction.response.send_message('Images successfully set', ephemeral=True)
        await asyncio.sleep(1)
        await interaction.delete_original_response()

class add_field(ui.Modal, title = 'Add Field'):
    def __init__(self, initial = False):
        super().__init__()
        self.initial = initial

    name_input = ui.TextInput(label = 'Name', style = discord.TextStyle.short, required = True)
    value_input = ui.TextInput(label = 'Content', style = discord.TextStyle.long, required = True)
    inline_input = ui.TextInput(label = 'Inline? (y/N)', style = discord.TextStyle.short, required = False)

    async def on_submit(self, interaction: discord.Interaction):
        if self.inline_input.value.lower() == 'y' or self.inline_input.value.lower() == 'yes':
            inline=True
        else:
            inline=False
        
        global fields
        global embed_preview
        global field_view
        global selected_field
        
        if self.initial:
            if fields is None:
                fields = []
            fields.append([self.name_input.value, self.value_input.value, inline])

            await embed_preview.edit(embed=generate_embed(title, description, color, footer, image, thumbnail, author, author_image, footer_image, fields))

            await interaction.response.send_message('Select prior to editing or deleting fields', view=EditFields(), ephemeral=True)
            field_view = await interaction.original_response()
        else:
            view = ui.View.from_message(field_view)
            view.children[1].disabled = True
            view.children[2].disabled = True
            try:
                view.children[3].add_option(label = self.name_input.value, value = self.name_input.value)
            except:
                return await interaction.response.send_message('There\'s an error idk (probably already exists)', ephemeral=True)
            if selected_field:
                view.children[3].options[selected_field].default = False
            await field_view.edit(view=view)

            await interaction.response.send_message('Field successfully added', ephemeral=True)
            await asyncio.sleep(1)
            await interaction.delete_original_response()
        
            if fields is None:
                fields = []
            fields.append([self.name_input.value, self.value_input.value, inline])

            await embed_preview.edit(embed=generate_embed(title, description, color, footer, image, thumbnail, author, author_image, footer_image, fields))

            selected_field = None

class edit_field(ui.Modal, title = 'Edit Field'):
    def __init__(self, field_index):
        super().__init__()
        self.field_index = field_index

        global fields
        if fields[field_index][2]:
            self.inline = 'y'
        else:
            self.inline = 'n'

        self.name_input = ui.TextInput(label = 'Name', style = discord.TextStyle.short, required = True, default=fields[self.field_index][0])
        self.add_item(self.name_input)
        self.value_input = ui.TextInput(label = 'Content', style = discord.TextStyle.long, required = True, default=fields[self.field_index][1])
        self.add_item(self.value_input)
        self.inline_input = ui.TextInput(label = 'Inline? (y/N)', style = discord.TextStyle.short, required = False, default=self.inline)
        self.add_item(self.inline_input)

    async def on_submit(self, interaction: discord.Interaction):
        if self.inline_input.value.lower() == 'y' or self.inline_input.value.lower() == 'yes':
            inline = True
        else:
            inline = False
        
        global fields

        original_label = fields[self.field_index][0]
        fields[self.field_index] = [self.name_input.value, self.value_input.value, inline]

        global embed_preview
        global field_view

        await embed_preview.edit(embed=generate_embed(title, description, color, footer, image, thumbnail, author, author_image, footer_image, fields))
        view = ui.View.from_message(field_view)
        view.children[1].disabled = True
        view.children[2].disabled = True
        for option in view.children[3].options:
            if option.label == original_label:
                option.label = fields[self.field_index][0]
                option.value = fields[self.field_index][0]
        view.children[3].options[self.field_index].default = False
        await field_view.edit(view=view)

        await interaction.response.send_message('Field successfully edited', ephemeral=True)
        await asyncio.sleep(1)
        await interaction.delete_original_response()
        global selected_field
        selected_field = None

class EmbedConfigure(ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(ColorSelect())
    
    @ui.button(label='Create Embed', style=discord.ButtonStyle.primary)
    async def create_embed(self, interaction: discord.Interaction, button: discord.ui.Button):
        global title
        global description
        global color
        global footer
        global image
        global thumbnail
        global author
        global author_image
        global footer_image
        global fields

        await interaction.response.send_message('Embed created', ephemeral=True)
        await asyncio.sleep(1)
        await interaction.delete_original_response()
        await interaction.channel.send(embed=generate_embed(title, description, color, footer, image, thumbnail, author, author_image, footer_image, fields))
    
    @ui.button(label='Edit Text', style=discord.ButtonStyle.secondary)
    async def text(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(customise_embed())
    
    @ui.button(label='Edit Images', style=discord.ButtonStyle.secondary)
    async def image(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(customise_embed_images())
    
    @ui.button(label='Add Field', style=discord.ButtonStyle.secondary)
    async def field(self, interaction: discord.Interaction, button: discord.ui.Button):
        global field_view
        await interaction.response.send_modal(add_field(True))
        self.remove_item(self.field)
        await interaction.edit_original_response(view = self)

class EditFields(ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(FieldList())

    @ui.button(label='Add Field', style=discord.ButtonStyle.secondary)
    async def add_field(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(add_field())

    @ui.button(label='Edit Field', style=discord.ButtonStyle.secondary, disabled=True)
    async def edit_field(self, interaction: discord.Interaction, button: discord.ui.Button):
        global selected_field
        if selected_field == None:
            await interaction.response.send_message('Please select a field to edit', ephemeral=True)
            await asyncio.sleep(1)
            return await interaction.delete_original_response()
        await interaction.response.send_modal(edit_field(selected_field))

    @ui.button(label='Remove Field', style=discord.ButtonStyle.secondary, disabled=True)
    async def remove_field(self, interaction: discord.Interaction, button: discord.ui.Button):
        print('idk how remove (yet (hopefully))')
        if fields == []:
            fields = None
            view = embed_preview.view.add_item(EmbedConfigure().field())
            embed_preview.edit(view=view)
            interaction.delete_original_response()

    # PROBLEM SEEMS TO BE THAT WHEN I EDIT THE VIEW THE BUTTONS STOP WORKING
            

class ColorSelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Red', value='0xeb4969'),
            discord.SelectOption(label='Orange', value='0xeb9a49'),
            discord.SelectOption(label='Yellow', value='0xfade7a'),
            discord.SelectOption(label='Green', value='0x9beba0'),
            discord.SelectOption(label='Blue', value='0xa7cdfa'),
            discord.SelectOption(label='Blurple', value='0x454fbf'),
            discord.SelectOption(label='Purple', value='0xd19cf0'),
            discord.SelectOption(label='Pink', value='0xef5a93', default=True),
            discord.SelectOption(label='White', value='0xffffff'),
            discord.SelectOption(label='Black', value='0x000000')
        ]
        super().__init__(placeholder='Choose the embed\'s color', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        global color
        color = int(self.values[0], 16)

        global embed_preview

        await embed_preview.edit(embed=generate_embed(title, description, color, footer, image, thumbnail, author, author_image, footer_image, fields))
        await interaction.response.send_message('Color successfully set', ephemeral=True)
        await asyncio.sleep(1)
        await interaction.delete_original_response()

class FieldList(ui.Select):
    def __init__(self):
        global fields
        super().__init__(
            placeholder='Select a field to edit or remove',
            min_values=1,
            max_values=1,
            options=[discord.SelectOption(label=field[0], value=field[0]) for field in fields]
        )

    async def callback(self, interaction: discord.Interaction):
        global fields
        global selected_field

        for i in range(len(fields)):
            if fields[i][0] == self.values[0]:
                selected_field = i

        global field_view

        self.view.children[1].disabled = False
        self.view.children[2].disabled = False
        self.view.children[3].options[selected_field].default = True
        await field_view.edit(view=self.view)

        await interaction.response.send_message('** **', ephemeral=True)
        await interaction.delete_original_response()

async def setup(bot):
    await bot.add_cog(Utility(bot), guild=discord.Object(id=752052271935914064))
