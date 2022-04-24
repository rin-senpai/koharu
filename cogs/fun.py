from discord.ext import commands
from owoify import owoify
import asyncio
import random

bad_words = ['frick', 'heck']

class Fun(commands.Cog, description='Commands that are fun. I know, it\'s a bit hard to guess what these categories are for.'):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.command(description='I echo the words of my *true* kouhai.', help='Append your request with `-h` or `--hide` in order to remove any traces of your actions.')
    @commands.is_owner()
    async def say(self, ctx, *, msg):
        if msg == '':
            return await ctx.reply('Oh nyuu.. wh-what do I say? Help me, pwetty please? Nyaaa…')
        for bad_word in bad_words:
            if bad_word in msg.lower():
                return await ctx.reply('Nyaoww~ that\'s an icky word! Hmpf, nyu don\'t know that I\'m a good little kitty-nya')
        reply = None
        if ctx.message.reference is not None:
            reply = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        if msg.startswith('-h ') or msg.startswith('--hide '):
            msg = msg.removeprefix('-h ')
            msg = msg.removeprefix('--hide ')
            await ctx.message.delete()
        if reply is not None:
            await reply.reply(msg)
        else:
            await ctx.send(msg)

    @commands.command(description='I echo the words of my *true* kouhai except owo.', help='Append your request with `-h` or `--hide` in order to remove any traces of your actions.')
    @commands.is_owner()
    async def owoify(self, ctx, *, msg):
        if msg == '':
            return await ctx.reply('Oh nyuu.. wh-what do I say? Help me, pwetty please? Nyaaa…')
        for bad_word in bad_words:
            if bad_word in msg.lower():
                return await ctx.reply('Nyaoww~ that\'s an icky word! Hmpf, nyu don\'t know that I\'m a good little kitty-nya')
        reply = None
        if ctx.message.reference is not None:
            reply = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        if msg.startswith('-h ') or msg.startswith('--hide '):
            msg = msg.removeprefix('-h ')
            msg = msg.removeprefix('--hide ')
            await ctx.message.delete()
        if msg.startswith('owo ') or msg.startswith('uwu ') or msg.startswith('uvu '):
            level = msg[0:3]
            msg = msg[4:]
            if reply is not None:
                await reply.reply(owoify(msg, level))
            else:
                await ctx.send(owoify(msg, level))
        else:
            if reply is not None:
                await reply.reply(owoify(msg))
            else:
                await ctx.send(owoify(msg))


    @commands.command(description='Play some Russian roulette and have a chance of getting yourself kicked from the server!', help='You have a 1/6 chance of getting the better option.')
    @commands.guild_only()
    async def roulette(self, ctx):
        msg = await ctx.send('**Spinning...**\nhttps://i.imgur.com/lPFgRP7.gif')
        await asyncio.sleep(3)
        if random.randint(1, 6) == 2:
            try:
                await ctx.guild.kick(ctx.author, reason='They were unlucky.')
            except Exception:
                return await ctx.reply('You seem to be too powerful\nhttps://tenor.com/view/fraz-bradford-meme-world-of-tanks-albania-gif-20568566')
            await msg.edit(content='Omae wa mou shindeiru~\nhttps://i.imgur.com/uTMawPi.gif')
        else:
            await msg.edit(content='Niice!\nhttps://i.imgur.com/KFvEtfj.gif')

    @commands.command(description='Feeling down? Go kick yourself.')
    @commands.guild_only()
    async def suicide(self, ctx):
        try:
            await ctx.guild.kick(ctx.author, reason='Ah what a beautiful way to go')
        except Exception:
            return await ctx.reply('You seem to be too powerful\nhttps://tenor.com/view/fraz-bradford-meme-world-of-tanks-albania-gif-20568566')
        await ctx.send('Sayo-nara\nhttps://tenor.com/view/gigachad-chad-gif-20773266')

async def setup(bot):
    await bot.add_cog(Fun(bot))
