import re
from .common import *
from .checks import *
from discord.ext import commands
from discord import Forbidden

class Moderation(commands.Cog):
	"""Commands restricted to moderators."""

	def __init__(self, client):
		self.client = client

	@commands.command(
		description=(
			"Gives or removes the 'Bandit' role from a user, preventing or allowing rejoining privileges. "
			"Accepts the user's name (or tag) and an optional reason.\n"
			"Usage: `.bandit UserX [optional reason]`\n"
			"Example: `.bandit UserX You are breaking the rules.`\n"
			"If the user's nickname contains spaces, enclose it in quotation marks."
		)
	)
	@hf_guild_only()
	async def bandit(self, ctx, user: discord.Member = None, *, reason: str = "No reason given."):
		"""Assign or remove the 'Bandit' role to/from a user, even on rejoining."""

		# Check for moderator permissions
		if not ctx.author.guild_permissions.manage_roles:
			await ctx.channel.send(f"**{ctx.author.name}:** You lack permission to use this command. :angry:")
			return

		# Ensure user parameter is provided
		if user is None:
			await ctx.channel.send(f"**{ctx.author.name}:** Please specify a user to assign the 'Bandit' role to.")
			return

		bandit_role = discord.utils.get(user.guild.roles, name="Bandit")

		try:
			# Toggle the 'Bandit' role
			action = "remove" if bandit_role in user.roles else "add"
			await self.toggle_bandit_role(user, bandit_role, reason, action)

			# Update muted users list
			if user.id in MyGlobals.muted_user_ids:
				MyGlobals.muted_user_ids.remove(user.id)
			else:
				MyGlobals.muted_user_ids.append(user.id)

		except Forbidden:
			await ctx.channel.send(f"{ctx.author.mention}: I lack permission to manage roles.")
		except Exception as e:
			await ctx.channel.send(f"An error occurred: {e}")

	async def toggle_bandit_role(self, user: discord.Member, bandit_role: discord.Role, reason: str, action: str):
		"""Add or remove the 'Bandit' role from a user based on the action specified."""
		if action == "remove":
			await user.remove_roles(bandit_role, reason=reason)
		else:
			await user.add_roles(bandit_role, reason=reason)

	@bandit.error
	async def bandit_error(self, ctx, error):
		"""Error handler for the 'bandit' command."""
		if isinstance(error, commands.MemberNotFound):
			await ctx.channel.send(f"**{ctx.author.name}:** User not found. :thinking:")
		elif isinstance(error, NoHFGuild):
			await ctx.channel.send(error)
		else:
			await ctx.channel.send(f"An unexpected error occurred: {error}")

async def setup(client):
	await client.add_cog(Moderation(client))
