from .common import *

class NoHFGuild(commands.CheckFailure):
	pass

def hf_guild_only():
	async def predicate(ctx):
		if ctx.author.guild.id != hf_guild_id:
			raise NoHFGuild("**{0}:** This command is for using in the Hero Fighter server only.".format(ctx.author.name))
		return True
	return commands.check(predicate)

