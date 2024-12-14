#!/usr/bin/python3

import sys
import asyncio
import discord

# Cogs
import config
from cog.common import *
from cog.on_message import *
from cog.on_command import *
from cog.on_member_join import *
from cog.on_member_update import *
from cog import RandomMessage as rm
from cog import twitch

# Extensions to load on startup
STARTUP_EXTENSIONS = (
	"cog.Help",
	"cog.Games",
	"cog.Utilities",
	"cog.Discord",
	"cog.HeroFighter",
	"cog.Moderation"
)

@client.event
async def on_ready():
	print("Bot Online!")
	print(f"Name: {client.user.name}")
	print(f"ID: {client.user.id}")
	print(f"Discord.py version: {discord.__version__}")

	# Use asyncio.gather() to manage multiple background tasks if needed
	await asyncio.gather(
		client.change_presence(activity=discord.Game(name='Hero Fighter')),
		# Uncomment if needed:
		# rm.RandomMessage(),  # Sends random messages to a channel periodically
		# twitch.twitch()	  # Notifies a channel when a Twitch stream goes live
	)

async def load_extensions():
	for extension in STARTUP_EXTENSIONS:
		try:
			await client.load_extension(extension)
			print(f"Loaded extension: {extension}")
		except Exception as e:
			print(f"Failed to load extension {extension}: {type(e).__name__}: {e}")

async def run_bot():
	await load_extensions()
	await client.start(config.bot_private_token, reconnect=True)

if __name__ == "__main__":
	if sys.version_info < (3, 11):
		raise Exception("Python 3.11 or above is required.")
	
	try:
		asyncio.run(run_bot())
	except Exception as e:
		print(f"Error running bot: {type(e).__name__}: {e}")
		sys.exit(1)
