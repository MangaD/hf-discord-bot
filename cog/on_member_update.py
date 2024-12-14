from .common import *

@client.event
async def on_member_update(before: discord.Member, after: discord.Member):
	"""Handle updates to a member's status, roles, or nickname."""
	# Fetch the notification channel
	notification_channel = client.get_channel(NOTIFICATIONS_CHANNEL_ID)

	# Log nickname changes
	if before.nick != after.nick:
		old_nick = before.nick or before.name
		new_nick = after.nick or after.name
		embed = discord.Embed(
			title="Nickname Change",
			description=f"**{before.name}** changed their nickname",
			color=discord.Color.blue()
		)
		embed.add_field(name="Before", value=old_nick, inline=True)
		embed.add_field(name="After", value=new_nick, inline=True)
		embed.set_thumbnail(url=before.display_avatar.url)
		await notification_channel.send(embed=embed)

	# Log role additions
	added_roles = [role for role in after.roles if role not in before.roles]
	if added_roles:
		added_roles_str = ", ".join([role.name for role in added_roles])
		embed = discord.Embed(
			title="Role Added",
			description=f"**{before.name}** was given new role(s)",
			color=discord.Color.green()
		)
		embed.add_field(name="Added Roles", value=added_roles_str, inline=False)
		embed.set_thumbnail(url=before.display_avatar.url)
		await notification_channel.send(embed=embed)

	# Log role removals
	removed_roles = [role for role in before.roles if role not in after.roles]
	if removed_roles:
		removed_roles_str = ", ".join([role.name for role in removed_roles])
		embed = discord.Embed(
			title="Role Removed",
			description=f"**{before.name}** had role(s) removed",
			color=discord.Color.red()
		)
		embed.add_field(name="Removed Roles", value=removed_roles_str, inline=False)
		embed.set_thumbnail(url=before.display_avatar.url)
		await notification_channel.send(embed=embed)

	# Print a summary to the console
	log_message = (
		f"Member Update - {before.name}#{before.discriminator}\n"
		f"Nickname: {before.nick} -> {after.nick}\n"
		f"Roles Added: {[role.name for role in added_roles]}\n"
		f"Roles Removed: {[role.name for role in removed_roles]}\n"
	)
	# Uncomment to log in the console if needed
	# print(log_message)
