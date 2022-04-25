import discord
from discord.ext import commands
import random
import typing

from NHentai import NHentai
nhentai = NHentai()

class HentaiFlags(commands.FlagConverter):
    cursed: int = None

class NSFW(commands.Cog, description='The cultured commands. Unfortunately they can\'t be used outside of cultured channels, but if you\'re the type of person who uses non-cultured channels, I don\'t think you deserve to be in a server with me.'):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.command(aliases=['sex'], description='Pure culture.', help='You can specify your own sauce by simply using it as an argument. \n\nYou can also specify the amount of cursed tags you want by using the argument `cursed: <number>`. Setting this to 0 removes all cursed tags. \n\nIf you don\'t specify a number, you will have a 50% chance to get 3 cursed tags, and a 50% chance to get 0.')
    @commands.is_nsfw()
    async def hentai(self, ctx, sauce: typing.Optional[int], *, flags: HentaiFlags):
        cursed_tags = ['bbm', 'bbw', 'netorare', 'rape', 'scat', 'dicknipples', 'eye penetration', 'farting', 'guro', 'inflation', 'cumflation', 'drugs', 'vore', 'vomit', 'smegma', 'snuff', 'blackmail', 'moral degeneration', 'mind break', 'torture', 'urethra insertion', 'cbt', 'breast expansion', 'prolapse', 'pregnant', 'urination', 'amputee', 'brain fuck', 'cannibalism', 'diaper', 'milking', 'bestiality']

        cursed: bool = None

        if flags.cursed is None:
            flags.cursed = 3
        elif flags.cursed < 1:
            cursed = False
        elif 15 > flags.cursed > 0:
            cursed = True
        elif flags.cursed > 15:
            cursed = True
            flags.cursed = 5
        
        if sauce is None:
            if cursed == False:
                await ctx.send(nhentai.get_random().url)
            elif cursed == True or random.randint(1, 10) > 5:
                while True:
                    search_terms = random.sample(cursed_tags, flags.cursed)
                    page = nhentai.search(query=' '.join(search_terms))
                    if page.doujins != []:
                        break
                doujin = random.choice(page.doujins)
                await ctx.send(doujin.url)
            else:
                await ctx.send(nhentai.get_random().url)
        else:
            if nhentai.get_doujin(id=sauce) is None:
                await ctx.reply('That doesn\'t seem to be valid sauce.')
            else:
                await ctx.send(nhentai.get_doujin(id=sauce).url)

    @commands.command(aliases=['ball', 'stretch', 'stretcher', 'reddit'], description='Section two. Ball stretcher.')
    @commands.is_nsfw()
    async def ballstretcher(self, ctx):
        await ctx.send('https://cdn.discordapp.com/attachments/752052271935914067/967798988222890035/unknown.png')

    @commands.command(description='xd')
    async def buttons(self, ctx):
        await ctx.send('owo', view=Buttons())

class Buttons(discord.ui.View):
    def __init__(self, *, timeout=180):
        super().__init__(timeout=timeout)
    @discord.ui.button(label="OwO", style=discord.ButtonStyle.primary, emoji='<a:gorospin:863670621732732938>')
    async def owo(self, interaction:discord.Interaction, button:discord.ui.Button):
        button.disabled=True
        await interaction.response.edit_message(content='<a:gorospin:863670621732732938>', view=self)
       
async def setup(bot):
    await bot.add_cog(NSFW(bot))
