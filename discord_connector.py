
"""
Reference documentation:
- https://discordpy.readthedocs.io/en/stable/discord.html#discord-intro
- https://docs.discord.com/developers/quick-start/getting-started

Useful concepts:
- Use the `@client.event` decorator to register an event (lots of events in this library!)
- This library is asynchronous:
    - Do things as a "callback"
    - Functions are called when something happens
- Bot sees all messages across all channels
    - Need to filter by channel
- A mention using @user is actually part of the message

Bot ideas:
1. Player login and logoff channel
2. Chat mirror passthrough from server to discord (maybe the other way around too?)

"""

import os
import discord
import asyncio
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
load_dotenv()


async def send_discord_message(message: str):
    """
    Send a message to a Discord channel.
    This function assumes token and channel id are available through the environment variables.
    
    Args:
        message: The message content to send
    """
    
    logger.debug("Getting environment variables and connecting to Discord...")
    try:
        bot_token = os.environ["DISCORD_BOT_TOKEN"]
        channel_id = int(os.environ["DISCORD_CHANNEL_ID"])
    except KeyError as e:
        logger.error(f"Missing required environment variable: {e}")
        return
    
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)
    
    @client.event
    async def on_ready():
        logger.info(f"Logged in to Discord as {client.user}")
        channel = client.get_channel(channel_id)
        if channel:
            await channel.send(message)
        else:
            logger.error(f"Channel {channel_id} not found.")
        await client.close()
    
    await client.start(bot_token)


def send_message(message: str):
    """Sync wrapper for send_discord_message"""
    asyncio.run(send_discord_message(message))

if __name__ == "__main__":
    send_message("You have run discord_connector.py as a main program. Don't do that.")
