import discord
from discord import app_commands
from discord.ext import commands
import math
import random

class NSFW(commands.Cog, description='The cultured commands. Unfortunately they can\'t be used outside of cultured channels, but if you\'re the type of person who uses non-cultured channels, I don\'t think you deserve to be in a server with me.'):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='hentai', description='Pure culture.', nsfw=True)
    async def hentai(self, interaction: discord.Interaction, sauce: str = '', cursed: bool = False):
        try:
            intSauce = int(sauce)
            if intSauce < 1 or intSauce > 999999:
                return await interaction.response.send_message('That doesn\'t seem to be valid sauce.', ephemeral=True)

        except:
            return await interaction.response.send_message('That doesn\'t seem to be valid sauce.', ephemeral=True)

        newest = 430423
        cursedSauce = ['278832', '210510', '77054', '177013', '255918', '114750', '139732', '222855', '261174', '201704', '4280', '215600', '228922', '152889', '269253', '268289', '239103', '123442', '75715', '105369', '267924', '252067', '222855', '189774', '87639', '286919', '180027', '212084', '278832', '210510', '77054', '114750', '139732', '222855', '261174', '201704', '4280', '200948', '219153']

        if sauce != '':
            return await interaction.response.send_message('https://nhentai.net/g/' + sauce)
        if cursed:
            return await interaction.response.send_message('https://nhentai.net/g/' + cursedSauce[random.randint(0, len(cursedSauce) - 1)])
        else:
            if random.random() > 0.6:
                return await interaction.response.send_message('https://nhentai.net/g/' + cursedSauce[random.randint(0, len(cursedSauce) - 1)])
            else:
                return await interaction.response.send_message('https://nhentai.net/g/' + str(math.floor(random.random() * newest) + 1))


    @app_commands.command(name='ballstretcher', description='Section two: ball stretcher', nsfw=True)
    async def ballstretcher(self, interaction: discord.Interaction):
        await interaction.response.send_message('https://cdn.discordapp.com/attachments/752052271935914067/967798988222890035/unknown.png')
       
async def setup(bot):
    await bot.add_cog(NSFW(bot), guilds=[discord.Object(id=752052271935914064), discord.Object(id=722386163356270662)])
