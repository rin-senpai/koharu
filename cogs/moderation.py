import discord
from discord.ext import commands
import datetime

class Moderation(commands.Cog, description='That\'s right, I can do moderation too! <:hutao_x:815118311582597161>'):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.command(aliases=['kicc'], description='Kicks a user from the server.', help='Specify the user by mentioning them. You may provide a reason following this if desired. The user will be notified by DM, so don\'t think they won\'t know it was you.')
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = None):
        direct_embed = discord.Embed(
            title=f'You have been kicked from {ctx.guild.name}',
            description=f'{"**Reason:** `" + reason + "`" if reason is not None else "No reason was provided."}',
            color=0xef5a93
        )
        direct_embed.set_author(name=f'{ctx.author.name}#{ctx.author.discriminator}', icon_url=ctx.author.avatar.url)
        direct_embed.timestamp = datetime.datetime.utcnow()

        guild_embed = discord.Embed(
            title=f'{member.name}#{member.discriminator} has been kicked',
            description=f'{"**Reason:** `" + reason + "`" if reason is not None else "No reason was provided."}',
            color=0xef5a93
        )
        guild_embed.set_author(name=f'{ctx.author.name}#{ctx.author.discriminator}',icon_url=ctx.author.avatar.url)
        guild_embed.timestamp = datetime.datetime.utcnow()

        if reason is None:
            reason = f'Action done by {ctx.author} (ID: {ctx.author.id})'

        if member.top_role >= ctx.guild.me.top_role or member == ctx.guild.owner:
            return await ctx.reply(f'If I wish to defeat {member.name}, I must train for another 500 years.')
        
        if member.top_role >= ctx.author.top_role:
            return await ctx.reply(f'If you wish to defeat {member.name}, train for another 500 years.')

        await member.send(embed=direct_embed)
        await member.kick(reason=reason)
        await ctx.send(embed=guild_embed)

    @commands.command(aliases=['hammer'], description='Bans a user from the server.')
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason = None):
        if reason is None:
            reason = f'Action done by {ctx.author} (ID: {ctx.author.id})'

        await ctx.guild.ban(member, reason=reason)
        await ctx.send('xd')

    @commands.group(description='Purges various things.')
    async def purge(self, ctx):
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

    @commands.group(description='Manages the bot\'s prefix.')
    async def prefix (self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.reply('Where valid subcommand. (I should probably make these also do senpai nani group command in the future)')

    @prefix.command(aliases=['current'], description='Shows the current prefix.')
    async def view(self, ctx):
        await ctx.send(f'The current prefix of this server is `{(await self.bot.get_prefix(ctx.message))[-1]}`.')

    @prefix.command(aliases=['create', 'add'], description='Changes the bot\'s prefix.', help='Enclose your specified prefix with `backticks` to allow subsequent spaces and more.')
    @commands.has_permissions(manage_guild=True)
    async def set(self, ctx, *, prefix: str):
        if prefix.startswith('`') and prefix.endswith('`'):
            prefix = prefix[1:-1]
        await ctx.bot.db.execute(f'UPDATE guilds SET prefix = $1 WHERE guild_id = $2', prefix, ctx.guild.id)
        await ctx.send(f'The prefix has been set to `{prefix}`.')

    @prefix.command(aliases=['default'], description='Resets the bot\'s prefix to the default.')
    @commands.has_permissions(manage_guild=True)
    async def reset(self, ctx):
        await ctx.bot.db.execute(f'UPDATE guilds SET prefix = $1 WHERE guild_id = $2', 'senpai ', ctx.guild.id)
        await ctx.send('The prefix has been set to `senpai `.')

async def setup(bot):
    await bot.add_cog(Moderation(bot))