from .common import *

# Bandit role is given on join for the user ids in this list
muted_users_ids = [

];

@client.event
async def on_member_join(member):
	if member.guild.id == hf_guild_id:
		# Give ban role to user on join
		if member.id in MyGlobals.muted_users_ids:
			return await member.add_roles(discord.utils.get(member.guild.roles, name="Bandit"), reason="Muted member tried to rejoin")

		if await hasAlreadyIntroduced(member) == True:
			await eng_general.send("Welcome back, {0}!".format(member.mention))
		else:
			await eng_general.send("Hello {0}! It would be awesome if you could introduce yourself in {1}. :wink:".format(member.mention, intro_channel.mention))

		# Give Chinese role
		if (re.findall(r'[\u4e00-\u9fff]+', member.name) or re.findall(r'[\u4e00-\u9fff]+', member.nick)):
			return await member.add_roles(discord.utils.get(member.guild.roles, name="Chinese"), reason="Member's name or nickname contains Chinese characters.")
