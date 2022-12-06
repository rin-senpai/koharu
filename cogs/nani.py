import discord
from discord import ui
from discord import app_commands
from discord.ext import commands, menus
from discord.ext.commands import HelpCommand

class NaniCommand(HelpCommand):
    def __init__(self):
        super().__init__()
        self.command_attrs = {
            'name': 'nani',
            'aliases': ['help']
        }

    async def send_bot_help(self, mapping):
        owner = self.context.bot.get_user(self.context.bot.owner_id)
        
        del mapping[self.cog]
        del mapping[None]

        all_embed = discord.Embed(
            title='All Commands',
            description=('Note that only commands available to you are shown. '
            'To cycle through categories, press the arrow buttons at the bottom of this message.\n\n'
            'To view details on specific categories, groups, or commands, use `senpai nani <category/group/command>`. '
            'This is case-sensitive (categories are as displayed, and groups and commands are lowercase).\n\n'
            'If you have any queries or issues related to me, please contact my kouhai [here](https://ko-fi.com/voxeldev).'),
            color=0xef5a93
        )

        for cog in mapping:
            commands = await self.filter_commands(cog.get_commands(), sort=True)
            if len(commands) == 0:
                continue
            commands_list = '```'
            for command in commands:
                commands_list += f'{command.name.capitalize()}, '
            commands_list = commands_list[:-2] + '```'
            all_embed.add_field(name=cog.qualified_name, value=commands_list, inline=True)
            all_embed.set_footer(text=f'Developed by {owner.name}#{owner.discriminator}', icon_url=owner.avatar.url)
        all_embed.add_field(name='Links', value='[Invite me to your server](https://discord.com/oauth2/authorize?client_id=785120734116577280&permissions=8&scope=bot)\n[Invest in Rin\'s various funds](https://ko-fi.com/voxeldev)', inline=False)

        formatter = NaniPageSource(list(mapping), self, owner)
        menu = NaniPages(formatter, all_embed)
        return await menu.start(self.context)

    async def send_cog_help(self, cog):
        commands = await self.filter_commands(cog.get_commands(), sort=True)
        embed = discord.Embed(
            title=f'{cog.qualified_name}',
            description=f'{cog.description}',
            color=0xef5a93
        )
        for command in commands:
            embed.add_field(name=command.name.capitalize(), value=command.description, inline=False)
        return await self.get_destination().send(embed=embed)

    async def send_group_help(self, group):
        embed = discord.Embed(
            title = f'{group.cog.qualified_name} - {group.name.capitalize()}',
            description = f'{group.description}\n\n**Usage:** {self.get_command_signature(group)} <subcommand>',
            color = 0xef5a93
        )
        for i, command in enumerate(group.commands):
            embed.add_field(name=f'{command.name.capitalize()}', value=command.description, inline=False)
        return await self.get_destination().send(embed=embed)

    async def send_command_help(self, command):
        if command.parent is not None:
            name = f'{command.parent.name.capitalize()} {command.name.capitalize()}'
        else:
            name = command.name.capitalize()

        if command.help is not None:
            help = command.help + '\n\n'
        else:
            help = ''
        
        embed = discord.Embed(
            title=f'{command.cog.qualified_name} - {name}',
            description=f'{command.description}\n\n{help}**Usage:** {self.get_command_signature(command)}',
            color=0xef5a93
        )
        return await self.get_destination().send(embed=embed)

    async def send_error_message(self, error):
        await self.context.reply(error)

class NaniPageSource(menus.ListPageSource):
    def __init__(self, data, nanicommand, owner):
        super().__init__(data, per_page=1)
        self.nanicommand = nanicommand
        self.owner = owner
        
    async def format_page(self, menu, entries):
        # commands = await NaniCommand.filter_commands(entries.get_commands(), sort=True)
        # page = menu.current_page
        # max_page = self.get_max_pages()
        # starting_number = page * self.per_page + 1
        embed = discord.Embed(
            title=f'{entries.qualified_name}',
            description=f'{entries.description}',
            color=0xef5a93
        )
        embed.set_footer(text=f'Developed by {self.owner.name}#{self.owner.discriminator}', icon_url=self.owner.avatar.url)
        for command in entries.get_commands():
            embed.add_field(name=command.name.capitalize(), value=command.description, inline=False)
        return embed

class NaniPages(ui.View, menus.MenuPages):
    def __init__(self, source, all_embed, *, delete_message_after=False):
        super().__init__(timeout=60)
        self._source = source
        self.current_page = 0
        self.ctx = None
        self.message = None
        self.delete_message_after = delete_message_after
        self.all_embed = all_embed

    async def start(self, ctx):
        await self._source._prepare_once()
        self.ctx = ctx
        self.message = await self.send_initial_message(ctx, ctx.channel)

    async def on_timeout(self) -> None:
        for button in self.children:
            button.disabled = True
        await self.message.edit(view=self)

    async def show_checked_page(self, page_number: int) -> None:
        max_pages = self._source.get_max_pages()
        try:
            if max_pages is None:
                await self.show_page(page_number)
            elif page_number >= max_pages:
                await self.show_page(0)
            elif page_number < 0:
                await self.show_page(max_pages - 1)
            elif max_pages > page_number >= 0:
                await self.show_page(page_number)
        except IndexError:
            pass

    async def _get_kwargs_from_page(self, page):
        value = await super()._get_kwargs_from_page(page)
        if 'view' not in value:
            value.update({'view': self})
        return value
    
    async def interaction_check(self, interaction):
        return interaction.user == self.ctx.author

    @ui.button(emoji='<:previous:967665422633689138>', style=discord.ButtonStyle.primary)
    async def previous_page(self, interaction, button):
        await self.show_checked_page(self.current_page - 1)

    @ui.button(label='All', style=discord.ButtonStyle.secondary)
    async def all_page(self, interaction, button):
        await interaction.response.edit_message(embed=self.all_embed)

    @ui.button(emoji='<:next:967665404589801512>', style=discord.ButtonStyle.primary)
    async def next_page(self, interaction, button):
        await self.show_checked_page(self.current_page + 1)

class Nani(commands.Cog):
    def __init__(self, bot):
        self._original_help_command = bot.help_command
        bot.help_command = NaniCommand()
        bot.help_command.cog = self
        
    def cog_unload(self):
        self.bot.help_command = self._original_help_command

async def setup(bot):
    await bot.add_cog(Nani(bot), guild=discord.Object(id=752052271935914064))
