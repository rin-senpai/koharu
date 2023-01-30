from discord import ui, app_commands
import discord
from discord.ext import commands
import requests
import asyncio
from .utils.image import resize, is_image_url

class Utility(commands.Cog, description='Only my *true* kouhai can use me, but I don\'t mind if others find utility in me. 👉 👈'):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='color', description='Sets your role color. Give the hex code of the color you want.')
    async def color(self, interaction: discord.Interaction, color: str = None, random: bool = False):
        if random:
            role_color = discord.Color.random()
        else:
            if color is None:
                role_color = discord.Color.default()
            else:
                if not color.startswith('#'):
                    color = '#' + color
                try:
                    role_color = discord.Color.from_str(color)
                except:
                    return await interaction.response.send_message('That doesn\'t seem to be a valid color.', ephemeral=True)
        role = discord.utils.get(interaction.guild.roles, name=f'{interaction.user.id}')
        if role is None:
            role = await interaction.guild.create_role(name=f'{interaction.user.id}', color=role_color)
            await interaction.user.add_roles(role)
            if color is None:
                return await interaction.response.send_message('Your role has been created.', ephemeral=True)
            else:
                return await interaction.response.send_message(f'Your role has been created and updated to {str(role_color)}.', ephemeral=True)
        await role.edit(colour=role_color)
        if role not in interaction.user.roles:
            await interaction.user.add_roles(role)
        if color is None and random is False:
            return await interaction.response.send_message('Your role has been reset.', ephemeral=True)
        else:
            return await interaction.response.send_message(f'Your role has been updated to {str(role_color)}.', ephemeral=True)

    @color.error
    async def color_error(self, ctx, error):
        if isinstance(error, commands.BadColourArgument):
            await ctx.reply('That doesn\'t seem to be a valid color.')

    @app_commands.command(name='avatar', description='Sends the profile picture of the specified user.')
    async def avatar(self, interaction: discord.Interaction, member: discord.Member = None):
        if member is None:
            member = interaction.user
        embed = discord.Embed(title=f'{member.name}\'s Avatar', url=member.avatar.url)
        embed.set_image(url=member.avatar.url)
        await interaction.response.send_message(embed=embed)

    image = app_commands.Group(name='image', description='Manupulates images')

    @image.command(name='resize', description='Resizes an image.')
    async def resize(self, interaction: discord.Interaction, width: int, height: int, image: discord.Attachment = None, image_url: str = ''):
        files = []
        if is_image_url(image_url):
            files.append(resize(requests.get(image_url).content, image_url.split('/')[-1], width, height))
        if image is not None:
            if image.content_type.startswith('image'):
                files.append(resize(await image.read(), image.filename, width, height))
        if files == []:
            return await interaction.response.send_message('No images?', ephemeral=True)
        try:
            await interaction.response.send_message(files=files)
        except discord.HTTPException:
            await interaction.response.send_message('There\'s just no way that thing will fit!', ephemeral=True)

    @app_commands.command(name='embed', description='Generates an embed')
    @app_commands.default_permissions(manage_guild=True)
    async def embed(self, interaction: discord.Interaction):
        view = InteractiveEmbedBuilder()
        await interaction.response.send_message(view=view, embed=view.embed, ephemeral=True)

