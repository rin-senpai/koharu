from discord.ext import commands

class Moderation(commands.Cog, description='That\'s right, I can do moderation too! <:hutao_x:815118311582597161>'):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.group(description='Purges various things.')
    async def purge (self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.reply('Purge what?? Give me something valid.')

    @purge.command(aliases=['message'], description='Purge a number of messages from the channel.', help='If desired, you may express the amount of messages to be deleted. This defaults to 100.')
    @commands.has_permissions(manage_messages=True)
    async def messages (self, ctx, amount: int = 100):
        await ctx.channel.purge(limit=amount)
        await ctx.send(f'Purged {amount} messages.')

    @purge.command(aliases=['colours', 'color', 'colour'], description='Purges all unused color roles.')
    @commands.has_permissions(manage_roles=True)
    async def colors(self, ctx):
        for role in ctx.guild.roles:
            if len(role.name) == 18 and role.name.isnumeric() and role.members == []:
                await role.delete()

        await ctx.send('Unused color roles have successfully been purged.')

async def setup(bot):
    await bot.add_cog(Moderation(bot))
