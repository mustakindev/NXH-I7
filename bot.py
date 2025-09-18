# bot.py → Main bot entry point ✨
import discord
from discord.ext import commands
import json
import os
import asyncio
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('nxh-i7')

# Load config
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Bot setup
bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None,
    activity=discord.Activity(
        type=discord.ActivityType.watching,
        name="🌸 Cute VPS Panels"
    )
)

# Store start time for uptime
bot.start_time = datetime.utcnow()

# Load cogs
async def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and not filename.startswith('__'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                logger.info(f'✅ Loaded cog: {filename}')
            except Exception as e:
                logger.error(f'❌ Failed to load cog {filename}: {e}')

@bot.event
async def on_ready():
    logger.info(f'🌸 {bot.user} is online and ready!')
    logger.info(f'👑 Serving {len(bot.guilds)} server(s)')
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        logger.info(f'🔁 Synced {len(synced)} slash commands')
    except Exception as e:
        logger.error(f'❌ Failed to sync commands: {e}')
    
    # Set rich presence rotation
    statuses = [
        ("watching", "🌸 Cute VPS Panels"),
        ("playing", "💻 Hosting with Love"),
        ("listening", "🎀 Your VPS requests")
    ]
    
    async def rotate_status():
        while True:
            for activity_type, text in statuses:
                if activity_type == "watching":
                    activity = discord.Activity(type=discord.ActivityType.watching, name=text)
                elif activity_type == "playing":
                    activity = discord.Activity(type=discord.ActivityType.playing, name=text)
                else:
                    activity = discord.Activity(type=discord.ActivityType.listening, name=text)
                await bot.change_presence(activity=activity)
                await asyncio.sleep(30)  # Rotate every 30 seconds
    
    bot.loop.create_task(rotate_status())

@bot.event
async def on_member_join(member):
    """Optional: Track new members for invite tracking system"""
    pass

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("👑 You don't have permission to use this command!")
    else:
        logger.error(f'⚠️ Command error: {error}')
        await ctx.send("💔 An error occurred. Please try again later!")

if __name__ == "__main__":
    asyncio.run(load_cogs())
    bot.run(config['token'])
