
"""
Reference documentation:
- https://discordpy.readthedocs.io/en/stable/discord.html#discord-intro
- https://docs.discord.com/developers/quick-start/getting-started

"""

import os
import discord

# clients are our connection to Discord
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
bot_token = os.environ["DISCORD_BOT_TOKEN"]
channel_id = 1497415786925391933 # TODO: Replace with environment variable too?
message = "Hello world!"

"""
use the `@client.event` decorator to register an event (lots of events in this library!)

library is asynchronous:
- do things as a "callback"
- functions are called when something happens

"""

@client.event
async def on_ready(): # the bot has finished loggin on
    print(f'We have logged in as {client.user}')

    # Send message to specific channel
    channel = client.get_channel(channel_id)
    if channel:
        await channel.send(message)

@client.event
async def on_message(message): # the bot has received a message
    if message.author == client.user: # ignore messages from ourselves (this event triggers for every message received)
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

client.run(bot_token) # run the bot with a login token (DO NOT COMMIT!)

"""
INTEGRATION IDEAS:
1. Player login and logoff channel
2. Chat mirror passthrough from server to discord (maybe the other way around too?)

Experiment findings:
- Bot sees all messages across all channels
    - Need to filter by channel
- A mention using @user is actually part of the message (duh)


"""

