from discord import app_commands, Interaction

async def owner_only(interaction: Interaction):
    return await interaction.client.is_owner(interaction.user)