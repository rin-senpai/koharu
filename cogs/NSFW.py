from discord.ext import commands
import random
import typing

from NHentai import NHentai
nhentai = NHentai()

class HentaiFlags(commands.FlagConverter):
    cursed: int = None

class NSFW(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.command(aliases=['sex'])
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
       
async def setup(bot):
    await bot.add_cog(NSFW(bot))