class InteractiveEmbedBuilder(ui.View):
    def __init__(self):
        super().__init__()
        self.embed = discord.Embed(description='草', color=0xef5a93)
        self.add_item(ColorSelect(self))

    @ui.button(label='Create Embed', style=discord.ButtonStyle.primary, row = 0)
    async def create_embed(self, interaction: discord.Interaction, button: discord.ui.Button):
        await asyncio.sleep(1)
        await interaction.delete_original_response()
        await interaction.channel.send(embed=self.embed)
        await interaction.response.send_message('Embed created', ephemeral=True)
    
    @ui.button(label='Edit Text', style=discord.ButtonStyle.secondary, row = 0)
    async def text(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CustomiseEmbedText(self)
        await interaction.response.send_modal(modal)
    
    @ui.button(label='Edit Images', style=discord.ButtonStyle.secondary, row = 0)
    async def image(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CustomiseEmbedImages(self)
        await interaction.response.send_modal(modal)
    
    @ui.button(label='Add Field', style=discord.ButtonStyle.secondary, row = 0)
    async def add_field(self, interaction: discord.Interaction, button: discord.ui.Button):
        if len(self.embed.fields) == 25:
            return await interaction.response.send_message('You can\'t have more than 25 fields in an embed', ephemeral=True)
        modal = AddField(self)
        await interaction.response.send_modal(modal)

class ColorSelect(ui.Select):
    def __init__(self, parent):
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
        super().__init__(placeholder='Choose the embed\'s color', min_values=1, max_values=1, options=options, row=1)
        self.parent = parent

    async def callback(self, interaction: discord.Interaction):
        embed = self.parent.embed

        color = int(self.values[0], 16)
        embed.color = color
        self.parent.embed = embed

        await interaction.response.edit_message(view=self.parent, embed=embed)

class FieldSelect(ui.Select):
    def __init__(self, parent):
        options = []
        for i, field in enumerate(parent.embed.fields):
            options.append(discord.SelectOption(label=field.name, value=str(i)))
        super().__init__(placeholder='Choose a field', min_values=1, max_values=1, options=options, row=2)
        self.parent = parent
    
    async def callback(self, interaction: discord.Interaction):
        modal = EditField(self.parent, int(self.values[0]))
        await interaction.response.send_modal(modal)

class CustomiseEmbedText(ui.Modal, title = 'Customise Embed'):
    def __init__(self, parent: InteractiveEmbedBuilder):
        super().__init__()
        self.parent = parent

        self.title_input = ui.TextInput(label = 'Title', style = discord.TextStyle.short, required = True, default=self.parent.embed.title)
        self.add_item(self.title_input)
        self.author_input = ui.TextInput(label = 'Author', style = discord.TextStyle.short, required = False, default=self.parent.embed.author.name)
        self.add_item(self.author_input)
        self.description_input = ui.TextInput(label = 'Description', style = discord.TextStyle.long, required = True, default=(None if self.parent.embed.description == '草' else self.parent.embed.description))
        self.add_item(self.description_input)
        self.footer_input = ui.TextInput(label = 'Footer', style = discord.TextStyle.short, required = False, default=self.parent.embed.footer.text)
        self.add_item(self.footer_input)

    async def on_submit(self, interaction: discord.Interaction):
        embed = self.parent.embed
        embed.title = self.title_input.value
        embed.set_author(name = self.author_input.value, icon_url=embed.author.icon_url)
        embed.description = self.description_input.value
        embed.set_footer(text = self.footer_input.value, icon_url=embed.footer.icon_url)
        self.parent.embed=embed

        await interaction.response.edit_message(view=self.parent, embed=embed)

class CustomiseEmbedImages(ui.Modal, title = 'Customise Embed'):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        self.thumbnail_input = ui.TextInput(label = 'Thumbnail', style = discord.TextStyle.short, required = False, default=self.parent.embed.thumbnail)
        self.add_item(self.thumbnail_input)
        self.image_input = ui.TextInput(label = 'Image', style = discord.TextStyle.short, required = False, default=self.parent.embed.image)
        self.add_item(self.image_input)
        if self.parent.embed.author.name != '' and self.parent.embed.author.name is not None:
            self.author_image_input = ui.TextInput(label = 'Author Image', style = discord.TextStyle.short, required = False, default=self.parent.embed.author.icon_url)
            self.add_item(self.author_image_input)
        if self.parent.embed.footer.text != '' and self.parent.embed.footer.text is not None:
            self.footer_image_input = ui.TextInput(label = 'Footer Image', style = discord.TextStyle.short, required = False, default=self.parent.embed.footer.icon_url)
            self.add_item(self.footer_image_input)

    async def on_submit(self, interaction: discord.Interaction):
        embed = self.parent.embed
        embed.set_thumbnail(url=self.thumbnail_input.value)
        embed.set_image(url=self.image_input.value)
        if self.parent.embed.author.name != '' and self.parent.embed.author.name is not None:
            embed.set_author(name=self.parent.embed.author.name, icon_url=self.author_image_input.value)
        if self.parent.embed.footer.name != '' and self.parent.embed.footer.text is not None:
            embed.set_footer(text=self.parent.embed.footer.text, icon_url=self.footer_image_input.value)
        self.parent.embed=embed
        
        await interaction.response.edit_message(view=self.parent, embed=embed)

class AddField(ui.Modal, title = 'Add Field'):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

    name_input = ui.TextInput(label = 'Name', style = discord.TextStyle.short, required = True)
    value_input = ui.TextInput(label = 'Content', style = discord.TextStyle.long, required = True)
    inline_input = ui.TextInput(label = 'Inline? (y/N)', style = discord.TextStyle.short, required = False)

    async def on_submit(self, interaction: discord.Interaction):
        if self.inline_input.value.lower() == 'y' or self.inline_input.value.lower() == 'yes':
            inline=True
        else:
            inline=False
        
        embed = self.parent.embed
        embed.add_field(
            name=self.name_input.value,
            value=self.value_input.value,
            inline=inline
        )
        self.parent.embed = embed
        if len(embed.fields) == 1:
            self.parent.add_item(FieldSelect(self.parent))
        else:
            self.parent.children[5].add_option(label=self.name_input.value, value=str(len(embed.fields)-1))
        
        await interaction.response.edit_message(view=self.parent, embed=embed)

class EditField(ui.Modal, title = 'Edit Field'):
    def __init__(self, parent, field_index):
        super().__init__()
        self.parent = parent
        self.field_index = field_index

        self.name_input = ui.TextInput(label = 'Name', style = discord.TextStyle.short, required = True, default=self.parent.embed.fields[self.field_index].name)
        self.add_item(self.name_input)
        self.value_input = ui.TextInput(label = 'Content', style = discord.TextStyle.long, required = True, default=self.parent.embed.fields[self.field_index].value)
        self.add_item(self.value_input)
        self.inline_input = ui.TextInput(label = 'Inline? (y/N)', style = discord.TextStyle.short, required = False, default=self.parent.embed.fields[self.field_index].inline)
        self.add_item(self.inline_input)
        self.delete_input = ui.TextInput(label = 'Delete? (y/N)', style = discord.TextStyle.short, required = False)
        self.add_item(self.delete_input)

    async def on_submit(self, interaction: discord.Interaction):
        if self.inline_input.value.lower() == 'y' or self.inline_input.value.lower() == 'yes':
            inline=True
        else:
            inline=False
        
        embed = self.parent.embed

        if self.delete_input.value.lower() == 'y' or self.delete_input.value.lower() == 'yes':
            embed.remove_field(self.field_index)
            self.parent.children[5].options.pop(self.field_index)
            self.parent.remove_item(self.parent.children[5])
        else:
            embed.set_field_at(
                index=self.field_index,
                name=self.name_input.value,
                value=self.value_input.value,
                inline=inline
            )
        self.parent.embed = embed
        
        await interaction.response.edit_message(view=self.parent, embed=embed)

async def setup(bot):
    await bot.add_cog(Utility(bot), guilds=[discord.Object(id=752052271935914064), discord.Object(id=722386163356270662)])
