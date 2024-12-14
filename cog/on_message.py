from .common import *
import re

### TTS - Start

from gtts import gTTS
from io import BytesIO
import io
import re
import asyncio
from .utils.FFmpegPCMAudioGTTS import FFmpegPCMAudioGTTS

media_only_channels = [
	media_channel,
	artwork_channel,
	hf_memes_channel,
	memes_channel
]

media_url_regexps = [
	"((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?", # youtube
	"https?:\/\/.*\/.*\.(png|gif|webp|jpeg|jpg)\??.*", # image
	"https:\/\/(?:www\.)?deviantart.com\/.+" # deviantart
]

def mentionsToNicks(msg):
	str = msg.content
	#print (str)
	p = re.compile(r'\<@\!?([0-9]{18})\>')
	for m in re.findall(p, str):
		nick = msg.server.get_member(m).nick
		if nick is None:
			nick = msg.server.get_member(m).name
		str = str.replace("<@" + m + ">", nick)
		str = str.replace("<@!" + m + ">", nick)
	return str

def removeEmojis(str):
	p = re.compile(r'\<:(.*?)([0-9]{18})\>')
	str = p.sub('', str)
	return str

def replaceLink(str):
        p = re.compile(r'https?:\/\/.*?[ \t\r\n]')
        str = p.sub('url ', str)
        return str

async def tts_f(message, client):
	if not MyGlobals.tts_v:
		return
	if not message.content:
		return
	try:
		msg = mentionsToNicks(message)
		msg = removeEmojis(msg)
		msg = replaceLink(msg)
		#print(msg.encode('utf-8'))
		tts_o = gTTS(text=msg, lang=MyGlobals.lang, slow=False)
		while(MyGlobals.voice.is_playing()): pass
		mp3_fp = BytesIO()
		tts_o.write_to_fp(mp3_fp)
		mp3_fp.seek(0)
		#MyGlobals.player = discord.FFmpegPCMAudio(mp3_fp, pipe=True)
		MyGlobals.player = FFmpegPCMAudioGTTS(mp3_fp.read(), pipe=True)
		MyGlobals.voice.play(MyGlobals.player)
	except discord.InvalidArgument as ia:
		return await message.channel.send('**{0}:** You must join a voice channel!'.format(message.author.name))
	except io.UnsupportedOperation as up:
		return await message.channel.send('**{0}:** \'discord.FFmpegPCMAudio\' might have given a \'io.UnsupportedOperation\' exception: {1}'.format(message.author.name, up))
	except ValueError as ve:
		return await message.channel.send('**{0}:** Language \'{1}\' not supported.'.format(message.author.name, MyGlobals.lang))
	except Exception as e:
		return await message.channel.send(str(e))

### TTS - End



@client.event
async def on_message(message):

	#print (message.content.lower())

	hf_bot_pattern = re.compile("^(" + re.escape(client.user.name) + "|" + re.escape(client.user.mention) + ")[ \n\t\r]*!+$", re.IGNORECASE)
	# we do not want the bot to reply to itself
	if message.author == client.user:
		return
	# @HF Bot
	if (message.content.lower() == "<@!{}>".format(client.user.id)):
		await message.channel.send('What?!')
		return
	# HF Bot!
	elif (hf_bot_pattern.match(message.content) is not None):
		msg = '{0.author.mention}!'.format(message)
		await message.channel.send(msg)
		return
	# Hello/Hi HF Bot
	elif (message.content.lower().startswith("hello {}".format(client.user.name).lower())
		or message.content.lower().startswith("hello <@!{}>".format(client.user.id))
		or message.content.lower().startswith("hi {}".format(client.user.name).lower())
                or message.content.lower().startswith("hi <@!{}>".format(client.user.id))
		):
		msg = 'Hello {0.author.mention}'.format(message)
		await message.channel.send(msg)
		return
	# Who's daddy?
	elif (message.content.lower() == "who's daddy?"):
		await message.channel.send(client.get_user(mangad_id).mention)
		return
	# Give that man a cookie
	elif ("give that man a cookie" in message.content.lower()):
		await message.channel.send("http://orteil.dashnet.org/cookieclicker/")
		return
	elif ("bow to me" in message.content.lower() and message.author.mention == client.get_user(mangad_id).mention):
		await message.channel.send('_bows to {0}_'.format(message.author.mention))
		return

	# No swearing
	#if any(word in message.content.lower() for word in p.swearing):
	#	await message.channel.send("https://imgur.com/a/qcWud");

	if not message.content.startswith(bot_prefix):
		MyGlobals.last_message = message.content

	# TTS
	await tts_f(message, client)

	# Remove text messages in #media
	if (message.channel.id in media_only_channels) and (len(message.attachments) == 0 and not any(re.compile(r).match(message.content) for r in media_url_regexps)):
		try:
			await message.delete()
			#await message.channel.send('Text messages are not allowed in this channel. If you wish to comment on a picture you may create a thread.'.format(message))
		except discord.Forbidden:
			await message.channel.send("{0}: I do not have permission to remove this nuisance. :frowning:".format(client.get_user(mangad_id).mention))
		except:
			pass
		return

	if (message.channel.id == introductions_channel and await hasAlreadyIntroduced(message.author)):
		try:
			await message.delete()
			response = await message.channel.send(f"{message.author.mention}: You have already introduced yourself. You may edit your introduction, but not send a new message. You may create a thread under someone's introduction message if you wish to reply to it.")
			asyncio.create_task(delete_after_delay(response, delay=15))
		except discord.Forbidden:
			await message.channel.send("{0}: I do not have permission to remove this nuisance. :frowning:".format(client.get_user(mangad_id).mention))
		except:
			pass
		return

	await client.process_commands(message)
