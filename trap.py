import discord
from discord.ext import commands
import json
import os
import asyncio
from datetime import timedelta

CONFIG_FILE = "trap_channels.json"


class TrapChannel(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = self.load_config()

    # LOAD CONFIG
    def load_config(self):

        if not os.path.exists(CONFIG_FILE):
            return {"servers": {}}

        with open(CONFIG_FILE, "r") as f:
            return json.load(f)

    # SAVE CONFIG
    def save_config(self):

        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config, f, indent=4)

    # CHECK TRAP CHANNEL
    def is_trap_channel(self, guild_id, channel_id):

        guild_id = str(guild_id)
        channel_id = str(channel_id)

        return (
            guild_id in self.config["servers"]
            and channel_id in self.config["servers"][guild_id]["trap_channels"]
        )

    # SET TRAP CHANNEL
    @commands.hybrid_command(name="settrapchannel")
    @commands.has_permissions(administrator=True)
    async def settrapchannel(self, ctx, channel: discord.TextChannel):

        guild_id = str(ctx.guild.id)

        if guild_id not in self.config["servers"]:
            self.config["servers"][guild_id] = {
                "trap_channels": []
            }

        if str(channel.id) not in self.config["servers"][guild_id]["trap_channels"]:

            self.config["servers"][guild_id]["trap_channels"].append(
                str(channel.id)
            )

            self.save_config()

            await ctx.send(
                f"✅ {channel.mention} set as trap channel"
            )

        else:
            await ctx.send("Channel already added")

    # REMOVE TRAP CHANNEL
    @commands.hybrid_command(name="removetrapchannel")
    @commands.has_permissions(administrator=True)
    async def removetrapchannel(self, ctx, channel: discord.TextChannel):

        guild_id = str(ctx.guild.id)

        if (
            guild_id in self.config["servers"]
            and str(channel.id) in self.config["servers"][guild_id]["trap_channels"]
        ):

            self.config["servers"][guild_id]["trap_channels"].remove(
                str(channel.id)
            )

            self.save_config()

            await ctx.send(
                f"❌ Removed {channel.mention}"
            )

        else:
            await ctx.send("Channel not found")

    # MESSAGE LISTENER
    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot:
            return

        if not message.guild:
            return

        await self.bot.process_commands(message)

        # Ignore commands
        if message.content.startswith(("!", "/", "?")):
            return

        # Check trap channel
        if not self.is_trap_channel(
            message.guild.id,
            message.channel.id
        ):
            return

        user = message.author

        # Ignore admins
        if user.guild_permissions.administrator:
            return

        # DELETE MESSAGE
        try:
            await message.delete()
        except:
            pass

        # TIMEOUT USER
        try:
            await user.timeout(
                timedelta(hours=48),
                reason="Trap channel triggered"
            )
        except Exception as e:
            print(e)

        # WARNING MESSAGE
        try:

            warn = await message.channel.send(
                f"🚫 {user.mention} DO NOT SEND MESSAGES HERE!"
            )

            await asyncio.sleep(5)

            await warn.delete()

        except:
            pass


async def setup(bot):
    await bot.add_cog(TrapChannel(bot))
