from .common import *
import re

@client.event
async def on_member_join(member):
	"""Handle events when a member joins the server."""
	if member.guild.id != HF_GUILD_ID:
		return  # Exit if the member is not joining the Hero Fighter guild

	# Assign the "Bandit" role if the user is in the muted users list
	if member.id in MyGlobals.muted_user_ids:
		await assign_role(member, "Bandit", "Muted member rejoined the server.")
		return

	# Greet the member in the English General channel
	eng_general = client.get_channel(english_general_id)
	intro_channel = client.get_channel(introductions_channel)
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
