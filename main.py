import discord
import datetime
import os
import asyncio
from secret import token


client = discord.Bot()


@client.event
async def on_ready():
    print('ready')
    await asyncio.sleep(10)
    while True:
        print(datetime.datetime.now())
        await asyncio.sleep(3600)


for f in os.listdir('./cogs'):
    if f.endswith('.py'):
        client.load_extension(f'cogs.{f[:-3]}', store=False)


if __name__ == '__main__':
    client.run(token)