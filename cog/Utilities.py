# Import necessary modules
import os
import sys
import random
import json
import requests
import re
import html
import asyncio
import urllib.parse
from urllib.parse import quote
from datetime import datetime
from urllib import parse
from bs4 import BeautifulSoup
import openai
import pytz
import yt_dlp
import discord
from .common import *
import config

# Add the parent directory to sys.path for module access
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

# YouTube Downloader Configuration
ytdl_format_options = {
	'format': 'bestaudio',
	'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
	'restrictfilenames': True,
	'noplaylist': True,
	'nocheckcertificate': True,
	'ignoreerrors': False,
	'quiet': True,
	'no_warnings': True,
	'default_search': 'auto',
	'source_address': '0.0.0.0'  # Bind to IPv4 to avoid IPv6 issues
}

# FFmpeg options for audio playback
ffmpeg_options = {
	'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
	'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)
voice_channel = None
playing = False

class YTDLSource(discord.PCMVolumeTransformer):
	def __init__(self, source, *, data, volume=0.5):
		super().__init__(source, volume)
		self.data = data
		self.title = data.get('title')
		self.url = data.get('url')

	@classmethod
	async def from_url(cls, url, *, loop=None, stream=True):
		loop = loop or asyncio.get_event_loop()
		try:
			data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
			if 'entries' in data:
				# Take first item from a playlist if multiple entries
				data = data['entries'][0]
			filename = data['url'] if stream else ytdl.prepare_filename(data)
			return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
		except Exception as e:
			print(f"Error extracting info from YouTube URL: {e}")
			return None

async def disconnect_after_finished(e=None):
	"""Disconnect from voice channel after playback is finished, handling errors if any."""
	await MyGlobals.voice_client.disconnect()
	MyGlobals.playing = False
	if e:
		print(f'Player error: {e}')

def search_youtube(query):
	"""Search YouTube and return the URL of the first matching video."""
	# If input is already a YouTube URL, return it directly
	if re.match(r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$', query):
		return query

	query_encoded = urllib.parse.quote(query)
	search_url = f"https://www.youtube.com/results?search_query={query_encoded}"
	session = requests.Session()
	session.cookies.set('CONSENT', 'WP.27b9d3', domain=".youtube.com")
	response = session.get(search_url)

	match = re.search(r'"url":"\/watch\?v=([^"]+)"', response.text)
	if match:
		video_id = match.group(1)
		return f'https://www.youtube.com/watch?v={video_id}'
	return None

# Miscellaneous Functions
mangle_lines = {}

def get_random_lang(long_list, short_list):
	"""Select a random language from `long_list` not in `short_list` and add it to `short_list`."""
	random_lang = random.choice(long_list)
	if random_lang not in short_list:
		short_list.append(random_lang)
	else:
		return get_random_lang(long_list, short_list)
	return short_list

def translate(text, in_lang='auto', out_lang='en', verify_ssl=True):
	"""Translate text using Google Translate API."""
	is_raw_output = out_lang.endswith('-raw')
	if is_raw_output:
		out_lang = out_lang[:-4]

	headers = {
		'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11'
	}

	params = {
		"client": "gtx",
		"sl": in_lang,
		"tl": out_lang,
		"dt": "t",
		"q": text,
	}
	url = "http://translate.googleapis.com/translate_a/single"

	try:
		response = requests.get(url, params=params, timeout=40, headers=headers, verify=verify_ssl)
		response.raise_for_status()
		result = response.text

		if result == '[,,""]':
			return None, in_lang

		while ',,' in result:
			result = result.replace(',,', ',null,').replace('[,', '[null,')

		data = json.loads(result)

		if is_raw_output:
			return str(data), 'en-raw'

		language = data[2] if len(data) > 2 else '?'
		translated_text = ''.join(x[0] for x in data[0])
		return translated_text, language
	except requests.RequestException as e:
		print(f"Request error during translation: {e}")
		return None, in_lang
	except (json.JSONDecodeError, IndexError) as e:
		print(f"Error parsing translation data: {e}")
		return None, in_lang

# Wiktionary lookups
wiktionary_uri = 'http://en.wiktionary.org/w/index.php?title={}&printable=yes'
tag_pattern = re.compile(r'<[^>]+>')
unordered_list_pattern = re.compile(r'(?ims)<ul>.*?</ul>')

def clean_html_tags(html_content):
	"""Clean HTML tags from the provided content and format text."""
	cleaned_text = tag_pattern.sub('', html_content).strip()
	return (
		cleaned_text.replace('\n', ' ')
		.replace('\r', '')
		.replace('(intransitive', '(intr.')
		.replace('(transitive', '(trans.')
	)

def fetch_wiktionary_entry(word):
	"""Fetch definitions from Wiktionary for the specified word."""
	try:
		response = requests.get(wiktionary_uri.format(quote(word)), stream=True)
		response.raise_for_status()
		content = html.unescape(response.text)
		cleaned_content = unordered_list_pattern.sub('', content)
	except requests.RequestException as e:
		print(f"Error fetching Wiktionary entry: {e}")
		return None, {}

	mode = None
	etymology = None
	definitions = {}

	for line in cleaned_content.splitlines():
		# Identify modes (parts of speech or etymology)
		if 'id="Etymology"' in line:
			mode = 'etymology'
		elif 'id="Noun"' in line:
			mode = 'noun'
		elif 'id="Verb"' in line:
			mode = 'verb'
		elif 'id="Adjective"' in line:
			mode = 'adjective'
		elif 'id="Adverb"' in line:
			mode = 'adverb'
		elif 'id="Interjection"' in line:
			mode = 'interjection'
		elif 'id="Particle"' in line:
			mode = 'particle'
		elif 'id="Preposition"' in line:
			mode = 'preposition'
		elif 'id="' in line:
			mode = None

		# Capture etymology or definition lines
		elif mode == 'etymology' and '<p>' in line:
			etymology = clean_html_tags(line)
		elif mode and '<li>' in line:
			definitions.setdefault(mode, []).append(clean_html_tags(line))

		if '<hr' in line:
			break

	return etymology, definitions

# Part of speech categories to display
parts_of_speech = ('preposition', 'particle', 'noun', 'verb', 'adjective', 'adverb', 'interjection')

def format_definitions(result, definitions, max_definitions=2):
	"""Format definitions for display with a limit on the number per part of speech."""
	for part in parts_of_speech:
		if part in definitions:
			defs = definitions[part][:max_definitions]
			formatted_defs = '\n'.join(f'{i + 1}. {e.strip(" .")}' for i, e in enumerate(defs))
			result += f'\n\n**{part.capitalize()}**: {formatted_defs}'
	return result.strip(' .,')

# Discord integration
class Utilities(commands.Cog):
	"""Useful commands for everyday life."""

	def __init__(self, client):
		self.client = client

	@commands.command(name='8', description='Ask the magic 8-ball a question! Usage: `.8 <question>`')
	async def ball(self, ctx):
		"""Ask the magic 8-ball a question."""
		responses = [
			"It is certain", "It is decidedly so", "Without a doubt", "Yes definitely",
			"You may rely on it", "As I see it yes", "Most likely", "Outlook good", "Yes",
			"Signs point to yes", "Reply hazy try again", "Ask again later", "Better not tell you now",
			"Cannot predict now", "Concentrate and ask again", "Don't count on it", "My reply is no",
			"God says no", "Very doubtful", "Outlook not so good"
		]
		await ctx.channel.send(random.choice(responses))

	@commands.command(description='Look up a video on YouTube. Usage: `.yt <search_phrase>`')
	async def yt(self, ctx, *, search_phrase: str = None):
		"""Look up a video on YouTube."""
		if not search_phrase:
			await ctx.channel.send(f"**{ctx.author.name}:** Please provide a search term.")
			return
		url = search_youtube(search_phrase)
		if not url:
			await ctx.channel.send(f"**{ctx.author.name}:** Could not find a video for '{search_phrase}'.")
		else:
			await ctx.channel.send(url)

	@commands.command(description='Text to speech with optional language hint. Usage: `.tts es`')
	async def tts(self, ctx, *, lang_code: str = "en"):
		"""Text to speech with optional language hint."""
		if "streamer" not in [role.name.lower() for role in ctx.author.roles]:
			await ctx.channel.send(f"**{ctx.author.name}:** You do not have permission to use this command.")
			return

		if MyGlobals.tts_enabled:
			await self.stop_tts(ctx)
			return

		if ctx.author.voice is None:
			await ctx.channel.send(f"**{ctx.author.name}:** You must join a voice channel!")
			return

		try:
			await self.start_tts(ctx, lang_code)
		except Exception as e:
			MyGlobals.tts_enabled = False
			MyGlobals.languague = "en"
			MyGlobals.voice_client = None
			await ctx.channel.send(f"Error: {e}")

	async def start_tts(self, ctx, lang_code):
		"""Start TTS playback."""
		MyGlobals.tts_enabled = True
		MyGlobals.language = lang_code
		voice_channel = ctx.author.voice.channel
		if MyGlobals.voice_client and MyGlobals.voice_client.is_connected():
			await MyGlobals.voice_client.move_to(voice_channel)
		else:
			MyGlobals.voice_client = await voice_channel.connect()

	async def stop_tts(self, ctx):
		"""Stop TTS playback."""
		await MyGlobals.voice_client.disconnect()
		MyGlobals.tts_enabled = False
		MyGlobals.language = "en"
		await ctx.channel.send(f"**{ctx.author.name}:** Stopped TTS.")

	@commands.command(description='Play a YouTube video in voice channel. Usage: `.ytc <search_phrase or url>`')
	async def ytc(self, ctx, *, search_phrase: str = None):
		"""Play a YouTube video in the voice channel."""
		if "streamer" not in [role.name.lower() for role in ctx.author.roles]:
			await ctx.channel.send(f"**{ctx.author.name}:** You do not have permission to use this command.")
			return

		if MyGlobals.tts_enabled:
			await ctx.channel.send(f"**{ctx.author.name}:** Cannot play YouTube video while TTS is active.")
			return

		if ctx.author.voice is None:
			await ctx.channel.send(f"**{ctx.author.name}:** You must join a voice channel!")
			return

		if not search_phrase:
			await ctx.channel.send(f"**{ctx.author.name}:** Please provide a search term or URL.")
			return

		try:
			await self.play_youtube_audio(ctx, search_phrase)
		except Exception as e:
			await ctx.channel.send(f"Error: {e}")

	async def play_youtube_audio(self, ctx, search_phrase):
		"""Play YouTube audio in voice channel."""
		url = search_youtube(search_phrase)
		if not url:
			await ctx.channel.send(f"**{ctx.author.name}:** Could not find a video.")
			return

		voice_channel = ctx.author.voice.channel
		if MyGlobals.voice_client and MyGlobals.voice_client.is_connected():
			await MyGlobals.voice_client.move_to(voice_channel)
		else:
			MyGlobals.voice_client = await voice_channel.connect()

		async with ctx.typing():
			MyGlobals.audio_player = await YTDLSource.from_url(url, loop=self.client.loop)
			if MyGlobals.voice_client.is_playing():
				MyGlobals.voice_client.stop()
			MyGlobals.voice_client.play(MyGlobals.audio_player)
		await ctx.send(f"Now playing: {MyGlobals.audio_player.title}")
		MyGlobals.playing = True
	@commands.command(description='Pause or resume audio from voice channel. Usage: `.ytp`')

	async def ytp(self, ctx):
		"""Toggle pause/resume for audio in the voice channel."""
		try:
			if MyGlobals.voice_client and MyGlobals.voice_client.is_connected():
				if MyGlobals.voice_client.is_playing() and not MyGlobals.voice_client.is_paused():
					MyGlobals.voice_client.pause()
					await ctx.send('Audio paused.')
				elif MyGlobals.voice_client.is_paused():
					MyGlobals.voice_client.resume()
					await ctx.send('Audio resumed.')
				else:
					await ctx.send("No audio is playing.")
			else:
				await ctx.send("Not connected to a voice channel.")
		except Exception as e:
			await ctx.send(f"Error: {e}")

	@commands.command(description='Disconnect from voice channel. Usage: `.ytd`')
	async def ytd(self, ctx):
		"""Disconnect from voice channel."""
		if "streamer" not in [role.name.lower() for role in ctx.author.roles]:
			await ctx.send(f"**{ctx.author.name}:** You do not have permission to use this command.")
			return
		if MyGlobals.tts_enabled:
			await ctx.send(f"**{ctx.author.name}:** Cannot disconnect while TTS is active.")
			return

		if MyGlobals.voice_client and MyGlobals.voice_client.is_connected():
			await MyGlobals.voice_client.disconnect()
			MyGlobals.playing = False
			await ctx.send("Disconnected from the voice channel.")
		else:
			await ctx.send("Not connected to a voice channel.")

	@commands.command(description='Look up a word on UrbanDictionary. Usage: `.ud <word>`')
	async def ud(self, ctx, *, word: str = None):
		"""Look up a word on UrbanDictionary."""
		if not word:
			await ctx.send(f"**{ctx.author.name}:** Please provide a word to look up.")
			return

		try:
			url = f"http://www.urbandictionary.com/define.php?term={word}"
			response = requests.get(url)
			response.raise_for_status()
			soup = BeautifulSoup(response.content, "html.parser")
			meaning = soup.find("div", attrs={"class": "meaning"})
			
			if meaning:
				meaning_text = meaning.get_text().replace("&apos", "'")
				if any(bad_word in meaning_text.lower() for bad_word in config.bad_words):
					meaning_text = "*- nsfw -*"
				
				if len(meaning_text) > 300:
					meaning_text = meaning_text[:295] + '[...]'
				await ctx.send(f"**{ctx.author.name}:** {meaning_text}")
			else:
				await ctx.send(f"**{ctx.author.name}:** Couldn't find any definitions for '{word}'.")
		except requests.RequestException as e:
			await ctx.send(f"Error fetching UrbanDictionary entry: {e}")
		except Exception as e:
			await ctx.send(f"Error processing UrbanDictionary entry: {e}")

	@commands.command(description='Look up a word on Wiktionary. Usage: `.wt <word>`')
	async def wt(self, ctx, *, word: str = None):
		"""Look up a word on Wiktionary."""
		if not word:
			await ctx.send(f"**{ctx.author.name}:** Please provide a word to look up.")
			return

		try:
			etymology, definitions = fetch_wiktionary_entry(word)
			if not definitions:
				await ctx.send(f"**{ctx.author.name}:** Couldn't find any definitions for '{word}'.")
				return
			
			result = format_definitions(f"**__{word}__**", definitions)
			if len(result) > 300:
				result = result[:295] + '[...]'
			await ctx.send(result)
		except Exception as e:
			await ctx.send(f"Error fetching Wiktionary entry: {e}")

	@commands.command(description='Look up something on Wikipedia. Usage: `.w <phrase>`')
	async def w(self, ctx, *, phrase: str = None):
		"""Look up something on Wikipedia."""

		if not phrase or len(phrase.strip()) == 0:
			await ctx.channel.send(f"**{ctx.author.name}:** Please provide a phrase to look up.")
			return
		if len(phrase) > 2000:
			await ctx.channel.send(f"**{ctx.author.name}:** Phrase must be under 2000 characters.")
			return

		# Determine language and server
		lang = 'en'
		tokens = phrase.split()
		if tokens[0].startswith(":"):
			lang = tokens.pop(0)[1:]
			phrase = " ".join(tokens)

		server = f'{lang}.wikipedia.org'
		search_url = f'https://{server}/w/api.php?format=json&action=query&list=search&srlimit=1&srprop=timestamp&srwhat=text&srsearch={urllib.parse.quote(phrase)}'

		# Perform search query
		try:
			search_response = requests.get(search_url).json()
			search_results = search_response.get("query", {}).get("search", [])
			if not search_results:
				await ctx.channel.send(f"**{ctx.author.name}:** No results found for '{phrase}'.")
				return
			page_title = search_results[0]["title"]
		except (requests.RequestException, KeyError) as e:
			await ctx.channel.send(f"**{ctx.author.name}:** Error fetching search results: {e}")
			return

		# Fetch snippet
		snippet_url = f'https://{server}/w/api.php?format=json&action=query&prop=extracts&exintro&explaintext&exchars=300&redirects&titles={urllib.parse.quote(page_title)}'
		try:
			snippet_response = requests.get(snippet_url).json()
			page_data = next(iter(snippet_response["query"]["pages"].values()))
			snippet = page_data.get("extract", "No extract available.")
		except (requests.RequestException, KeyError) as e:
			await ctx.channel.send(f"**{ctx.author.name}:** Error fetching snippet for '{page_title}': {e}")
			return

		# Format and send message
		page_url = f'https://{server}/wiki/{urllib.parse.quote(page_title)}'
		await ctx.channel.send(f'[WIKIPEDIA] {page_title} | "{snippet}" | <{page_url}>')

	@commands.command(description='Translates a phrase with optional language hints. Usage: `.tr :en :zh <phrase>`')
	async def tr(self, ctx, *, phrase: str = None):
		"""Translate a phrase, with optional language hints for input and output languages."""

		if not phrase or len(phrase.strip()) == 0:
			await ctx.channel.send(f"**{ctx.author.name}:** Please provide a phrase to translate.")
			return
		if len(phrase) > 2000:
			await ctx.channel.send(f"**{ctx.author.name}:** Phrase must be under 2000 characters.")
			return

		in_lang, out_lang, phrase_text = self.parse_languages(phrase)

		if in_lang != out_lang:
			try:
				translated_text, detected_lang = translate(phrase_text, in_lang, out_lang)
				if translated_text:
					response = f'"{translated_text}" ({detected_lang} to {out_lang}, translate.google.com)'
				else:
					response = f'Translation from {in_lang} to {out_lang} failed. Please check language abbreviations.'
			except Exception as e:
				response = f"Error in translation: {e}"
			await ctx.channel.send(f"**{ctx.author.name}:** {response}")
		else:
			await ctx.channel.send(f"**{ctx.author.name}:** Could not guess the language. Please specify input and output languages.")

	def parse_languages(self, phrase):
		"""Parse the input and output languages from a given phrase."""
		tokens = phrase.split()
		in_lang = 'auto'
		out_lang = 'en'
		
		if tokens[0].startswith(":"):
			in_lang = tokens.pop(0)[1:]
			if tokens and tokens[0].startswith(":"):
				out_lang = tokens.pop(0)[1:]
		phrase_text = " ".join(tokens)
		
		return in_lang, out_lang, phrase_text

	@commands.command(description='Repeatedly translates the input until it becomes nonsensical. Usage: `.mangle <phrase>`')
	async def mangle(self, ctx, *, phrase: str = None):
		"""Repeatedly translates the input to multiple languages until it loses meaning."""
		
		long_lang_list = ['fr', 'de', 'es', 'it', 'no', 'he', 'la', 'ja', 'cy', 'ar', 'yi', 'zh', 'nl', 'ru', 'fi', 'hi', 'af', 'jw', 'mr', 'ceb', 'cs', 'ga', 'sv', 'eo', 'el', 'ms', 'lv']
		lang_sequence = random.sample(long_lang_list, 8)
		
		if not phrase:
			phrase = MyGlobals.last_message or ""
			if not phrase:
				await ctx.channel.send(f"**{ctx.author.name}:** Please specify a phrase to mangle.")
				return

		mangled_text = phrase.strip()

		for lang in lang_sequence:
			try:
				# Translate to a random language and then back to English
				mangled_text, _ = translate(mangled_text, 'en', lang)
				mangled_text, _ = translate(mangled_text, lang, 'en')
			except Exception as e:
				await ctx.channel.send(f"Error during mangling: {e}")
				return
		
		await ctx.channel.send(f"**{ctx.author.name}:** {mangled_text}")

	@commands.command(description='Get the time in a specific timezone. Usage: `.time Asia/Hong_Kong`')
	async def time(self, ctx, *, zone: str = None):
		"""Get the time in a specific timezone."""
		if not zone:
			await ctx.channel.send(f"**{ctx.author.name}:** You need to specify a timezone.")
			return

		try:
			timezone = pytz.timezone(zone)
			current_time = datetime.now(timezone).strftime('%Y-%m-%d %H:%M:%S %Z %z')
			await ctx.channel.send(f"**{ctx.author.name}**: {current_time}")
		except pytz.UnknownTimeZoneError:
			await ctx.channel.send(
				f"**{ctx.author.name}**: Unrecognized timezone. Check valid timezones here: <https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568>"
			)

	@commands.command(description='Converts kg to lbs and vice-versa. Usage: `.weight 60kg` or `.weight 130lbs`')
	async def weight(self, ctx, *, weight_str: str = None):
		"""Converts kg to lbs and vice-versa."""
		if not weight_str:
			await ctx.channel.send(f"**{ctx.author.name}:** Please specify a weight.")
			return

		kg_match = re.search(r"(\d+\.?\d*) *[Kk][Gg]", weight_str)
		lbs_match = re.search(r"(\d+\.?\d*) *[Ll][Bb][Ss]", weight_str)

		if kg_match:
			kg = float(kg_match.group(1))
			lbs = round(kg * 2.20462, 2)
			await ctx.channel.send(f"**{ctx.author.name}**: {lbs} lbs")
		elif lbs_match:
			lbs = float(lbs_match.group(1))
			kg = round(lbs / 2.20462, 2)
			await ctx.channel.send(f"**{ctx.author.name}**: {kg} kg")
		else:
			await ctx.channel.send(f"**{ctx.author.name}:** Invalid format. Usage: `.weight 60kg` or `.weight 130lbs`.")

	@commands.command(description='Interact with OpenAI. Usage: `.ai What is Hero Fighter?`', enabled=False, hidden=True)
	async def ai(self, ctx, *, phrase: str = None):
		"""Interact with OpenAI."""
		if not phrase:
			await ctx.channel.send(f"**{ctx.author.name}:** Please provide input for OpenAI.")
			return

		try:
			response = openai.Completion.create(
				engine="text-davinci-003",
				prompt=phrase,
				max_tokens=2000,
				temperature=0.5
			)
			await ctx.channel.send(f"**{ctx.author.name}**: {response.choices[0].text.strip()}")
		except Exception as e:
			await ctx.channel.send(f"Error with OpenAI API: {e}")

	@commands.command(description='Generate an image with OpenAI given a description. Usage: `.ai_img <description>`', enabled=False, hidden=True)
	async def ai_img(self, ctx, *, phrase: str = None):
		"""Generate an image with OpenAI given a description."""
		if not phrase:
			await ctx.channel.send(f"**{ctx.author.name}:** Please provide an image description.")
			return

		num_images = await self.get_user_selection(ctx, "Select number of images to generate:", ["1", "2", "3", "4", "5"])
		if num_images is None:
			return

		image_size = await self.get_user_selection(ctx, "Select the image size:", ["256x256", "512x512", "1024x1024"])
		if image_size is None:
			return

		try:
			response = openai.Image.create(
				prompt=phrase,
				n=int(num_images),
				size=image_size
			)
			for item in response['data']:
				await ctx.channel.send(item['url'])
		except Exception as e:
			await ctx.channel.send(f"**{ctx.author.name}:** Error generating image: {e}")

	async def get_user_selection(self, ctx, prompt, options):
		"""Helper function to create a dropdown for user selection."""
		class DropdownView(discord.ui.View):
			def __init__(self, options):
				super().__init__()
				self.value = None
				self.options = options

			@discord.ui.select(
				options=[discord.SelectOption(label=option) for option in options],
				placeholder="Select an option...",
				min_values=1,
				max_values=1
			)
			async def select_callback(self, select, interaction):
				self.value = select.values[0]
				select.disabled = True
				await interaction.response.edit_message(view=None)
				self.stop()

		view = DropdownView(options)
		message = await ctx.send(prompt, view=view)
		await view.wait()
		await message.delete()
		return view.value


async def setup(client):
	await client.add_cog(Utilities(client))
