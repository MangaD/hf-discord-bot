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


		alreadyIntroduced = False
		eng_general = client.get_channel(english_general_id)
		intro_channel = client.get_channel(introductions_channel)

		try:
			# https://stackoverflow.com/a/63864014/3049315
			intro_messages = await intro_channel.history(limit=None).flatten()
			for msg in intro_messages:
				if member.id == msg.author.id:
					alreadyIntroduced = True
		except discord.Forbidden:
			await eng_general.send("{0}: I do not have permission to read the message history of {1}. :frowning:".format(client.get_user(mangad_id).mention, intro_channel.mention))
		except Exception as e:
			await eng_general.send("Exception thrown: " + str(e))

		if alreadyIntroduced == True:
			await eng_general.send("Welcome back, {0}!".format(member.mention))
		else:
			await eng_general.send("Hello {0}! It would be awesome if you could introduce yourself in {1}. :wink:".format(member.mention, intro_channel.mention))

		# Give Chinese role
		if (re.findall(r'[\u4e00-\u9fff]+', member.name) or re.findall(r'[\u4e00-\u9fff]+', member.nickname)):
			return await member.add_roles(discord.utils.get(member.guild.roles, name="Chinese"), reason="Member's name or nickname contains Chinese characters.")
