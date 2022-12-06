import discord

def generate_embed(title, description, color = 0xef5a93, footer = None, image = None, thumbnail = None, author = None, fields = None):
    embed = discord.Embed(title=title, description=description, color=color)
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    if image:
        embed.set_image(url=image)
    if footer:
        embed.set_footer(text=footer)
    if author:
        embed.set_author(name=author)
    if fields:
        for field in fields:
            embed.add_field(name=field[0], value=field[1], inline=field[2])
    return embed