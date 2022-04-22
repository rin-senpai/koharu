from discord.ext import commands

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.group()
    async def purge (self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Purge what?? Give me something valid.')

    @purge.command(aliases=['message'])
    @commands.has_permissions(manage_messages=True)
    async def messages (self, ctx, amount: int):
        await ctx.channel.purge(limit=amount)
        await ctx.send(f'Purged {amount} messages.')

    @purge.command(aliases=['colours', 'color', 'colour'])
    @commands.has_permissions(manage_roles=True)
    async def colors(self, ctx):
        for role in ctx.guild.roles:
            if len(role.name) == 18 and role.name.isnumeric() and role.members == []:
                await role.delete()

        await ctx.send('Unused color roles have successfully been purged.')

async def setup(bot):
    await bot.add_cog(Moderation(bot))
