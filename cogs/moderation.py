from discord import ui, app_commands
import discord
from discord.ext import commands
import datetime

class Moderation(commands.Cog, description='That\'s right, I can do moderation too! <:hutao_x:815118311582597161>'):
    def __init__(self, bot):
        self.bot = bot
        self.kick_ctx_menu = app_commands.ContextMenu(
            name='Kick',
            callback=self.kick_menu
        )
        self.ban_ctx_menu = app_commands.ContextMenu(
            name='Ban',
            callback=self.ban_menu
        )
        self.bot.tree.add_command(self.kick_ctx_menu)
        self.bot.tree.add_command(self.ban_ctx_menu)

    @app_commands.command(name='kick', description='Kicks a user from the server') # help='Specify the user by mentioning them. You may provide a reason following this if desired. The user will be notified by DM, so don\'t think they won\'t know it was you.'
    @app_commands.guild_only()
    @app_commands.default_permissions(kick_members=True)
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        if reason is None:
            reason = f'Action done by {interaction.user} (ID: {interaction.user.id})'

        if member.top_role >= interaction.guild.me.top_role or member == interaction.guild.owner:
            return await interaction.response.send_message(f'If I wish to defeat {member.name}, I must train for another 500 years.', ephemeral=True)
        
        if member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message(f'If you wish to defeat {member.name}, train for another 500 years.', ephemeral=True)

        await member.send(embed=direct_kickban_embed(interaction.user, interaction.guild, reason, 'kick'))
        await member.kick(reason=reason)
        await interaction.response.send_message(embed=guild_kickban_embed(interaction.user, member, reason, 'kick'))

    @app_commands.default_permissions(kick_members=True)
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick_menu(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.send_modal(kickban_modal(member=member, action='kick'))

    @commands.command(name='ban', description='Bans a user from the server')
    @app_commands.guild_only()
    @app_commands.default_permissions(ban_members=True)
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        if reason is None:
            reason = f'Action done by {interaction.user} (ID: {interaction.user.id})'

        if member.top_role >= interaction.guild.me.top_role or member == interaction.guild.owner:
            return await interaction.response.send_message(f'If I wish to defeat {member.name}, I must train for another 500 years.', ephemeral=True)
        
        if member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message(f'If you wish to defeat {member.name}, train for another 500 years.', ephemeral=True)

        await member.send(embed=direct_kickban_embed(interaction.user, interaction.guild, reason, 'ban'))
        await interaction.guild.ban(member, reason=reason)
        await interaction.response.send_message(embed=guild_kickban_embed(interaction.user, member, reason, 'ban'))

    @app_commands.default_permissions(ban_members=True)
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban_menu(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.send_modal(kickban_modal(member=member, action='ban'))

    purge = app_commands.Group(name='purge', description='Purges various things', guild_only=True, default_permissions=discord.Permissions(manage_messages=True, manage_roles=True))

    @purge.command(name='messages', description='Purge a number of messages from the channel')
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge_messages(self, interaction: discord.Interaction, amount: int, ephemeral: bool = False):
        await interaction.response.defer(ephemeral=True)
        await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f'Purged {amount} {"message" if amount == 1 else "messages"} from this channel', ephemeral=ephemeral)

    @purge.command(name='colors', description='Purges all unused color roles')
    @app_commands.default_permissions(manage_roles=True)
    @app_commands.checks.has_permissions(manage_roles=True)
    async def purge_colors(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        num_purged = 0
        for role in interaction.guild.roles:
            if len(role.name) == 18 and role.name.isnumeric() and role.members == []:
                await role.delete()
                num_purged += 1
        if num_purged == 0:
            await interaction.followup.send('No unused color roles found', ephemeral=True)
        else:
            await interaction.followup.send(f'{num_purged} unused color {"role has" if num_purged == 1 else "roles have"} successfully been purged')

    @commands.group(description='idkstuff')
    async def welcome(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.reply('Where valid subcommand. (I should probably make these also do senpai nani group command in the future)')

    # Embed welcome?

    @commands.Cog.listener()
    async def on_member_join(self, member):
        role = discord.utils.get(member.guild.roles, name=f'{member.id}')
        if role is None:
            role = await member.guild.create_role(name=f'{member.id}', color=0)
            await member.add_roles(role)
        else:
            await member.add_roles(role)

        channel = await self.bot.db.fetch('SELECT broadcast_channel FROM guilds WHERE guild_id = $1', member.guild.id)
        channel = channel[0].get('broadcast_channel')
        if channel is not None:
            message = await self.bot.db.fetch('SELECT welcome_msg FROM guilds WHERE guild_id = $1', member.guild.id)
            message = message[0].get('welcome_msg')
            if message is not None:
                message = message.replace('$member', member.mention)
                await self.bot.get_channel(channel).send(message)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel = await self.bot.db.fetch('SELECT broadcast_channel FROM guilds WHERE guild_id = $1', member.guild.id)
        channel = channel[0].get('broadcast_channel')
        if channel is not None:
            message = await self.bot.db.fetch('SELECT leave_msg FROM guilds WHERE guild_id = $1', member.guild.id)
            message = message[0].get('leave_msg')
            if message is not None:
                message = message.replace('$member', member.mention)
                await self.bot.get_channel(channel).send(message)

class kickban_modal(ui.Modal, title = 'w h y'):
    def __init__(self, member, action):
        super().__init__()
        self.member = member
        self.action = action

    reason = ui.TextInput(label = 'Reason', style = discord.TextStyle.long, required = False)

    async def on_submit(self, interaction: discord.Interaction):
        if self.reason.value is None or self.reason.value == '':
                self.reason.value = f'Action done by {interaction.user} (ID: {interaction.user.id})'

        if self.member.top_role >= interaction.guild.me.top_role or self.member == interaction.guild.owner:
            return await interaction.response.send_message(f'If I wish to defeat {self.member.name}, I must train for another 500 years.', ephemeral=True)
        
        if self.member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message(f'If you wish to defeat {self.member.name}, train for another 500 years.', ephemeral=True)
        
        if self.action == 'kick':
            await self.member.send(embed=direct_kickban_embed(interaction.user, interaction.guild, self.reason.value, 'kick'))
            await self.member.kick(reason=self.reason.value)
            await interaction.response.send_message(embed=guild_kickban_embed(interaction.user, self.member, self.reason.value, 'kick'))
        elif self.action == 'ban':
            await self.member.send(embed=direct_kickban_embed(interaction.user, interaction.guild, self.reason.value, 'ban'))
            await interaction.guild.ban(self.member, reason=self.reason.value)
            await interaction.response.send_message(embed=guild_kickban_embed(interaction.user, self.member, self.reason.value, 'ban'))
        else:
            print('You screwed up kickban_modal.')

def direct_kickban_embed(user, guild, reason, type):
    direct_embed = discord.Embed(
            title=f'You have been {"kicked" if type == "kick" else "banned"} from {guild.name}',
            description=f'{"**Reason:** `" + reason + "`" if reason is not None else "No reason was provided."}',
            color=0xef5a93
        )
    direct_embed.set_author(name=f'{user.name}#{user.discriminator}', icon_url=user.avatar.url)
    direct_embed.timestamp = datetime.datetime.utcnow()
    
    return direct_embed

def guild_kickban_embed(user, member, reason, type):
    guild_embed = discord.Embed(
        title=f'{member.name}#{member.discriminator} has been {"kicked" if type == "kick" else "banned"}',
        description=f'{"**Reason:** `" + reason + "`" if reason is not None else "No reason was provided."}',
        color=0xef5a93
    )
    guild_embed.set_author(name=f'{user.name}#{user.discriminator}',icon_url=user.avatar.url)
    guild_embed.timestamp = datetime.datetime.utcnow()
    
    return guild_embed

async def setup(bot):
    await bot.add_cog(Moderation(bot), guild=discord.Object(id=752052271935914064))
