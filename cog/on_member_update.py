from .common import *

@client.event
async def on_member_update(before: discord.Member, after: discord.Member):
	"""Handle updates to a member's status, roles, or nickname."""
	# Fetch the notification channel
	notification_channel = client.get_channel(NOTIFICATIONS_CHANNEL_ID)

	# Log status changes
	#if before.status != after.status:
	#	await notification_channel.send(f"**{before.name}** is now **{after.status}**.")

	# Log nickname changes
	if before.nick != after.nick:
		old_nick = before.nick or before.name
		new_nick = after.nick or after.name
		await notification_channel.send(f"**{before.name}** changed their nickname from **{old_nick}** to **{new_nick}**.")

	# Log role additions and removals
	added_roles = [role for role in after.roles if role not in before.roles]
	removed_roles = [role for role in before.roles if role not in after.roles]

	if added_roles:
		added_roles_str = ", ".join([role.name for role in added_roles])
		await notification_channel.send(f"**{before.name}** was given the role(s): **{added_roles_str}**.")
	
	if removed_roles:
		removed_roles_str = ", ".join([role.name for role in removed_roles])
		await notification_channel.send(f"**{before.name}** had the role(s) **{removed_roles_str}** removed.")

	# Print a summary to the console
	log_message = (
		f"Member Update - {before.name}#{before.discriminator}\n"
		f"Status: {before.status} -> {after.status}\n"
		f"Nickname: {before.nick} -> {after.nick}\n"
		f"Roles Added: {[role.name for role in added_roles]}\n"
		f"Roles Removed: {[role.name for role in removed_roles]}\n"
	)
	#print(log_message)
