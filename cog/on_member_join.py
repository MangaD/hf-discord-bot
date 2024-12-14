from .common import *

# Bandit role is given on join for the user ids in this list
muted_users_ids = [

];

@client.event
async def on_member_join(member):
	if member.guild.id == hf_guild_id:
		# Give ban role to user on join
		if member.id in MyGlobals.muted_users_ids:
			bandit_role = discord.utils.get(member.guild.roles, name="Bandit")
			return await member.add_roles(bandit_role, reason="Muted member tried to rejoin")

		eng_general = client.get_channel(english_general_id)
		intro_channel = client.get_channel(introductions_channel)

		if await hasAlreadyIntroduced(member):
			await eng_general.send(f"Welcome back, {member.mention}!")
		else:
			await eng_general.send(f"Hello {member.mention}! It would be awesome if you could introduce yourself in {intro_channel.mention}. :wink:")

		# Give Chinese role
		if re.search(r'[\u4e00-\u9fff]+', member.name) or (member.nick and re.search(r'[\u4e00-\u9fff]+', member.nick)):
			chinese_role = discord.utils.get(member.guild.roles, name="Chinese")
			return await member.add_roles(chinese_role, reason="Member's name or nickname contains Chinese characters.")
