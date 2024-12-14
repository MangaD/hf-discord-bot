# Translate
# coding=utf-8
from __future__ import (unicode_literals, absolute_import,
                        print_function, division)

# https://www.geeksforgeeks.org/python-import-from-parent-directory/
import os
import sys
# getting the name of the directory
# where the this file is present.
current = os.path.dirname(os.path.realpath(__file__))
# Getting the parent directory name
# where the current directory is present.
parent = os.path.dirname(current)
# adding the parent directory to
# the sys.path.
sys.path.append(parent)
import config


from .common import *

# mangle, serverinfo
import random
import json
import sys
import requests
from requests import get
from urllib import parse

# UrbanDictionary
from bs4 import BeautifulSoup

# Wikitionary
import re
import html

# Time and timezone
from datetime import datetime
import pytz

### YouTube - Start

import youtube_dl
import urllib
import asyncio

youtube_dl.utils.bug_reports_message = lambda: ''


ytdl_format_options = {
	'format': 'bestaudio', #'bestaudio/best',
	'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
	'restrictfilenames': True,
	'noplaylist': True,
	'nocheckcertificate': True,
	'ignoreerrors': False,
	'logtostderr': False,
	'quiet': True,
	'no_warnings': True,
	'default_search': 'auto',
	'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

# https://stackoverflow.com/questions/61959495/when-playing-audio-the-last-part-is-cut-off-how-can-this-be-fixed-discord-py
ffmpeg_options = {
	'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
	'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
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
		data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

		if 'entries' in data:
			# take first item from a playlist
			data = data['entries'][0]

		filename = data['url'] if stream else ytdl.prepare_filename(data)
		return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

async def disconnectAfterFinished(e=None):
	await MyGlobals.voice.disconnect()
	playing=False
	if e:
		print('Player error: %s' % e);

def searchYT(word):
	# If word is a url, return it
	reg = '^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+$'
	if re.match(reg, word) is not None:
		return word
	query = urllib.parse.quote(word)
	url = "https://www.youtube.com/results?search_query=" + query
	# https://stackoverflow.com/questions/25500563/set-new-cookie-between-requests-with-python-requests
	s = requests.Session()
	r = s.get(url, stream=True)
	s.cookies.set('CONSENT', 'YES+cb.20210530-19-p0.en+FX+267', domain=".youtube.com")
	s.cookies.set('GPS', '1', domain=".youtube.com")
	s.cookies.set('VISITOR_INFO1_LIVE', 'x2hbo4Xe7qE', domain=".youtube.com")
	s.cookies.set('YSC', 'Fstz0Ucts3w', domain=".youtube.com")
	r = s.get(url, stream=True)
	reg = '"url":"\/watch\?v=([^"]+)"'
	vid = None
	for match in re.finditer(reg, r.text):
		vid = match.group(1)
		break
	if vid is None:
		return None
	return 'https://www.youtube.com/watch?v=' + vid

### YouTube - End


mangle_lines = {}

def get_random_lang(long_list, short_list):
	random_index = random.randint(0, len(long_list) - 1)
	random_lang = long_list[random_index]
	if random_lang not in short_list:
		short_list.append(random_lang)
	else:
		return get_random_lang(long_list, short_list)
	return short_list


def translate(text, in_lang='auto', out_lang='en', verify_ssl=True):
	raw = False
	if str(out_lang).endswith('-raw'):
		out_lang = out_lang[:-4]
		raw = True

	headers = {
		'User-Agent': 'Mozilla/5.0' +
		'(X11; U; Linux i686)' +
		'Gecko/20071127 Firefox/2.0.0.11'
	}

	query = {
		"client": "gtx",
		"sl": in_lang,
		"tl": out_lang,
		"dt": "t",
		"q": text,
	}
	url = "http://translate.googleapis.com/translate_a/single"
	result = requests.get(url, params=query, timeout=40, headers=headers,
	                      verify=verify_ssl).text

	if result == '[,,""]':
		return None, in_lang

	while ',,' in result:
		result = result.replace(',,', ',null,')
		result = result.replace('[,', '[null,')

	data = json.loads(result)

	if raw:
		return str(data), 'en-raw'

	try:
		language = data[2]  # -2][0][0]
	except:
		language = '?'

	return ''.join(x[0] for x in data[0]), language



uri = 'http://en.wiktionary.org/w/index.php?title=%s&printable=yes'
r_tag = re.compile(r'<[^>]+>')
r_ul = re.compile(r'(?ims)<ul>.*?</ul>')

def text(html):
	text = r_tag.sub('', html).strip()
	text = text.replace('\n', ' ')
	text = text.replace('\r', '')
	text = text.replace('(intransitive', '(intr.')
	text = text.replace('(transitive', '(trans.')
	return text

def wikt(word):
	bytes = html.unescape(requests.get(uri % urllib.parse.quote(word), stream=True).text)
	bytes = r_ul.sub('', bytes)

	mode = None
	etymology = None
	definitions = {}
	for line in bytes.splitlines():
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
		elif (mode == 'etmyology') and ('<p>' in line):
			etymology = text(line)
		elif (mode is not None) and ('<li>' in line):
			definitions.setdefault(mode, []).append(text(line))
		if '<hr' in line:
			break
	return etymology, definitions

parts = ('preposition', 'particle', 'noun', 'verb',
	'adjective', 'adverb', 'interjection')

def format(result, definitions, number=2):
	for part in parts:
		if part in definitions:
			defs = definitions[part][:number]
			result += u'\n\n**{}**: '.format(part)
			n = ['\n%s. %s' % (i + 1, e.strip(' .')) for i, e in enumerate(defs)]
			result += ', '.join(n)
	return result.strip(' .,')



# Discord integration
class Utilities(commands.Cog):

	"""Useful commands for everyday life.""" # Shows as description in ".help Utilities"

	def __init__(self, client):
		self.client = client

	@commands.command(name='8', description='Ask the magic 8ball a question! Usage: `.8 <question>`')
	async def ball(self, ctx):
		"""Ask the magic 8ball a question! Usage: .8 <question>"""
		messages = ["It is certain"," It is decidedly so","Without a doubt","Yes definitely",
			"You may rely on it","As I see it yes","Most likely","Outlook good","Yes",
			"Signs point to yes","Reply hazy try again","Ask again later","Better not tell you now",
			"Cannot predict now","Concentrate and ask again","Don't count on it","My reply is no",
			"God says no","Very doubtful","Outlook not so good"]
		answer = random.randint(0,len(messages) - 1)
		return await ctx.channel.send(messages[answer]);

	@commands.command(pass_context=True, description='Look up a video on YouTube. Usage: `.yt <search_phrase>`')
	async def yt(self, ctx, *, word : str = None):
		"""Look up a video on YouTube. Usage: `.yt <search_phrase>`"""
		if word is None:
			return await ctx.channel.send('**{0}:** You must tell me what to look up!'.format(ctx.author.name))
		url = searchYT(word)
		if url is None:
			return await ctx.channel.send('**{0}:** Could not find a video.'.format(ctx.author.name))
		return await ctx.channel.send(url)


	@commands.command(pass_context=True, description='Text to speech with optional language hint. Usage: `.tts es`')
	async def tts(self, ctx, *, word : str = None):
		"""Text to speech with optional language hint. Usage: `.tts es`"""
		if not "streamer" in [y.name.lower() for y in ctx.author.roles]:
			return await ctx.channel.send('**{0}:** You do not have permission to use this command.'.format(ctx.author.name))
		global playing
		if playing:
			return await ctx.channel.send('**{0}:** Cannot use TTS with YouTube song!'.format(ctx.author.name))
		if MyGlobals.tts_v:
			await MyGlobals.voice.disconnect()
			MyGlobals.tts_v = False
			MyGlobals.lang = "en"
			return await ctx.channel.send('**{0}:** Stopped TTS.'.format(ctx.author.name))
		try:
			if not ctx.author.voice:
				return await ctx.channel.send('**{0}:** You must join a voice channel!'.format(ctx.author.name))
			MyGlobals.tts_v = True
			if word is None:
				MyGlobals.lang = "en"
			else:
				MyGlobals.lang = word
			if MyGlobals.voice is not None and MyGlobals.voice.is_connected():
				await MyGlobals.voice.disconnect()
			voice_channel = ctx.author.voice.channel
			MyGlobals.voice = await voice_channel.connect()
		except Exception as e:
			MyGlobals.tts_v = False
			MyGlobals.lang = "en"
			MyGlobals.voice = None
			return await ctx.channel.send(str(e))


	# ERROR: No video formats found
	# ^ Upgrade youtube-dl with pip
	@commands.command(pass_context=True, description='Play a YouTube video in voice channel. Usage: `.ytc <search_phrase or url>`')
	async def ytc(self, ctx, *, word : str = None):
		"""Play a YouTube video in voice channel. Usage: `.ytc <search_phrase or url>`"""
		if not "streamer" in [y.name.lower() for y in ctx.author.roles]:
			return await ctx.channel.send('**{0}:** You do not have permission to use this command.'.format(ctx.author.name))
		global voice_channel
		global playing
		if MyGlobals.tts_v:
			return await ctx.channel.send('**{0}:** Cannot play while TTS is on!'.format(ctx.author.name))
		if word is None:
			return await ctx.channel.send('**{0}:** You must tell me what to look up!'.format(ctx.author.name))
		try:
			if not ctx.author.voice:
				return await ctx.channel.send('**{0}:** You must join a voice channel!'.format(ctx.author.name))
			voice_channel = ctx.author.voice.channel
			if MyGlobals.voice is not None and MyGlobals.voice.is_connected() and MyGlobals.voice.channel != voice_channel:
				await MyGlobals.voice.disconnect()

			async with ctx.typing():
				MyGlobals.player = await YTDLSource.from_url(searchYT(word), loop=self.client.loop)
				if MyGlobals.voice is None or not MyGlobals.voice.is_connected():
					MyGlobals.voice = await voice_channel.connect()
				if MyGlobals.voice.is_playing():
					MyGlobals.voice.stop()
				MyGlobals.voice.play(MyGlobals.player)
			await ctx.send('Now playing: {}'.format(MyGlobals.player.title))
			playing = True
		except Exception as e:
			return await ctx.channel.send(str(e))

	@commands.command(pass_context=True, description='Pause / resume audio from voice channel. Usage: `.ytp`')
	async def ytp(self, ctx):
		try:
			if MyGlobals.voice is not None:
				if MyGlobals.voice.is_playing() and not MyGlobals.voice.is_paused():
					await ctx.send('Pausing audio.')
					MyGlobals.voice.pause()
				elif MyGlobals.voice.is_paused():
					await ctx.send('Resuming audio.')
					MyGlobals.voice.resume()
		except Exception as e:
			return await ctx.channel.send(str(e))

	@commands.command(pass_context=True, description='Disconnect from voice channel. Usage: `.ytd`')
	async def ytd(self, ctx):
		"""Disconnect from voice channel."""
		if not "streamer" in [y.name.lower() for y in ctx.author.roles]:
			return await ctx.channel.send('**{0}:** You do not have permission to use this command.'.format(ctx.author.name))
		if MyGlobals.tts_v:
			return await ctx.channel.send('**{0}:** Cannot use with TTS on!'.format(ctx.author.name))
		global playing
		if not playing:
			return await ctx.channel.send('**{0}:** YouTube video is not playing.'.format(ctx.author.name))
		await MyGlobals.voice.disconnect()
		playing = False

	@commands.command(pass_context=True, description='Look up a word on UrbanDictionary. Usage: `.ud <word>`')
	async def ud(self, ctx, *, word : str = None):
		"""Look up a word on UrbanDictionary."""
		if word is None:
			return await ctx.channel.send('**{0}:** You must tell me what to look up!'.format(ctx.author.name))
		r = requests.get("http://www.urbandictionary.com/define.php?term={}".format(word))
		soup = BeautifulSoup(r.content, "html.parser")
		meaning = soup.find("div",attrs={"class":"meaning"})
		if meaning is None:
			return await ctx.channel.send("**{0}:** Couldn't get any definitions for \'%s\'.".format(ctx.author.name) % word)
		meaning = meaning.get_text()
		meaning.replace("&apos", "'")
		try:
			if any(x in meaning.lower() for x in config.bad_words):
				meaning = "*- nsfw -*"
		except NameError:
			pass
		meaning = "**{0}:** ".format(ctx.author.name) + meaning
		if meaning is None:
			return await ctx.channel.send("**{0}:** Couldn't get any definitions for \'%s\'.".format(ctx.author.name) % word)
		elif len(meaning) > 300:
			meaning = meaning[:295] + '[...]'
		await ctx.channel.send(meaning)



	@commands.command(pass_context=True, description='Look up a word on Wiktionary. Usage: `.wt <word>`')
	async def wt(self, ctx, *, word : str = None):
		"""Look up a word on Wiktionary."""
		if word is None:
			return await ctx.channel.send('**{0}:** You must tell me what to look up!'.format(ctx.author.name))

		_etymology, definitions = wikt(word)
		if not definitions:
			return await ctx.channel.send("**{0}:** Couldn't get any definitions for \'%s\'.".format(ctx.author.name) % word)

		word = "**__{}__**".format(word)
		result = format(word, definitions)
		if len(result) < 150:
			result = format(word, definitions, 3)
		if len(result) < 150:
			result = format(word, definitions, 5)
		elif len(result) > 300:
			result = result[:295] + '[...]'
		await ctx.channel.send(result)

	@commands.command(pass_context=True, description='Look up something on Wikipedia. Usage: `.w <phrase>`')
	async def w(self, ctx, *, phrase : str = None):
		"""Look up something on Wikipedia."""

		if phrase is None or phrase.strip() == '':
			return await ctx.channel.send('**{0}:** You must tell me what to look up!'.format(ctx.author.name))

		if (len(phrase) > 2000):
			return await ctx.channel.send('**{0}:** Phrase must be under 2000 characters.'.format(ctx.author.name))

		lang = 'en'
		show_url=True

		msg_array = phrase.split( )
		if msg_array[0].startswith(":"):
			lang = msg_array[0][1:]
			msg_array.pop(0)
			phrase = " ".join(msg_array)

		server = lang + '.wikipedia.org'


		search_url = ('https://%s/w/api.php?format=json&action=query'
			'&list=search&srlimit=%d&srprop=timestamp&srwhat=text'
			'&srsearch=') % (server, 1)
		search_url += phrase

		query = get(search_url).json()

		if 'query' in query:
			query = query['query']['search']
			query_r = [r['title'] for r in query]
			if query_r:
				query = query_r[0]
			else:
				return await ctx.channel.send("**{0}:** Couldn't get any results for \'%s\'.".format(ctx.author.name) % phrase)
		else:
			return await ctx.channel.send("**{0}:** Couldn't get any results for \'%s\'.".format(ctx.author.name) % phrase)

		page_name = query.replace('_', ' ')
		query = urllib.parse.quote(query.replace(' ', '_'))
		try:
			snippet_url = ('https://' + server + '/w/api.php?format=json'
				'&action=query&prop=extracts&exintro&explaintext'
				'&exchars=300&redirects&titles=')
			snippet_url += query
			snippet = get(snippet_url).json()
			snippet = snippet['query']['pages']

			# For some reason, the API gives the page *number* as the key, so we just
			# grab the first page number in the results.
			snippet = snippet[list(snippet.keys())[0]]

			snippet = snippet['extract']
		except KeyError:
			if show_url:
				await ctx.channel.send("[WIKIPEDIA] Error fetching snippet for \"{}\".".format(page_name))
			return
		msg = '[WIKIPEDIA] {} | "{}"'.format(page_name, snippet)
		msg_url = msg + ' | <https://{}/wiki/{}>'.format(server, query)

		if show_url:
			msg = msg_url
		await ctx.channel.send(msg)

	@commands.command(pass_context=True, description='Translates a phrase, with an optional language hint. Usage: `.tr :en :zh <phrase>`')
	async def tr(self, ctx, *, phrase : str = None):
		"""Translates a phrase, with an optional language hint."""

		if phrase is None or phrase.strip() == '':
			return await ctx.channel.send('**{0}:** You need to specify a string for me to translate!'.format(ctx.author.name))

		if (len(phrase) > 2000):
			return await ctx.channel.send('**{0}:** Phrase must be under 2000 characters.'.format(ctx.author.name))

		in_lang = 'auto'
		out_lang = 'en'

		msg_array = phrase.split( )
		if msg_array[0].startswith(":"):
			in_lang = msg_array[0][1:]
			if msg_array[1].startswith(":"):
				out_lang = msg_array[1][1:]
				msg_array.pop(0)
			msg_array.pop(0)
			phrase = " ".join(msg_array)

		if in_lang != out_lang:
			msg, in_lang = translate(phrase, in_lang, out_lang, verify_ssl=True)

			if msg:
				msg = parse.unquote(msg)  # msg.replace('&#39;', "'")
				msg = '"%s" (%s to %s, translate.google.com)' % (msg, in_lang, out_lang)
			else:
				msg = 'The %s to %s translation failed, are you sure you specified valid language abbreviations?' % (in_lang, out_lang)

			await ctx.channel.send("**" + ctx.author.name + ":** " + msg)
		else:
			await ctx.channel.send('**{0}:** Language guessing failed, so try suggesting one!'.format(ctx.author.name))

	@commands.command(pass_context=True, description='Repeatedly translate the input until it makes absolutely no sense. Usage: `.mangle <phrase>`')
	async def mangle(self, ctx, *, phrase : str = None):
		"""Repeatedly translate the input until it makes absolutely no sense."""
		global mangle_lines
		long_lang_list = ['fr', 'de', 'es', 'it', 'no', 'he', 'la', 'ja', 'cy', 'ar', 'yi', 'zh', 'nl', 'ru', 'fi', 'hi', 'af', 'jw', 'mr', 'ceb', 'cs', 'ga', 'sv', 'eo', 'el', 'ms', 'lv']
		lang_list = []
		for __ in range(0, 8):
			lang_list = get_random_lang(long_lang_list, lang_list)
		random.shuffle(lang_list)
		if phrase is None:
			if MyGlobals.last_message is None:
				return await ctx.channel.send('**{0}:** What do you want me to mangle?'.format(ctx.author.name))
			else:
				phrase = (MyGlobals.last_message.strip(), '')
		else:
			phrase = (phrase.strip(), '')
		if phrase[0] == '':
			return await ctx.channel.send('**{0}:** What do you want me to mangle?'.format(ctx.author.name))

		for lang in lang_list:
			backup = phrase
			try:
				phrase = translate(phrase[0], 'en', lang, True)
			except:
				phrase = False
			if not phrase:
				phrase = backup
				break

			try:
				phrase = translate(phrase[0], lang, 'en', True)
			except:
				phrase = backup
				continue

			if not phrase:
				phrase = backup
				break
		return await ctx.channel.send('**{0}:** '.format(ctx.author.name) + phrase[0])

	@commands.command(pass_context=True, description='Get the time in a specific timezone. Usage: `.time Asia/Hong_Kong`')
	async def time(self, ctx, *, zone : str = None):
		"""Get the time in a specific timezone."""
		dateFormat = '%Y-%m-%d %H:%M:%S %Z %z'
		try:
			return await ctx.channel.send('**{0}**: {1}'.format(ctx.author.name, datetime.now(pytz.utc if zone is None else pytz.timezone(zone)).strftime(dateFormat)))
		except pytz.exceptions.UnknownTimeZoneError:
			return await ctx.channel.send('**{0}**: Timezone not recognized. You may find a list of timezones here: <https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568>'.format(ctx.author.name))

def setup(client):
	client.add_cog(Utilities(client))
