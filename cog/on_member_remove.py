from .common import *

@client.event
async def on_member_remove(member: discord.Member):
	"""Handle when a member leaves the server."""
	# Fetch the notification channel
	notification_channel = client.get_channel(NOTIFICATIONS_CHANNEL_ID)

	# Create an embed for the member leave event
	embed = discord.Embed(
		title="Member Left",
		description=f"**{member.name}** has left the server.",
		color=discord.Color.dark_red()
	)
	embed.set_thumbnail(url=member.display_avatar.url)
	embed.add_field(name="Username", value=f"{member.name}#{member.discriminator}", inline=True)
	embed.add_field(name="Joined At", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
	embed.set_footer(text="Goodbye!", icon_url=ICON_URL)

	# Send the embed to the notification channel
	await notification_channel.send(embed=embed)
