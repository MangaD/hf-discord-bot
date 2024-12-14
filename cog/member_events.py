from .common import *
import re
from datetime import datetime, timedelta

@client.event
async def on_member_remove(member: discord.Member):
	"""Log when a member leaves or is kicked."""

	if member.guild.id != HF_GUILD_ID:
		return

	notification_channel = client.get_channel(NOTIFICATIONS_CHANNEL_ID)

	# Define a short time window for detecting recent kicks (e.g., 5 seconds)
	time_threshold = timedelta(seconds=5)

	# Get the current time in UTC
	now = datetime.utcnow()

	# Check if the member was kicked by fetching audit logs
	async for entry in member.guild.audit_logs(action=discord.AuditLogAction.kick, limit=1):
		if entry.target.id == member.id and (now - entry.created_at) <= time_threshold:
			embed = discord.Embed(
				title="Member Kicked",
				description=f"{member.mention} was kicked from the server.",
				color=discord.Color.orange()
			)
			embed.set_thumbnail(url=member.display_avatar.url)
			embed.add_field(name="Username", value=f"{member.name}#{member.discriminator}", inline=True)
			embed.add_field(name="Joined At", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
			embed.add_field(name="Kicked By", value=entry.user.mention, inline=True)
			embed.add_field(name="Reason", value=entry.reason or "No reason provided", inline=False)
			embed.set_footer(text="Kick Notification", icon_url=ICON_URL)
			await notification_channel.send(embed=embed)
			return  # Exit the function to avoid sending a "Member Left" message

	# If not kicked, log as a regular member leave
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


@client.event
async def on_member_ban(guild: discord.Guild, user: discord.User):
	"""Log member ban events."""

	if member.guild.id != HF_GUILD_ID:
		return

	notification_channel = client.get_channel(NOTIFICATIONS_CHANNEL_ID)

	# Fetch the audit log entry to identify who banned the user and the reason
	async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=1):
		if entry.target.id == user.id:
			embed = discord.Embed(
				title="Member Banned",
				description=f"{user.mention} was banned from the server.",
				color=discord.Color.red()
			)
			embed.set_thumbnail(url=user.display_avatar.url)
			embed.add_field(name="Username", value=f"{user.name}#{user.discriminator}", inline=True)
			embed.add_field(name="Joined At", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
			embed.add_field(name="Banned By", value=entry.user.mention, inline=True)
			embed.add_field(name="Reason", value=entry.reason or "No reason provided", inline=False)
			embed.set_footer(text="Ban Notification", icon_url=ICON_URL)
			await notification_channel.send(embed=embed)
			break


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

	# Assign the "Bandit" role if the user is in the muted users list
	if member.id in MyGlobals.muted_user_ids:
		await assign_role(member, "Bandit", "Muted member rejoined the server.")
		return

	# Greet the member in the English General channel
	eng_general = client.get_channel(ENGLISH_GENERAL_ID)
	intro_channel = client.get_channel(INTRODUCTIONS_CHANNEL_ID)
	if await has_already_introduced(member):
		await eng_general.send(f"Welcome back, {member.mention}!")
	else:
		await eng_general.send(f"Hello {member.mention}! Please introduce yourself in {intro_channel.mention}. :wink:")

	# Assign the "Chinese" role if the member’s name or nickname contains Chinese characters
	if contains_chinese_characters(member.name) or (member.nick and contains_chinese_characters(member.nick)):
		await assign_role(member, "Chinese", "Member's name or nickname contains Chinese characters.")

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

	# Print a summary to the console
	log_message = (
		f"Member Update - {before.name}#{before.discriminator}\n"
		f"Nickname: {before.nick} -> {after.nick}\n"
		f"Roles Added: {[role.name for role in added_roles]}\n"
		f"Roles Removed: {[role.name for role in removed_roles]}\n"
	)
	# Uncomment to log in the console if needed
	# print(log_message)
