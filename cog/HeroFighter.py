import re
import urllib.request
from xml.dom import minidom
from random import randint
import requests
from discord.ext import commands
from .common import *

def url_status(url: str, timeout: int = 2) -> bool:
	"""Check if a given URL is reachable within a specified timeout."""
	from urllib.error import URLError, HTTPError
	from socket import timeout as SocketTimeout

	try:
		urllib.request.urlcleanup()
		code = urllib.request.urlopen(url, timeout=timeout).getcode()
		return code == 200
	except (HTTPError, URLError, SocketTimeout):
		return False

def search_user(forum_url: str, keyword: str, max_display: int) -> str:
	"""Search for users in a specified forum and return formatted results."""
	query = urllib.parse.quote(keyword)
	url = f"{forum_url}/memberlist.php?sort=postnum&username_match=contains&username={query}"
	response = requests.get(url, stream=True)

	pattern = re.compile(r'(?:(?:<td class="trow[12]">)|(?:<div class="plink text-center col-sm-12">)|(?:<h4 class="memberlistname">))<a href="(.*?)">(<span.*?>)?(.*)?</a>')
	users = pattern.findall(response.text)
	message = ""

	for i, (user_url, garbage, username) in enumerate(users):
		if i >= max_display:
			message += f"\nFor more users, visit: <{url}>\n"
			break
		username = re.sub(r"</?span>", "", username)
		username = re.sub(r"</?strong>", "**", username)
		username = re.sub(r"</?s>", "~~", username)
		user_url = user_url.replace("&amp;", "&")
		message += f"{username} - <{user_url}>\n"

	return message

def chunks(s: str, n: int):
	"""Generate `n`-character chunks from a given string `s`."""
	for start in range(0, len(s), n):
		yield s[start:start+n]

class HeroFighter(commands.Cog):
	"""Commands and utilities for the Hero Fighter community."""

	def __init__(self, client):
		self.client = client

	@commands.command(description="Provides download links for Hero Fighter and related resources.")
	async def download(self, ctx):
		"""Send download links for Hero Fighter and resources."""
		message = (
			"**HFX (mobile):** <https://hf-empire.com/hfx-empire/download>\n"
			"**HFv0.7+ w/ RS (PC):** <https://hf-empire.com/hf-empire/downloads>\n"
			"**HF Workshop:** <https://hf-empire.com/forum/showthread.php?tid=317>\n"
			"**ALL MODS:** <https://down.hf-empire.cn>"
		)
		await ctx.channel.send(message)

	@commands.command(description="Check if the Hero Fighter v0.7 services are operational.")
	async def status(self, ctx):
		"""Check the operational status of Hero Fighter websites and services."""
		message = (
			f"Hero Fighter website is **{'up' if url_status('http://herofighter.com') else 'down'}**!\n"
			f"Hero Fighter Empire website is **{'up' if url_status('https://hf-empire.com') else 'down'}**!\n"
			f"Hero Fighter v0.7 services are **{'up' if url_status('http://s.herofighter.com') else 'down'}**!"
		)
		await ctx.channel.send(message)

	@commands.command(description="Display the Hero Fighter room list.")
	async def rl(self, ctx):
		"""Fetch and display the Hero Fighter room list."""
		try:
			url = f"http://herofighter.com/hf/rlg.php?ver=700&cc=de&s={randint(0, 99999)}"
			data = urllib.request.urlopen(url).read()
		except IOError:
			await ctx.channel.send("Failed to connect to the Hero Fighter server.")
			return

		room_message = self.parse_room_list(data)
		for chunk in chunks(encode_string_with_links(room_message), 2000):
			await ctx.channel.send(chunk)

	def parse_room_list(self, data: bytes) -> str:
		"""Parse room list XML data and return it as a formatted string."""
		room_list = minidom.parseString(data).getElementsByTagName('room')
		if not room_list:
			return "No rooms available."

		room_message = ""
		for i, room in enumerate(room_list, start=1):
			room_name = room.getElementsByTagName("rn")[0].firstChild.nodeValue
			disconnects = room.getElementsByTagName("dc")[0].firstChild.nodeValue
			connections = room.getElementsByTagName("cc")[0].firstChild.nodeValue
			current = room.getElementsByTagName("n")[0].firstChild.nodeValue
			limit = room.getElementsByTagName("nl")[0].firstChild.nodeValue
			players = room.getElementsByTagName("ppl")[0].firstChild.nodeValue if room.getElementsByTagName("ppl")[0].firstChild else ""

			room_message += f"{i}. **{room_name}**\t{disconnects}\t{connections}\t{current}/{limit}\t{players}\n"		
		return room_message

	@commands.command(description="Search for a user in the Hero Fighter and Little Fighter forums.")
	async def search(self, ctx, *, word: str = None):
		"""Search for a user in Hero Fighter and Little Fighter forums."""
		if not word:
			await ctx.channel.send(f"**{ctx.author.name}:** Please specify a user to search for.")
			return

		max_users_to_display = 5
		message1 = search_user("https://hf-empire.com/forum", word, max_users_to_display)
		message2 = search_user("https://lf-empire.de/forum", word, max_users_to_display)

		final_message = ""
		if message1:
			final_message += f"**Hero Fighter Empire**\n\n{message1}"
		if message2:
			final_message += f"\n**Little Fighter Empire**\n\n{message2}" if message1 else f"**Little Fighter Empire**\n\n{message2}"

		if final_message:
			await ctx.channel.send(final_message)
		else:
			await ctx.channel.send("No users matching the criteria.")

async def setup(client):
	await client.add_cog(HeroFighter(client))
