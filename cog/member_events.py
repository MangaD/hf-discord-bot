from .common import *
import re
from datetime import datetime, timedelta, timezone

@client.event
async def on_member_remove(member: discord.Member):
	"""Log when a member leaves, is kicked, or is banned."""

	if member.guild.id != HF_GUILD_ID:
		return  # Exit if the member is not joining the Hero Fighter guild

	notification_channel = client.get_channel(NOTIFICATIONS_CHANNEL_ID)
	time_threshold = timedelta(seconds=5)  # Time window for detecting kicks/bans
	now = datetime.now(timezone.utc)  # Use timezone-aware datetime

	# Check the audit logs for a recent ban or kick action
	async for entry in member.guild.audit_logs(limit=5):
		if entry.target.id == member.id and (now - entry.created_at) <= time_threshold:
			if entry.action == discord.AuditLogAction.ban:
				# Log as a ban
				embed = discord.Embed(
					title="Member Banned",
					description=f"{member.mention} was banned from the server.",
					color=discord.Color.red()
				)
				embed.set_thumbnail(url=member.display_avatar.url)
				embed.add_field(name="Username", value=f"{member.name}#{member.discriminator}", inline=True)
				embed.add_field(name="Banned By", value=entry.user.mention, inline=True)
				embed.add_field(name="Reason", value=entry.reason or "No reason provided", inline=False)
				embed.set_footer(text="Ban Notification", icon_url=ICON_URL)
				await notification_channel.send(embed=embed)
				return
			elif entry.action == discord.AuditLogAction.kick:
				# Log as a kick
				embed = discord.Embed(
					title="Member Kicked",
					description=f"{member.mention} was kicked from the server.",
					color=discord.Color.orange()
				)
				embed.set_thumbnail(url=member.display_avatar.url)
				embed.add_field(name="Username", value=f"{member.name}#{member.discriminator}", inline=True)
				embed.add_field(name="Kicked By", value=entry.user.mention, inline=True)
				embed.add_field(name="Reason", value=entry.reason or "No reason provided", inline=False)
				embed.set_footer(text="Kick Notification", icon_url=ICON_URL)
				await notification_channel.send(embed=embed)
				return

	# If no ban or kick is found, log as a regular member leave
	embed = discord.Embed(
		title="Member Left",
		description=f"{member.mention} has left the server.",
		color=discord.Color.dark_red()
	)
	embed.set_thumbnail(url=member.display_avatar.url)
	embed.add_field(name="Username", value=f"{member.name}#{member.discriminator}", inline=True)
	embed.add_field(name="Joined At", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
	embed.set_footer(text="Goodbye!", icon_url=ICON_URL)

	await notification_channel.send(embed=embed)

	# Do not remove the user from the database when he leaves, se we can restore his roles (e.g. Bandit)
	#await MyGlobals.db.remove_user_from_db(member.id, member.guild.id)


@client.event
async def on_member_join(member):
	"""Handle events when a member joins the server."""

	if member.guild.id != HF_GUILD_ID:
		return  # Exit if the member is not joining the Hero Fighter guild

	"""Log member join events."""
	notification_channel = client.get_channel(NOTIFICATIONS_CHANNEL_ID)

	embed = discord.Embed(
		title="Member Joined",
		description=f"Welcome {member.mention} to the server!",
		color=discord.Color.green()
	)
	embed.set_thumbnail(url=member.display_avatar.url)
	embed.add_field(name="Username", value=f"{member.name}#{member.discriminator}", inline=True)
	embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
	embed.set_footer(text="New Member", icon_url=ICON_URL)

	await notification_channel.send(embed=embed)

	# Old code when using temporary memory to save the bandit role
	# Assign the "Bandit" role if the user is in the muted users list
	#if member.id in MyGlobals.user_roles:
	#	await assign_role(member, "Bandit", "Muted member rejoined the server.")
	#	return

	# Greet the member in the 'welcome' channel
	welcome_channel = client.get_channel(WELCOME_CHANNEL_ID)
	intro_channel = client.get_channel(INTRODUCTIONS_CHANNEL_ID)
	if await has_already_introduced(member):
		await welcome_channel.send(f"Welcome back, {member.mention}!")
	else:
		await welcome_channel.send(f"Hello {member.mention}! Please introduce yourself in {intro_channel.mention}. :wink:")

	# Assign the "Chinese" role if the member’s name or nickname contains Chinese characters
	if contains_chinese_characters(member.name) or (member.nick and contains_chinese_characters(member.nick)):
		await assign_role(member, "Chinese", "Member's name or nickname contains Chinese characters.")

	try:
		# Attempt to restore user if he exists in the database
		if not await MyGlobals.db.restore_user_data(member):
			# Add user to the database if he did not exist there
			await MyGlobals.db.update_user_in_db(member.id, str(member), member.display_name, member.nick, member.guild.id, member.roles)
	except discord.Forbidden:
		await notification_channel(f"Missing permissions to edit roles/nickname for {member} in guild {member.guild.id}")
	except sqlite3.Error as e:
		await notification_channel(f"Database error for {member} in guild {member.guild.id}: {e}")
	except discord.HTTPException as e:
		await notification_channel(f"Discord API error for {member} in guild {member.guild.id}: {e}")


async def assign_role(member, role_name, reason):
	"""Assign a role to a member with error handling."""
	role = discord.utils.get(member.guild.roles, name=role_name)
	if role:
		try:
			await member.add_roles(role, reason=reason)
		except discord.Forbidden:
			log.error(f"Insufficient permissions to assign the '{role_name}' role to {member}.")
		except discord.HTTPException as e:
			log.error(f"Failed to assign the '{role_name}' role to {member}: {e}")

def contains_chinese_characters(text):
	"""Check if a given text contains Chinese characters."""
	return bool(re.search(r'[\u4e00-\u9fff]+', text))


@client.event
async def on_member_update(before: discord.Member, after: discord.Member):
	"""Handle updates to a member's status, roles, or nickname."""

	if before.guild.id != HF_GUILD_ID:
		return

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

	# Check if roles or nickname changed
	if before.roles != after.roles or before.nick != after.nick:

		# Don't let bandit assign roles for himself
		bandit_role = discord.utils.get(after.guild.roles, name="Bandit")

		# If user still has bandit role, then remove any roles he just added
		if bandit_role in after.roles and await MyGlobals.db.has_role(after.id, after.guild.id, "Bandit"):
			try:
				await after.edit(roles=[bandit_role], reason="Bandit is not allowed to change roles")
				#print(f"Attempted to change roles: {before.roles} --- {after.roles}")
			except discord.Forbidden:
				print(f"Missing permissions to edit roles for {after} in guild {guild.id}")
				return
			except discord.HTTPException as e:
				print(f"Discord API error for {after} in guild {guild.id}: {e}")
				return
		else:
			await MyGlobals.db.update_user_in_db(after.id, str(after), after.display_name, after.nick, after.guild.id, after.roles)

	# Print a summary to the console
	log_message = (
		f"Member Update - {before.name}#{before.discriminator}\n"
		f"Nickname: {before.nick} -> {after.nick}\n"
		f"Roles Added: {[role.name for role in added_roles]}\n"
		f"Roles Removed: {[role.name for role in removed_roles]}\n"
	)
	# Uncomment to log in the console if needed
	# print(log_message)


@client.event
async def on_user_update(before: discord.Member, after: discord.Member):
	if before.bot:
		return
	if before.name != after.name or before.discriminator != after.discriminator or before.global_name != after.global_name:
		await MyGlobals.db.update_user_global_name(after.id, str(after), after.display_name)

