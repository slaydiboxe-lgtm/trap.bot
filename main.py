import discord
from discord.ext import commands
import asyncio
import os

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

async def main():
    async with bot:
        await bot.load_extension("trap")
        await bot.start(TOKEN)

asyncio.run(main())
