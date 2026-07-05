from .common import *
import re
import asyncio
import io
from gtts import gTTS
from io import BytesIO
from .utils.FFmpegPCMAudioGTTS import FFmpegPCMAudioGTTS
from collections import defaultdict
from time import time
from discord.ext import tasks

media_only_channels = [
	MEDIA_CHANNEL_ID,
	ARTWORK_CHANNEL_ID,
	AI_ART_CHANNEL_ID,
	HF_MEMES_CHANNEL_ID,
	MEMES_CHANNEL_ID
]

media_url_patterns = [
	r"(?:https?:\/\/)?(?:www|m\.)?(youtube\.com|youtu.be)\/[\w\-]+", # YouTube
	r"https?:\/\/.*\.(png|gif|webp|jpeg|jpg)\??.*",                  # Images
	r"https:\/\/(?:www\.)?deviantart.com\/.+"                        # DeviantArt
]

# Anti-spam tracking: {user_id: [(message_content, guild_id, channel_id, timestamp), ...]}
user_message_history = defaultdict(list)

@tasks.loop(seconds=15)
async def cleanup_old_messages():
	"""Periodically remove message records older than their guild's configured retention window."""
	try:
		current_time = time()
		for user_id in list(user_message_history.keys()):
			#print(f"cleanup_old_messages {user_id}")
			filtered_entries = []
			for content, guild_id, channel_id, ts in user_message_history[user_id]:
				guild_settings = MyGlobals.db.get_guild_settings(guild_id)
				window_seconds = min(guild_settings.get("spam_window_seconds", 15), 15)
				if current_time - ts < window_seconds:
					filtered_entries.append((content, guild_id, channel_id, ts))
			user_message_history[user_id] = filtered_entries
			if not user_message_history[user_id]:
				del user_message_history[user_id]
	except asyncio.CancelledError:
		pass

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

def get_spam_fingerprint(message):
	"""Create a stable fingerprint for spam detection."""
	text = message.content.strip().lower() if message.content else ""
	if message.attachments:
		attachment_sigs = "|".join(sorted([f"{att.size}_{att.filename.split('.')[-1]}" for att in message.attachments])).lower()
		return f"{text}|{attachment_sigs}" if text else attachment_sigs
	return text

async def check_cross_channel_spam(message):
	"""Detect and handle cross-channel spam."""
	if not message.guild:
		return False

	# Ignore bot messages and commands
	if message.author == client.user or message.content.startswith(BOT_PREFIX):
		return False

	settings = MyGlobals.db.get_guild_settings(message.guild.id)
	if not settings.get("spam_enabled", 1):
		return False

	current_time = time()
	user_id = message.author.id
	msg_content = get_spam_fingerprint(message)

	window_seconds = min(settings.get("spam_window_seconds", 15), 15)

	# Add current message to tracking
	user_message_history[user_id].append((msg_content, message.guild.id, message.channel.id, current_time))

	# Check for spam using guild-configured window and trigger count
	recent_messages = [
		(content, guild_id, channel_id, ts)
		for content, guild_id, channel_id, ts in user_message_history[user_id]
		if guild_id == message.guild.id and current_time - ts <= window_seconds
	]

	message_channels = defaultdict(set)
	for content, guild_id, channel_id, _ in recent_messages:
		if content == msg_content and guild_id == message.guild.id:
			message_channels[content].add(channel_id)

	trigger_count = settings.get("spam_trigger_channel_count", 3)
	if msg_content in message_channels and len(message_channels[msg_content]) >= trigger_count:
		await handle_spam(message, msg_content, settings)
		return True
	return False

