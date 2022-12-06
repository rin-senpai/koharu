from discord.app_commands import CommandTree
from discord import Interaction

class Tree(CommandTree):
    async def interaction_check(self, interaction: Interaction) -> bool:
        return True
