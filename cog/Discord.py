from .common import *

import random
import re
import sys
import datetime
from discord.ext import commands

# Store bot start time globally for uptime calculation
START_TIME = datetime.datetime.utcnow()

class Discord(commands.Cog):
	"""Discord related utilities."""

	def __init__(self, client):
		self.client = client

	@commands.command(description="Returns the bot's uptime. Usage: `.uptime`")
	async def uptime(self, ctx):
		"""Calculate and display the bot's uptime."""
		uptime_duration = datetime.datetime.utcnow() - START_TIME
		uptime_str = str(datetime.timedelta(seconds=round(uptime_duration.total_seconds())))
		await ctx.channel.send(f"I've been active for {uptime_str} and still going strong!")

	@commands.command(description="Get a user's avatar image. Usage: `.avatar [nickname]`")
	async def avatar(self, ctx, *, user: discord.Member = None):
		"""Display the avatar of the specified user or the command caller."""
		user = user or ctx.author
		await ctx.send(user.display_avatar.url)

	@avatar.error
	async def avatar_error(self, ctx, error):
		if isinstance(error, commands.MemberNotFound):
			await ctx.channel.send(f"**{ctx.author}:** I could not find that user.")

	@commands.command(description="Get a user's profile banner image. Usage: `.banner [nickname]`")
	async def banner(self, ctx, *, user: discord.Member = None):
		"""Display the banner of the specified user or the command caller."""
		user = user or ctx.author
		banner = getattr(user, "banner", None)
		if banner:
			await ctx.send(banner.url)
		else:
			await ctx.channel.send(f"**{ctx.author.display_name}:** {user.display_name} does not have a banner.")

	@banner.error
	async def banner_error(self, ctx, error):
		if isinstance(error, commands.MemberNotFound):
			await ctx.channel.send(f"**{ctx.author.display_name}:** I could not find that user.")

	@commands.command(description="Get a user's accent color. Usage: `.accent [nickname]`")
	async def accent(self, ctx, *, user: discord.Member = None):
		"""Display the accent color of the specified user or the command caller."""
		user = user or ctx.author
		accent_color = getattr(user, "accent_color", None)
		if accent_color:
			await ctx.channel.send(f"**{user.display_name}'s accent color:** #{accent_color.value:06x}")
		else:
			await ctx.channel.send(f"**{ctx.author.display_name}:** {user.display_name} does not have an accent color.")

	@accent.error
	async def accent_error(self, ctx, error):
		if isinstance(error, commands.MemberNotFound):
			await ctx.channel.send(f"**{ctx.author.display_name}:** I could not find that user.")

	@commands.command(description="Get a user's current status. Usage: `.status [nickname]`")
	async def status(self, ctx, *, user: discord.Member = None):
		"""Display the current status of the specified user or the command caller."""
		user = user or ctx.author
		status_map = {
			discord.Status.online: "Online",
			discord.Status.idle: "Idle",
			discord.Status.dnd: "Do Not Disturb",
			discord.Status.offline: "Offline",
		}
		status_text = status_map.get(getattr(user, "status", None), "Unknown")
		await ctx.channel.send(f"**{user.display_name}'s status:** {status_text}")

	@status.error
	async def status_error(self, ctx, error):
		if isinstance(error, commands.MemberNotFound):
			await ctx.channel.send(f"**{ctx.author.display_name}:** I could not find that user.")

	@commands.command(description="Get a user's current activity. Usage: `.activity [nickname]`")
	async def activity(self, ctx, *, user: discord.Member = None):
		"""Display the current activity of the specified user or the command caller."""
		user = user or ctx.author
		activity = getattr(user, "activity", None)
		activity_text = str(activity) if activity else "No current activity"
		await ctx.channel.send(f"**{user.display_name}'s activity:** {activity_text}")

	@activity.error
	async def activity_error(self, ctx, error):
		if isinstance(error, commands.MemberNotFound):
			await ctx.channel.send(f"**{ctx.author.display_name}:** I could not find that user.")

	@commands.command(aliases=['sicon'], description="Display the server's icon. Usage: `.servericon`")
	async def servericon(self, ctx):
		"""Display the server's icon if available."""
		icon_url = ctx.guild.icon.url if ctx.guild.icon else None
		await ctx.channel.send(icon_url or f"**{ctx.author.display_name}:** This server has no icon.")

	@commands.command(description="Display a custom emoji image. Usage: `.emoji <emoji>`")
	async def emoji(self, ctx, *, emoji_name: str = None):
		"""Display a custom emoji from the server or globally available emojis."""
		if not emoji_name:
			await ctx.channel.send(f"**{ctx.author.display_name}:** Please provide an emoji name or mention.")
			return

		emoji_obj = None
		cleaned_name = emoji_name.strip()

		if cleaned_name.startswith("<") and cleaned_name.endswith(">"):
			match = re.search(r"\d+", cleaned_name)
			if match:
				emoji_obj = self.client.get_emoji(int(match.group(0)))
		elif cleaned_name.startswith(":") and cleaned_name.endswith(":"):
			emoji_obj = discord.utils.get(ctx.guild.emojis, name=cleaned_name.strip(":")) or discord.utils.get(self.client.emojis, name=cleaned_name.strip(":"))
		else:
			emoji_obj = discord.utils.get(ctx.guild.emojis, name=cleaned_name) or discord.utils.get(self.client.emojis, name=cleaned_name)

		if emoji_obj:
			await ctx.send(emoji_obj.url)
		elif len(cleaned_name) == 1 or not cleaned_name.isalnum():
			await ctx.send(cleaned_name)
		else:
			await ctx.channel.send(f"**{ctx.author.display_name}:** I could not find that emoji.")

	@commands.command(aliases=['ricon'], description="Display a role's icon. Usage: `.roleicon [role]`")
	async def roleicon(self, ctx, *, role: discord.Role = None):
		"""Display the icon of the specified role or the command caller's top role."""
		role = role or ctx.author.top_role
		icon = getattr(role, "icon", None)
		if icon:
			await ctx.send(icon.url)
		else:
			await ctx.channel.send(f"**{ctx.author.display_name}:** That role does not have an icon.")

	@commands.command(aliases=['ssplash'], description="Display the server's splash image. Usage: `.ssplash`")
	async def serversplash(self, ctx):
		"""Display the server's splash image if available."""
		splash_url = ctx.guild.splash.url if ctx.guild.splash else None
		await ctx.channel.send(splash_url or f"**{ctx.author.display_name}:** This server has no splash image.")

	@commands.command(aliases=['sbanner'], description="Display the server's banner image. Usage: `.sbanner`")
	async def serverbanner(self, ctx):
		"""Display the server's banner image if available."""
		banner_url = ctx.guild.banner.url if ctx.guild.banner else None
		await ctx.channel.send(banner_url or f"**{ctx.author.display_name}:** This server has no banner image.")

	@commands.command(aliases=['sdsplash'], description="Display the server's discovery splash image. Usage: `.sdsplash`")
	async def serverdiscoverysplash(self, ctx):
		"""Display the server's discovery splash image if available."""
		discovery_splash_url = ctx.guild.discovery_splash.url if ctx.guild.discovery_splash else None
		await ctx.channel.send(discovery_splash_url or f"**{ctx.author.display_name}:** This server has no Discovery splash image.")

	@commands.command(aliases=['sinfo'], description="Display information about the server. Usage: `.sinfo`")
	async def serverinfo(self, ctx):
		"""Display details about the server."""
		guild = ctx.guild
		owner = await guild.fetch_member(guild.owner_id)
		created_at = self.format_discord_timestamp(guild.id)
		features = "\n".join(guild.features) if guild.features else "-"

		embed = discord.Embed(title=guild.name, color=discord.Color.orange())
		embed.set_author(name="Server Info")
		embed.add_field(name="ID", value=guild.id)
		embed.add_field(name="Owner", value=owner)
		embed.add_field(name="Members", value=guild.member_count)
		embed.add_field(name="Text Channels", value=len(guild.text_channels))
		embed.add_field(name="Voice Channels", value=len(guild.voice_channels))
		embed.add_field(name="Created At", value=created_at)
		embed.add_field(name="Locale", value=guild.preferred_locale)
		embed.add_field(name="Roles", value=len(guild.roles) - 1)
		embed.add_field(name="Features", value=features)

		if guild.emojis:
			emoji_list = " ".join(map(str, random.sample(guild.emojis, min(30, len(guild.emojis)))))
			embed.add_field(name=f"Custom Emojis ({len(guild.emojis)})", value=emoji_list[:1020] + "..." if len(emoji_list) > 1020 else emoji_list)

		if guild.icon:
			embed.set_thumbnail(url=guild.icon.url)

		await ctx.channel.send(embed=embed)

	@commands.command(aliases=['cinfo'], description="Display information about a channel. Usage: `.cinfo`")
	async def channelinfo(self, ctx, *, channel: discord.TextChannel = None):
		"""Display details about a specified or current channel."""
		channel = channel or ctx.channel
		created_at = self.format_discord_timestamp(channel.id)
		topic = channel.topic or "No topic set."

		embed = discord.Embed(title=channel.name, description=topic, color=discord.Color.orange())
		embed.add_field(name="ID", value=channel.id)
		embed.add_field(name="Created At", value=created_at)
		embed.add_field(name="Members", value=len(channel.members))

		await ctx.channel.send(embed=embed)

	@channelinfo.error
	async def channelinfo_error(self, ctx, error):
		if isinstance(error, commands.ChannelNotFound):
			await ctx.channel.send(f"**{ctx.author.display_name}:** I could not find that channel.")

	@commands.command(aliases=['uinfo'], description="Display information about a user. Usage: `.uinfo [nickname]`")
	async def userinfo(self, ctx, *, user: discord.Member = None):
		"""Display details about a specified user or the command caller."""
		user = user or ctx.author
		embed = self.create_user_info_embed(user)
		await ctx.channel.send(embed=embed)

	@userinfo.error
	async def userinfo_error(self, ctx, error):
		if isinstance(error, commands.MemberNotFound):
			await ctx.channel.send(f"**{ctx.author.display_name}:** I could not find that user.")
		else:
			await ctx.channel.send(f"**{ctx.author.display_name}:** An error occurred: {error}")

	def create_user_info_embed(self, user: discord.Member) -> discord.Embed:
		"""Helper to create an embed with user information and profile details."""
		joined_at = user.joined_at.strftime("%Y-%m-%d %H:%M") if getattr(user, "joined_at", None) else "N/A"
		created_at = user.created_at.strftime("%Y-%m-%d %H:%M") if getattr(user, "created_at", None) else "N/A"
		roles = ", ".join([str(role) for role in user.roles[1:10]]) if len(user.roles) > 1 else "None"

		status_map = {
			discord.Status.online: "Online",
			discord.Status.idle: "Idle",
			discord.Status.dnd: "Do Not Disturb",
			discord.Status.offline: "Offline",
		}
		status_text = status_map.get(getattr(user, "status", None), "Unknown")
		activity = getattr(user, "activity", None)
		activity_text = str(activity) if activity else "No current activity"
		accent_color = getattr(user, "accent_color", None)
		accent_text = f"#{accent_color.value:06x}" if accent_color else "None"
		banner = getattr(user, "banner", None)

		embed = discord.Embed(title=user.display_name, color=getattr(user, "color", discord.Color.orange()))
		embed.add_field(name="Name", value=f"{user.name}#{user.discriminator}")
		embed.add_field(name="Nickname", value=user.display_name)
		embed.add_field(name="ID", value=user.id)
		embed.add_field(name="Joined Server", value=joined_at)
		embed.add_field(name="Joined Discord", value=created_at)
		embed.add_field(name="Status", value=status_text)
		embed.add_field(name="Activity", value=activity_text)
		embed.add_field(name="Accent Color", value=accent_text)
		embed.add_field(name="Roles", value=f"({len(user.roles) - 1}) - {roles}")

		if user.display_avatar:
			embed.set_thumbnail(url=user.display_avatar.url)

		if banner:
			embed.set_image(url=banner.url)

		return embed

	@commands.command(aliases=['binfo'], description="Display information about the bot. Usage: `.binfo`")
	async def botinfo(self, ctx):
		"""Display details about the bot itself."""
		bot_user = ctx.guild.get_member(self.client.user.id)
		embed = self.create_user_info_embed(bot_user)
		embed.add_field(name="OS", value=sys.platform)
		embed.add_field(name="Python Version", value=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
		embed.add_field(name="Discord.py Version", value=discord.__version__)
		await ctx.channel.send(embed=embed)

	def format_discord_timestamp(self, discord_id: int) -> str:
		"""Format a Discord ID to a readable timestamp."""
		created_at = datetime.datetime(2015, 1, 1, tzinfo=datetime.timezone.utc) + datetime.timedelta(milliseconds=(discord_id >> 22))
		return created_at.strftime("%Y-%m-%d %H:%M")

async def setup(client):
	await client.add_cog(Discord(client))
