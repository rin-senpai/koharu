import discord
from PIL import Image, ImageSequence
from io import BytesIO
import validators
import requests
import time

def resize(file, filename, width, height):
    start_time = time.time()
    image = Image.open(BytesIO(file))
    output = BytesIO()
    if filename.endswith('.gif'):
        frames = []
        durations = []
        for frame in ImageSequence.Iterator(image):
            frames.append(frame.resize((width, height)))
            durations.append(frame.info['duration'])
        frames[0].save(output, 'GIF', save_all=True, append_images=frames[1:], loop=0, duration=durations, disposal=2, optimize=True)
        print(time.time() - start_time)
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
