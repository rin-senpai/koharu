import discord
import validators

def generate_embed(title, description, color = 0xef5a93, footer = None, image = None, thumbnail = None, author = None, author_image = None, footer_image = None, fields = None):
    embed = discord.Embed(title=title, description=description, color=color)
    if thumbnail:
        if validators.url(thumbnail):
            embed.set_thumbnail(url=thumbnail)
    if image:
        if validators.url(image):
            embed.set_image(url=image)
    if footer:
        if footer_image:
            if validators.url(footer_image):
                embed.set_footer(text=footer, icon_url=footer_image)
            else:
                embed.set_footer(text=footer)
        else:
            embed.set_footer(text=footer)
    if author:
        if author_image:
            if validators.url(author_image):
                embed.set_author(name=author, icon_url=author_image)
            else:
                embed.set_author(name=author)
        else:
            embed.set_author(name=author)
    if fields:
        for field in fields:
            embed.add_field(name=field[0], value=field[1], inline=field[2])
    return embed