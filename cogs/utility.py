from discord import ui, app_commands
import discord
from discord.ext import commands
import requests
from .utils.image import resize, is_image_url
from .utils.embeds import generate_embed

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
        await interaction.response.send_modal(customise_embed1())

class customise_embed1(ui.Modal, title = 'Customise Embed'):
    def __init__(self):
        super().__init__()

    title = ui.TextInput(label = 'Title', style = discord.TextStyle.short, required = True)
    author = ui.TextInput(label = 'Author', style = discord.TextStyle.short, required = False)
    description = ui.TextInput(label = 'Description', style = discord.TextStyle.long, required = True)
    footer = ui.TextInput(label = 'Footer', style = discord.TextStyle.short, required = False)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_modal(customise_embed2(self.title, self.author, self.description, self.footer))

class customise_embed2(ui.Modal, title = 'Customise Embed'):
    def __init__(self, title, author, description, footer):
        super().__init__()
        self.title = title
        self.author = author
        self.description = description
        self.footer = footer

    color = ui.TextInput(label = 'Color', style = discord.TextStyle.short, required = False)
    image = ui.TextInput(label = 'Image', style = discord.TextStyle.short, required = False)
    thumbnail = ui.TextInput(label = 'Thumbnail', style = discord.TextStyle.short, required = False)

    async def on_submit(self, interaction: discord.Interaction):
        interaction.response.send_message('Nyaoww~ I\'m a good little kitty-nya', ephemeral=True)
        interaction.channel.send(embed=generate_embed(self.title.value, self.description.value, self.color.value, self.footer.value, self.image.value, self.thumbnail.value, self.author.value))

async def setup(bot):
    await bot.add_cog(Utility(bot), guild=discord.Object(id=752052271935914064))