async def handle_spam(message, msg_content, settings):
	"""Handle spam violation using per-guild settings.
	Notify the staff channel with details of the action taken.
	"""
	spam_messages = []
	stripped_roles = []
	action_taken = "No action taken"

	try:
		member = message.guild.get_member(message.author.id)
		if member:
			stripped_roles = [role.name for role in member.roles if role != message.guild.default_role]

			bandit_role_name = settings.get("bandit_role_name", "Bandit")
			bandit_role = discord.utils.get(message.guild.roles, name=bandit_role_name)
			penalty = settings.get("spam_penalty", "bandit")
			joined_recently = False

			if member.joined_at:
				joined_recently = (
					discord.utils.utcnow() - member.joined_at
				).total_seconds() <= settings.get("spam_recent_join_seconds", 259200)

			if penalty == "ban":
				await member.ban(reason="Anti-spam violation: cross-channel spam detected", delete_message_days=0)
				action_taken = "Banned from server"
			elif penalty == "ban_recent" and joined_recently:
				await member.ban(reason="Anti-spam violation: recent account anti-spam violation", delete_message_days=0)
				action_taken = "Banned from server"
			elif penalty == "kick" or (penalty == "kick_recent" and joined_recently):
				await member.kick(reason="Anti-spam violation: cross-channel spam detected")
				action_taken = "Kicked from server"
			elif bandit_role:
				await member.edit(roles=[bandit_role], reason="Anti-spam violation: cross-channel spam detected")
				action_taken = f"Roles stripped and {bandit_role.name} role applied"
			else:
				await member.edit(roles=[], reason="Anti-spam violation: cross-channel spam detected")
				action_taken = "Roles stripped"
	except discord.Forbidden:
		pass
	except Exception:
		pass

	# Search all text and voice channels for spam messages from the user with matching fingerprint
	try:
		for channel in list(message.guild.text_channels) + list(message.guild.voice_channels):
			try:
				async for msg in channel.history(limit=10, oldest_first=False):
					if (
						msg.author.id == message.author.id and
						get_spam_fingerprint(msg) == msg_content
					):
						spam_messages.append(msg)
						try:
							await msg.delete()
						except discord.Forbidden:
							pass
						except discord.NotFound:
							pass
			except discord.Forbidden:
				pass
			except discord.NotFound:
				pass
	except Exception:
		pass

	# Send staff notification
	await notify_staff(message, msg_content, len(spam_messages), stripped_roles, action_taken, settings)

async def notify_staff(message, msg_content, message_count, stripped_roles=None, action_taken="Roles stripped and Bandit role applied", settings=None):
	"""Send a notification to the staff channel."""
	stripped_roles = stripped_roles or []
	try:
		staff_channel = None
		if settings is not None:
			staff_channel_id = settings.get("staff_channel_id")
			if staff_channel_id:
				staff_channel = message.guild.get_channel(staff_channel_id)
		if not staff_channel:
			staff_channel = client.get_channel(STAFF_CHANNEL_ID)
		if staff_channel:
			embed = discord.Embed(
				title="🚨 Cross-Channel Spam Detected",
				description=f"User {message.author.mention} posted the same message in {settings.get('spam_trigger_channel_count', 3)}+ channels within {settings.get('spam_window_seconds', 15)} seconds.",
				color=discord.Color.red()
			)
			embed.add_field(name="User", value=f"{message.author} (ID: {message.author.id})", inline=False)
			embed.add_field(name="Spam Messages Deleted", value=str(message_count), inline=True)
			embed.add_field(name="Action Taken", value=action_taken, inline=True)
			embed.add_field(name="Roles Stripped", value=(', '.join(stripped_roles) if stripped_roles else 'None'), inline=False)
			embed.add_field(name="Message Preview", value=f"```{msg_content[:100]}```", inline=False)
			
			await staff_channel.send(embed=embed)
	except discord.Forbidden:
		pass
	except Exception:
		pass

async def tts_f(message):
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

	# Check for cross-channel spam - if detected, exit early
	if message.guild and await check_cross_channel_spam(message):
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

	await tts_f(message)

	if (
		message.channel.id in media_only_channels
		and message.type != discord.MessageType.thread_created
		#and message.channel.type not in (
		#	discord.ChannelType.public_thread,
		#	discord.ChannelType.private_thread,
		#	discord.ChannelType.news_thread,
		#)
	):
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
