from .common import *
from discord.ext import commands

class NoHFGuild(commands.CheckFailure):
	pass

def hf_guild_only() -> commands.check:
	async def predicate(ctx: commands.Context) -> bool:
		if ctx.guild is None or ctx.guild.id != HF_GUILD_ID:
			raise NoHFGuild(f"**{ctx.author.name}:** This command can only be used in the Hero Fighter server.")
		return True
	return commands.check(predicate)
