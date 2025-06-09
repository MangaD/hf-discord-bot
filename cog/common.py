# Discord imports
import discord
from discord.ext import commands

import re  # Wrap links in < > brackets
import asyncio

from .Database import *

# Bot settings and configuration
BOT_PREFIX = "."
DESCRIPTION = (
	"Hello, I am HF Bot. I was born on July 8th, 2017. My creator is MangaD. "
	"I am awesome, I am great, I am the man, and yes, ladies, I am single!"
)
BOT_URL = "https://hf-empire.com"
ICON_URL = "https://hf-empire.com/favicon/favicon-16x16.png"

# Discord intents
intents = discord.Intents(
	messages=True,
	guilds=True,
	members=True,
	presences=True,
	voice_states=True,
	message_content=True
)
member_cache_flags = discord.MemberCacheFlags.all()

client = commands.Bot(
	command_prefix=BOT_PREFIX,
	description=DESCRIPTION,
	intents=intents,
	member_cache_flags=member_cache_flags
)
client.remove_command('help')

# Guild and channel IDs
HF_GUILD_ID = 234364433344888832
ENGLISH_GENERAL_ID = 234364433344888832
PVP_ID = 234395541453275136
MANGAD_ID = 222030109606019073
DOMAIN_OF_HF_BOT_CHANNEL_ID = 337250141083795456
ARTWORK_CHANNEL_ID = 891010482348105798
AI_ART_CHANNEL_ID = 1363939943533252760
MEDIA_CHANNEL_ID = 402476955003387905
INTRODUCTIONS_CHANNEL_ID = 860197524967391262
HF_MEMES_CHANNEL_ID = 394188677229576224
MEMES_CHANNEL_ID = 933263833324220457
NOTIFICATIONS_CHANNEL_ID = 1305142334286991460
WELCOME_CHANNEL_ID = 1357433032490877241

class MyGlobals:
	"""Global state variables for the bot."""
	last_message = None
	tts_enabled = False
	voice_client = None
	audio_player = None
	language = "en"
	# Dictionary to store user roles
	#user_roles = {}
	db = Database(client)

# Compile URL regex once globally
URL_REGEX = re.compile(r"((http://|https://)[^ <>'\"{}|\\^`\[\]]*)")

def encode_string_with_links(unencoded_string: str) -> str:
	"""
	Wrap URLs in < > to prevent Discord embedding.

	Args:
		unencoded_string (str): The input string containing URLs.

	Returns:
		str: The input string with URLs wrapped in < >.
	"""
	return URL_REGEX.sub(r'<\1>', unencoded_string)

def get_custom_emoji(name: str) -> discord.Emoji:
	"""
	Fetches a custom emoji by name.

	Args:
		name (str): The name of the emoji.

	Returns:
		discord.Emoji: The emoji object if found, else None.
	"""
	return discord.utils.get(client.emojis, name=name)

async def has_already_introduced(member: discord.Member, message_ignore: discord.Message = None) -> bool:
	"""
	Checks if a member has introduced themselves in the introductions channel.

	Args:
		member (discord.Member): The member to check.
		message_ignore (discord.Message): A message to ignore in the history check.

	Returns:
		bool: True if the member has already introduced, False otherwise.
	"""
	eng_general = client.get_channel(ENGLISH_GENERAL_ID)
	intro_channel = client.get_channel(INTRODUCTIONS_CHANNEL_ID)

	try:
		async for msg in intro_channel.history(limit=None):
			if msg.author.id == member.id and (message_ignore is None or msg != message_ignore):
				return True
	except discord.Forbidden:
		await eng_general.send(f"{client.get_user(MANGAD_ID).mention}: Permission to read {intro_channel.mention} message history is missing. :frowning:")
	except Exception as e:
		await eng_general.send(f"An exception occurred: {e}")

	return False
