import discord
from discord.ext import commands
import json
import os
import asyncio
from datetime import timedelta, datetime, timezone
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

async def main():
    async with bot:
        await bot.load_extension("trap")
        await bot.start(TOKEN)


CONFIG_FILE = "trap_channels.json"

class TrapChannel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = self.load_config()

    # === CONFIG LOAD / SAVE ===
    def load_config(self):
        default_config = {"servers": {}}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return default_config
        return default_config

    def save_config(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    # === CHECK CHANNEL ===
    def is_trap_channel(self, guild_id, channel_id):
        return str(channel_id) in self.config["servers"].get(str(guild_id), {}).get("trap_channels", [])

    # === COMMANDS ===
    @commands.hybrid_command(name="settrapchannel", description="Set a trap channel")
    @commands.has_permissions(administrator=True)
    async def set_trap_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        guild_id = str(ctx.guild.id)

        if guild_id not in self.config["servers"]:
            self.config["servers"][guild_id] = {"trap_channels": []}

        if str(channel.id) not in self.config["servers"][guild_id]["trap_channels"]:
            self.config["servers"][guild_id]["trap_channels"].append(str(channel.id))
            self.save_config()
            await ctx.send(f"✅ {channel.mention} is now set as a trap channel.")
        else:
            await ctx.send(f"⚠️ {channel.mention} is already a trap channel.")

    @commands.hybrid_command(name="removetrapchannel", description="Remove a trap channel")
    @commands.has_permissions(administrator=True)
    async def remove_trap_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        guild_id = str(ctx.guild.id)

        if guild_id in self.config["servers"]:
            if str(channel.id) in self.config["servers"][guild_id]["trap_channels"]:
                self.config["servers"][guild_id]["trap_channels"].remove(str(channel.id))
                self.save_config()
                await ctx.send(f"❌ {channel.mention} removed from trap channels.")
                return

        await ctx.send("⚠️ This channel is not configured as a trap channel.")

    # === DELETE USER MESSAGES IN LAST 10 MIN ===
    async def purge_user_messages(self, guild, user):
        now = datetime.now(timezone.utc)
        limit_time = now - timedelta(minutes=10)

        for channel in guild.text_channels:
            try:
                def check(msg):
                    return msg.author.id == user.id and msg.created_at > limit_time

                await channel.purge(limit=500, check=check)

            except discord.Forbidden:
                continue
            except Exception as e:
                print(f"Error in {channel.name}: {e}")

# === LISTENER ===
@commands.Cog.listener()
async def on_message(self, message: discord.Message):

    # Ignore bots
    if message.author.bot:
        return

    # Ignore DMs
    if not message.guild:
        return

    # Allow commands
    await self.bot.process_commands(message)

    # Ignore commands
    if message.content.startswith(("!", "/", "?")):
        return

    print(f"Message detected in: {message.channel.name}")

    # Check trap channel
    if not self.is_trap_channel(message.guild.id, message.channel.id):
        print("Not a trap channel")
        return

    print("TRAP CHANNEL DETECTED")

    user = message.author

    # Ignore admins
    if user.guild_permissions.administrator:
        print("Admin ignored")
        return

    # Delete message
    try:
        await message.delete()
        print("Message deleted")

    except Exception as e:
        print(f"Delete failed: {e}")

    # Timeout user
    try:
        await user.timeout(
            timedelta(hours=48),
            reason="Trap channel triggered"
        )

        print("User timed out")

    except Exception as e:
        print(f"Timeout failed: {e}")

    # Warning message
    try:
        warn_msg = await message.channel.send(
            f"🚫 {user.mention} DO NOT SEND MESSAGES HERE!"
        )

        await asyncio.sleep(5)
        await warn_msg.delete()

    except Exception as e:
        print(f"Warning failed: {e}")

        
    def cog_unload(self):
        pass


async def setup(bot):
    await bot.add_cog(TrapChannel(bot))
