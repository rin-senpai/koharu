from discord import app_commands
import discord
from PIL import Image, ImageSequence
from io import BytesIO
import validators
import requests
import aiohttp

def resize(file, filename, width, height):
    image = Image.open(BytesIO(file))
    output = BytesIO()
    if filename.endswith('.gif'):
        frames = []
        durations = []
        for frame in ImageSequence.Iterator(image):
            frames.append(frame.resize((width, height)))
            durations.append(frame.info['duration'])
        frames[0].save(output, 'GIF', save_all=True, append_images=frames[1:], loop=0, duration=durations, disposal=2, optimize=True)
    else:
        image = image.resize((width, height))
        image.save(output, 'PNG')
    output.seek(0)
    return discord.File(output, filename=filename)

def is_image_url(url):
    if not validators.url(url):
        return False
    image_formats = ('image/png', 'image/jpeg', 'image/jpg', 'image/gif')
    r = requests.head(url)
    if r.headers["content-type"] in image_formats:
      return True
    return False

async def url_to_file(url, filename):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            data = BytesIO(await resp.read())
            return discord.File(data, filename)
