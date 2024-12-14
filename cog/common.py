# Discord
import discord
from discord.ext.commands import Bot
from discord.ext import commands

import re # wrap links in < >

# Discord stuff

# Intents were added in v1.5
# An intent basically allows a bot to subscribe into specific buckets of events.
# https://discordpy.readthedocs.io/en/latest/intents.html
intents = discord.Intents(messages=True, guilds=True, members=True, presences=True, voice_states=True)
member_cache_flags = discord.MemberCacheFlags.all()

bot_prefix = "."
description = "Hello, I am HF Bot. I was born in July 8th, 2017. My father is MangaD. I am awesome, I am great, I am the man, and yes, ladies, I am single!"
bot_url = "https://hf-empire.com"
icon_url = "https://hf-empire.com/favicon/favicon-16x16.png"
client = commands.Bot(command_prefix=bot_prefix, description=description, intents=intents, member_cache_flags=member_cache_flags)
client.remove_command('help')

# ID's
hf_guild_id = 234364433344888832
english_general_id = 234364433344888832
pvp_id = 234395541453275136
mangad_id = 222030109606019073

domain_of_hf_bot_channel = 337250141083795456
artwork_channel = 891010482348105798
media_channel = 402476955003387905
introductions_channel = 860197524967391262
hf_memes_channel = 394188677229576224

class MyGlobals(object):
	last_message = None
	# TTS
	tts_v = False
	voice = None
	player = None
	lang = "en"
	# Bandit role is given on join for the user ids in this list
	muted_users_ids = [

	];

# Useful functions
def encode_string_with_links(unencoded_string):
        URL_REGEX = re.compile(r'''((http://|https://)[^ <>'"{}|\\^`[\]]*)''')
        return URL_REGEX.sub(r'<\1>', unencoded_string)

def get_custom_emoji(name):
	for x in client.get_all_emojis():
			if x.name == name:
				return x

