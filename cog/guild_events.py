from .common import *

@client.event
async def on_guild_channel_create(channel: discord.abc.GuildChannel):
	"""Log channel creation events."""
	notification_channel = client.get_channel(NOTIFICATIONS_CHANNEL_ID)

	embed = discord.Embed(
		title="Channel Created",
		description=f"A new channel was created: {channel.mention}",
		color=discord.Color.green()
	)
	embed.add_field(name="Channel Type", value=channel.type, inline=True)
	embed.add_field(name="Channel ID", value=channel.id, inline=True)
	embed.set_footer(text="Channel Creation", icon_url=ICON_URL)
	await notification_channel.send(embed=embed)


@client.event
async def on_guild_channel_update(before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
	"""Log channel update events."""
	notification_channel = client.get_channel(NOTIFICATIONS_CHANNEL_ID)

	embed = discord.Embed(
		title="Channel Updated",
		description=f"Channel {before.mention} was updated.",
		color=discord.Color.gold()
	)
	embed.add_field(name="Channel Type", value=before.type, inline=True)
	embed.add_field(name="Channel ID", value=before.id, inline=True)
	
	# Detect changes in channel name
	if before.name != after.name:
		embed.add_field(name="Name Before", value=before.name, inline=True)
		embed.add_field(name="Name After", value=after.name, inline=True)
	
	# Detect changes in channel topic (for text channels only)
	if isinstance(before, discord.TextChannel) and before.topic != after.topic:
		embed.add_field(name="Topic Before", value=before.topic or "None", inline=False)
		embed.add_field(name="Topic After", value=after.topic or "None", inline=False)
	
	embed.set_footer(text="Channel Update", icon_url=ICON_URL)
	await notification_channel.send(embed=embed)


@client.event
async def on_guild_channel_delete(channel: discord.abc.GuildChannel):
	"""Log channel deletion events."""
	notification_channel = client.get_channel(NOTIFICATIONS_CHANNEL_ID)

	embed = discord.Embed(
		title="Channel Deleted",
		description=f"The channel **{channel.name}** was deleted.",
		color=discord.Color.red()
	)
	embed.add_field(name="Channel Type", value=channel.type, inline=True)
	embed.add_field(name="Channel ID", value=channel.id, inline=True)
	embed.set_footer(text="Channel Deletion", icon_url=ICON_URL)
	await notification_channel.send(embed=embed)
