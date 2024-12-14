from .common import *

import random # serverinfo
import sys # botinfo
import datetime # Uptime, serverinfo

starttime = datetime.datetime.utcnow()

class Discord(commands.Cog):

	"""Discord related utilities.""" # Shows as description in ".help Discord"

	def __init__(self, client):
		self.client = client

	@commands.command(description='Returns the uptime of HF Bot. Usage: `.uptime`')
	async def uptime(self, ctx):
		"""Returns the uptime of HF Bot."""
		delta = datetime.timedelta(seconds=round((datetime.datetime.utcnow() - starttime).total_seconds()))
		return await ctx.channel.send("I've been sitting here for {} and I keep going!".format(delta))

		# https://stackoverflow.com/questions/59799987/how-to-get-a-users-avatar-with-their-id-in-discord-py
	@commands.command(description="Get the avatar image of a user. Usage: `.avatar nickname`. If the user's nickname has spaces, use quotation marks around it.")
	async def avatar(self, ctx, *,  user: discord.Member = None):
		"""Get the avatar image of a user. Usage: `.avatar nickname`. If the user's nickname has spaces, use quotation marks around it."""
		user = user or ctx.author
		await ctx.send(user.display_avatar)

	@avatar.error
	async def avatar_error(self, ctx, error):
		if isinstance(error, commands.errors.MemberNotFound):
			return await ctx.channel.send('**{0}:** I could not find that user.'.format(ctx.author))

	@commands.command(aliases=['ssplash'], pass_context=True, description='Display the server splash image. Usage: `.ssplash`')
	async def serversplash(self, ctx):
		if ctx.channel.guild.splash:
			return await ctx.channel.send(ctx.channel.guild.splash.url)
		else:
			return await ctx.channel.send('**{0}:** There is no splash image on this server.'.format(ctx.author.name))

	@commands.command(aliases=['sbanner'], pass_context=True, description='Display the server banner image. Usage: `.sbanner`')
	async def serverbanner(self, ctx):
		if ctx.channel.guild.banner:
			return await ctx.channel.send(ctx.channel.guild.banner.url)
		else:
			return await ctx.channel.send('**{0}:** There is no banner image on this server.'.format(ctx.author.name))

	@commands.command(aliases=['sdsplash'], pass_context=True, description='Display the server discovery splash image. Usage: `.sdsplash`')
	async def serverdiscoverysplash(self, ctx):
		if ctx.channel.guild.discovery_splash:
			return await ctx.channel.send(ctx.channel.guild.discovery_splash.url)
		else:
			return await ctx.channel.send('**{0}:** There is no Discovery splash image on this server.'.format(ctx.author.name))

	# https://gitlab.com/Kwoth/nadekobot/-/blob/1.9/NadekoBot.Core/Modules/Utility/InfoCommands.cs
	# https://discordpy.readthedocs.io/en/stable/api.html#discord.Guild
	@commands.command(aliases=['sinfo'], pass_context=True, description='Display info about the server. Usage: `.sinfo`')
	async def serverinfo(self, ctx):
		"""Display info about the server."""
		guild = ctx.channel.guild
		ownername = await guild.fetch_member(guild.owner_id)
		text_channel_count = len(guild.text_channels)
		voice_channel_count = len(guild.voice_channels)
		created_at = datetime.datetime(2015, 1, 1, 0, 0, 0, 0, tzinfo=datetime.timezone.utc) + datetime.timedelta(milliseconds=(guild.id >> 22))
		created_at = created_at.strftime("%Y-%m-%d %H:%M")
		features = "-"
		if guild.features:
			features = "\n".join(str(f) for f in guild.features)
		embed = discord.Embed(title = guild.name, colour = discord.Colour.orange())
		embed.set_author(name="Server info")
		embed.add_field(name="ID", value=guild.id, inline=True)
		embed.add_field(name="Owner", value=ownername, inline=True)
		embed.add_field(name="Members", value=guild.member_count, inline=True)
		embed.add_field(name="Text channels", value=text_channel_count, inline=True)
		embed.add_field(name="Voice channels", value=voice_channel_count, inline=True)
		embed.add_field(name="Created at", value=created_at, inline=True)
		embed.add_field(name="Region", value=guild.region, inline=True)
		embed.add_field(name="Roles", value=len(guild.roles)-1, inline=True)
		embed.add_field(name="Features", value=features, inline=True)
		if guild.emojis:
			emoji_list = list(str(e) for e in guild.emojis)
			random.shuffle(emoji_list)
			emoji_list = emoji_list[:30] if len(emoji_list) > 30 else emoji_list
			emoji_list = " ".join(str(f) for f in emoji_list)
			emoji_list = (emoji_list[:1020] + '...') if len(emoji_list) > 1020 else emoji_list
			embed.add_field(name="Custom emojis(" + str(len(guild.emojis)) + ")", value=emoji_list, inline=True)
		if guild.icon:
			embed.set_thumbnail(url=guild.icon.url)
		#embed.set_image(url=guild.splash_url)
		await ctx.channel.send(embed=embed)


	@commands.command(aliases=['cinfo'], pass_context=True, description='Display info about a channel. Usage: `.cinfo`')
	async def channelinfo(self, ctx, *,  channel : discord.TextChannel=None):
		"""Display info about a channel."""
		channel = channel or ctx.channel
		created_at = datetime.datetime(2015, 1, 1, 0, 0, 0, 0, tzinfo=datetime.timezone.utc) + datetime.timedelta(milliseconds=(channel.id >> 22))
		created_at = created_at.strftime("%Y-%m-%d %H:%M")
		topic = channel.topic if channel.topic else ""
		embed = discord.Embed(title = channel.name, description = topic, colour = discord.Colour.orange())
		embed.add_field(name="ID", value=channel.id, inline=True)
		embed.add_field(name="Created at", value=created_at, inline=True)
		embed.add_field(name="Members", value=len(channel.members), inline=True)
		#embed.add_field(name="News", value=("Yes" if channel.is_news() else "No"), inline=True)
		#embed.add_field(name="NSFW", value=("Yes" if channel.is_nsfw() else "No"), inline=True)
		await ctx.channel.send(embed=embed)

	@channelinfo.error
	async def channelinfo_error(self, ctx, error):
		if isinstance(error, commands.errors.ChannelNotFound):
			return await ctx.channel.send('**{0}:** I could not find that channel.'.format(ctx.author.name))


	@commands.command(aliases=['uinfo'], pass_context=True, description="Display info about a user. Usage: `.uinfo nickname`. If the user's nickname has spaces, use quotation marks around it.")
	async def userinfo(self, ctx, *,  user : discord.Member=None):
		"""Display info about a user. Usage: `.uinfo nickname`. If the user's nickname has spaces, use quotation marks around it."""
		if user is None:
			user = ctx.author
		embed = self.create_user_info_embed(user)
		await ctx.channel.send(embed=embed)

	@userinfo.error
	async def userinfo_error(self, ctx, error):
		if isinstance(error, commands.errors.MemberNotFound):
			return await ctx.channel.send('**{0}:** I could not find that user.'.format(ctx.author.name))
		else:
			return await ctx.channel.send('**{0}:** Got exception: {}'.format(ctx.author.name, error))

	def create_user_info_embed(self, user: discord.Member):
		joined_at = user.joined_at.strftime("%Y-%m-%d %H:%M")
		created_at = user.created_at.strftime("%Y-%m-%d %H:%M")
		roles = list(str(e) for e in user.roles)
		roles = roles[:10] if len(roles) > 10 else roles
		roles = ", ".join(str(r) for r in roles)
		roles = (roles[:1020] + '...') if len(roles) > 1020 else roles
		embed = discord.Embed(colour = user.color)
		embed.add_field(name="Name", value="**{0}**#{1}".format(user.name, str(user.discriminator)), inline=True)
		if user.display_name is not None:
			embed.add_field(name="Nickname", value=user.display_name, inline=True)
		embed.add_field(name="ID", value=user.id, inline=True)
		embed.add_field(name="Joined server", value=joined_at, inline=True)
		embed.add_field(name="Joined discord", value=created_at, inline=True)
		embed.add_field(name="Roles", value="**(" + str(len(user.roles)) + ")** - " + roles, inline=True)
		if user.display_avatar:
			embed.set_thumbnail(url=user.display_avatar)
		return embed

	@commands.command(aliases=['binfo'], pass_context=True, description="Display info about the bot. Usage: `.binfo`.")
	async def botinfo(self, ctx):
		"""Display info about the bot. Usage: `.binfo`."""
		user = [member for member in ctx.guild.members if client.user.id == member.id][0]
		embed = self.create_user_info_embed(user)
		embed.add_field(name="OS", value = sys.platform)
		python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
		embed.add_field(name="Python version", value = python_version)
		embed.add_field(name="Discord.py version", value = discord.__version__)
		await ctx.channel.send(embed=embed)

def setup(client):
	client.add_cog(Discord(client))
