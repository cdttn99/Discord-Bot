#!/opt/Smilebot/venv/bin/python
import discord
from discord.ext import commands
import asyncio
from fuzzywuzzy import fuzz
import datetime
import subprocess
from dotenv import load_dotenv
import os

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
LOG_FILE = "/opt/minecraft/ServerFiles-4.5/logs/latest.log"

@bot.event
async def  on_ready():
    print(f"Logged in as {bot.user}")

kill_phrases = [
    "kill yourself",
    "kys",
    "kill myself",
    "kill thineself",
]

@bot.event
async def on_message(message):
    content = message.content.lower()
    for phrase in kill_phrases:
        similarity = fuzz.partial_ratio(content, phrase)
        if similarity > 80:
            try:
                video = discord.File("dont_do_it.mp4")
                msg = await message.channel.send(f"{message.author.mention} watch this and respond with ✅ or you will be banned", file=video)
                await msg.add_reaction("✅")
                def check(reaction, user):
                    return user == message.author  and str(reaction.emoji) == "✅" and reaction.message.id == msg.id
                try:
                    await bot.wait_for("reaction_add", timeout=90.0, check=check)
                    msg2 = await message.channel.send("Thank you for confirming.")
                    await asyncio.sleep(5)
                    await msg2.delete()
                except asyncio.TimeoutError:
                    ban1 = await message.channel.send(f"{message.author.mention} did not respond in time. Timing out for 10 minutes.")
                    await asyncio.sleep(5)
                    await ban1.delete()
                    try:
                        ban2 = await message.author.timeout(discord.utils.utcnow() + discord.timedelta(minutes=1), reason="No confirmation after concerning message.")
                        await asyncio.sleep(5)
                        await ban2.delete()
                    except Exception as e:
                        await message.channel.send("Failed to timeout user. Do I have the correct permissions?")
                await asyncio.sleep(5)
                await msg.delete()
            except Exception as e:
                await message.channel.send("Failed to send video.")
    await bot.process_commands(message)

@bot.command()
@commands.has_permissions(administrator=True)
async def timeout(ctx, member: discord.Member, duration: str, *, reason ="no reason provided"):
    time_unit = duration[-1]
    try:
        time_value = int(duration[:-1])
    except ValueError:
        await ctx.send("Invalid Time")
        return
    
    time_map = {'s': 'seconds', 'm': 'minutes', 'h': 'hours'}
    if time_unit not in time_map:
        await ctx.send("Invalid time unit. Use `s`, `m`, or `h`.")
        return
    
    kwargs = {time_map[time_unit]: time_value}
    delta = timedelta(**kwargs)

    try:
        await member.timeout(delta, reason=reason)
        msg = await ctx.send(f"{member.mention} has been timed out for {duration}.")
        await ctx.message.delete()
        await asyncio.sleep(time_value)
        await msg.delete()
    except discord.Forbidden:
        await ctx.send("I don't have permission to timeout this user.")
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def Restartmc(ctx):
    try:
        await ctx.send("Restarting Server")
        subprocess.run(["sudo", "systemctl", "stop", "minecraftserver.service"])
        subprocess.run(["sudo", "rm", "-f", "/opt/minecraft/ServerFiles-4.5/logs/latest.log"])
        await asyncio.sleep(5)
        subprocess.run(["sudo", "systemctl", "start", "minecraftserver.service"])
        server_ready = await wait_for_server_ready(ctx, timeout=180)
        if server_ready:
            await ctx.send("Minecraft Server is alive!")
        else:
            await ctx.send("Timed out waiting for the server to start.")

    except Exception as e:
        await ctx.send(f"Unable to complete task. Error: {str(e)}")

async def wait_for_server_ready(ctx, timeout=180):
    start_time = datetime.datetime.now()
    deadline = start_time + datetime.timedelta(seconds=timeout)
    seen_lines = set()

    while datetime.datetime.now() < deadline:
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()
            for line in lines:
                if line not in seen_lines:
                    seen_lines.add(line)
                    if "Dedicated server took" in line:
                        return True
    return False

@timeout.error
async def timeout_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(f"{ctx.author.mention}, you do not have permission to do that")


bot.run(TOKEN)
