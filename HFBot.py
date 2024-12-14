#!/usr/bin/python3

import sys
import asyncio

# Cogs
import config
from cog.common import *
from cog.on_message import *
from cog.on_command import *
from cog.on_member_join import *
from cog.on_member_update import *
from cog import RandomMessage as rm
from cog import twitch

# this specifies what extensions to load when the bot starts up
startup_extensions = ["cog.Help",
		"cog.Games",
		"cog.Utilities",
		"cog.Discord",
		"cog.HeroFighter",
		"cog.Moderation"]

@client.event
async def on_ready():
	print("Bot Online!")
	print("Name: {}".format(client.user.name))
	print("ID: {}".format(client.user.id))
	print("Discord.py version: {}".format(discord.__version__))
	await asyncio.gather(
		client.change_presence(activity=discord.Game(name='Hero Fighter')) #,
		#rm.RandomMessage(), # Sends random messages to a channel once in a while
		#twitch.twitch() # Notifies in a channel when the Twitch stream has gone live
	)

async def run_bot():
	for extension in startup_extensions:
		try:
			await client.load_extension(extension)
		except Exception as e:
			exc = '{}: {}'.format(type(e).__name__, e)
			print('Failed to load extension {}\n{}'.format(extension, exc))
			exit()
	await client.start(config.bot_private_token, reconnect=True)

if __name__ == "__main__":
	if sys.version_info < (3,11):
		raise Exception("Python 3.11 or above must be used.")
	asyncio.run(run_bot())

