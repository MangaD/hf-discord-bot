from .common import *
from .checks import *

import re

class Moderation(commands.Cog): # Class shows as category in ".help" command

	"""For moderators only."""

	def __init__(self, client):
		self.client = client

	@commands.command(pass_context=True,
		description="""Gives the \'Bandit\' role to a user, even if he rejoins the server. Receives the user\'s name (or tag) and an optional reason.\n
			E.g. `.bandit UserX You are breaking the rules.`\n
			To undo, run the command again. If the user's nickname has spaces, use quotation marks around it.
			""") # description appears when using ".help bandit"
	@hf_guild_only()
	async def bandit(self, ctx, user : discord.Member=None, *, reason : str = None):

		"""Gives the \'Bandit\' role to a user, even if he rejoins the server. Receives the user's name (or tag) and an optional reason.\n
		E.g. `.bandit UserX You are breaking the rules.`\n
		To undo, run the command again. If the user's nickname has spaces, use quotation marks around it.
		""" # Appears in ".help"

		can_manage_roles = ctx.author.guild_permissions.manage_roles
		if can_manage_roles == False:
			return await ctx.channel.send("**{0}:** You do not have permission to use this command. :angry:".format(ctx.author.name))

		if user is None:
			return await ctx.channel.send("**{0}:** You did not give me a user to punish.".format(ctx.author.name))

		if reason is None:
			reason = "No reason given."

		bandit_role = discord.utils.get(user.guild.roles, name="Bandit")

		try:
			if bandit_role in user.roles:
				await user.remove_roles(bandit_role, reason=reason)
			else:
				await user.add_roles(bandit_role, reason=reason)
		except Forbidden:
			return await eng_general.send("{0}: I do not have permission to manage roles. :frowning:".format(client.get_user(mangad_id).mention))
		except Exception as e:
			return await eng_general.send("Exception thrown: " + e)

		if user.id in MyGlobals.muted_users_ids:
			MyGlobals.muted_users_ids.remove(user.id)
		else:
			MyGlobals.muted_users_ids.append(user.id)

	@bandit.error
	async def bandit_error(self, ctx, error):
		if isinstance(error, commands.errors.MemberNotFound):
			return await ctx.channel.send('**{0}:** I could not find that user. :thinking:'.format(ctx.author.name))
		elif isinstance(error, NoHFGuild):
			return await ctx.channel.send(error)


async def setup(client):
        await client.add_cog(Moderation(client))
