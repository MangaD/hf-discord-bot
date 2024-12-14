from .common import *
import re
import asyncio
from gtts import gTTS
from io import BytesIO
from .utils.FFmpegPCMAudioGTTS import FFmpegPCMAudioGTTS

media_only_channels = [
	MEDIA_CHANNEL_ID,
	ARTWORK_CHANNEL_ID,
	HF_MEMES_CHANNEL_ID,
	MEMES_CHANNEL_ID
]

media_url_patterns = [
	r"(?:https?:\/\/)?(?:www|m\.)?(youtube\.com|youtu.be)\/[\w\-]+",  # YouTube
	r"https?:\/\/.*\.(png|gif|webp|jpeg|jpg)\??.*",				   # Images
	r"https:\/\/(?:www\.)?deviantart.com\/.+"						 # DeviantArt
]

def mentions_to_nicks(msg):
	"""Convert mentions to nicknames in the given message content."""
	text = msg.content
	mention_pattern = re.compile(r'<@!?(\d{18})>')

	for user_id in mention_pattern.findall(text):
		member = msg.guild.get_member(int(user_id))
		nickname = member.nick if member and member.nick else member.name
		text = text.replace(f"<@{user_id}>", nickname).replace(f"<@!{user_id}>", nickname)
	return text

def remove_emojis(text):
	"""Remove custom Discord emojis from the given text."""
	return re.sub(r'<:\w+:\d{18}>', '', text)

def replace_links(text):
	"""Replace URLs in the given text with 'url'."""
	return re.sub(r'https?:\/\/\S+', 'url', text)

async def tts_f(message, client):
	"""Convert message text to speech and play it in the voice channel."""
	if not MyGlobals.tts_enabled or not message.content:
		return

	try:
		text = replace_links(remove_emojis(mentions_to_nicks(message)))
		tts_obj = gTTS(text=text, lang=MyGlobals.language, slow=False)
		mp3_fp = BytesIO()
		tts_obj.write_to_fp(mp3_fp)
		mp3_fp.seek(0)

		while MyGlobals.voice_client.is_playing():
			await asyncio.sleep(0.1)

		MyGlobals.audio_player = FFmpegPCMAudioGTTS(mp3_fp.read(), pipe=True)
		MyGlobals.voice_client.play(MyGlobals.audio_player)
	except discord.InvalidArgument:
		await message.channel.send(f"**{message.author.name}:** You need to join a voice channel first!")
	except io.UnsupportedOperation as e:
		await message.channel.send(f"**{message.author.name}:** An error occurred with TTS playback: {e}")
	except ValueError:
		await message.channel.send(f"**{message.author.name}:** Language '{MyGlobals.language}' not supported.")
	except Exception as e:
		await message.channel.send(f"Unexpected error: {e}")

@client.event
async def on_message(message):
	"""Handle incoming messages and trigger specific responses or actions."""
	if message.author == client.user:
		return

	hf_bot_pattern = re.compile(fr"^(?:{re.escape(client.user.name)}|{re.escape(client.user.mention)})[ \n\t\r]*!+$", re.IGNORECASE)

	if message.content.lower() == f"<@!{client.user.id}>":
		await message.channel.send("What?!")
	elif hf_bot_pattern.match(message.content):
		await message.channel.send(f"{message.author.mention}!")
	elif any(message.content.lower().startswith(greeting) for greeting in [f"hello {client.user.name}", f"hi {client.user.name}"]):
		await message.channel.send(f"Hello {message.author.mention}")
	elif message.content.lower() == "who's daddy?":
		await message.channel.send(client.get_user(MANGAD_ID).mention)
	elif "give that man a cookie" in message.content.lower():
		await message.channel.send("http://orteil.dashnet.org/cookieclicker/")
	elif "bow to me" in message.content.lower() and message.author.id == MANGAD_ID:
		await message.channel.send(f"_bows to {message.author.mention}_")

	if not message.content.startswith(BOT_PREFIX):
		MyGlobals.last_message = message.content

	await tts_f(message, client)

	if message.channel.id in media_only_channels:
		if len(message.attachments) == 0 and not any(re.search(pattern, message.content) for pattern in media_url_patterns):
			try:
				await message.delete()
				await message.channel.send(
					f"{message.author.mention}, text messages are not allowed here. Please comment via threads if needed.",
					delete_after=15
				)
			except discord.Forbidden:
				await message.channel.send(f"{client.get_user(MANGAD_ID).mention}: I lack permission to delete messages in this channel.")

	if message.channel.id == INTRODUCTIONS_CHANNEL_ID:
		if await has_already_introduced(message.author, message):
			try:
				await message.delete()
				response = await message.channel.send(
					f"{message.author.mention}, you've already introduced yourself. Edit your existing introduction or create a thread to reply.",
					delete_after=15
				)
			except discord.Forbidden:
				await message.channel.send(f"{client.get_user(MANGAD_ID).mention}: I lack permission to delete messages in the introductions channel.")

	await client.process_commands(message)
