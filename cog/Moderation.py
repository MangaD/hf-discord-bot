import re
from .common import *
from .checks import *
from discord.ext import commands
import sqlite3
import asyncio


class Moderation(commands.Cog):
	"""Commands restricted to moderators."""

	def __init__(self, client):
		self.client = client

	@commands.command(
		description=(
			"Saves all users to the local database.\n"
			"Usage: `.saveusers`\n"
		)
	)
	@hf_guild_only()
	@commands.has_permissions(administrator=True)  # Restrict to Administrators
	async def saveusers(self, ctx):

		# Check if user using the command has administrator permissions
		if not ctx.author.guild_permissions.administrator:
			await ctx.channel.send(f"**{ctx.author.display_name}:** You lack permission to use this command. :angry:")
			return

		# Check if the bot has permission to access members
		if not ctx.guild.me.guild_permissions.view_audit_log:  # Proxy for member access
			await ctx.send("I don't have permission to view member data!")
			return

		try:
			# Connect to SQLite database (creates file if it doesn't exist)
			conn = sqlite3.connect(MyGlobals.db.FILE_NAME)
			cursor = conn.cursor()

			# Clear existing data for this guild to avoid duplicates
			cursor.execute('DELETE FROM users WHERE guild_id = ?', (ctx.guild.id,))

			# Fetch all members in the guild
			member_count = 0
			async for member in ctx.guild.fetch_members(limit=None):
				# Skip the bot itself
				if member == ctx.guild.me:
					continue

				# Get role IDs (excluding @everyone)
				role_ids = [str(role.id) for role in member.roles if role != ctx.guild.default_role]
				roles_str = ','.join(role_ids) if role_ids else ''

				# Insert user data into the table
				cursor.execute('''
					INSERT INTO users (user_id, username, display_name, nick, guild_id, roles)
					VALUES (?, ?, ?, ?, ?, ?)
				''', (member.id, str(member), member.display_name, member.nick, ctx.guild.id, roles_str))
				member_count += 1

			# Commit changes and close connection
			conn.commit()
			conn.close()

			await ctx.send(f"Successfully saved information for {member_count} users to the database.")
		except discord.Forbidden:
			await ctx.send("I lack the permissions to access member data!")
		except sqlite3.Error as e:
			await ctx.send(f"An error occurred with the database: {e}")
		except Exception as e:
			await ctx.send(f"An unexpected error occurred: {e}")


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
	@commands.has_permissions(manage_roles=True)
	async def bandit(self, ctx, user: discord.Member = None, *, reason: str = "No reason given."):
		"""Assign or remove the 'Bandit' role to/from a user, even on rejoining."""

		# Check if user using the command has moderator permissions
		if not ctx.author.guild_permissions.manage_roles:
			await ctx.channel.send(f"**{ctx.author.display_name}:** You lack permission to use this command. :angry:")
			return

		# Check if the bot has permission to manage roles
		if not ctx.guild.me.guild_permissions.manage_roles:
			await ctx.send("I don't have permission to manage roles!")
			return

		# Ensure user parameter is provided
		if user is None:
			await ctx.channel.send(f"**{ctx.author.display_name}:** Please specify a user to assign the 'Bandit' role to.")
			return

		# Check if the bot's top role is higher than the member's highest role
		if user.top_role >= ctx.guild.me.top_role:
			await ctx.send("I can't manage roles for this user because their highest role is above or equal to mine!")
			return

		# Find the bandit role
		bandit_role = discord.utils.get(user.guild.roles, name="Bandit")
		if not bandit_role:
			await ctx.send("The 'Bandit' role does not exist in this server!")
			return

		# Check if the bot can manage the Bandit role
		if bandit_role.position >= ctx.guild.me.top_role.position:
			await ctx.send("I can't manage a role that's higher than or equal to my highest role!")
			return

		try:
			# Toggle the 'Bandit' role
			action = "remove" if bandit_role in user.roles else "add"
			await self.toggle_bandit_role(ctx, user, bandit_role, reason, action)
		except discord.Forbidden:
			await ctx.channel.send(f"{ctx.author.mention}: I lack permission to manage roles.")
		except discord.HTTPException:
			await ctx.channel.send(f"{ctx.author.mention}: An error occurred while trying to modify roles.")
		except Exception as e:
			await ctx.channel.send(f"An error occurred: {e}")

	async def toggle_bandit_role(self, ctx, user: discord.Member, bandit_role: discord.Role, reason: str, action: str):
		"""Add or remove the 'Bandit' role from a user based on the action specified."""
		if action == "remove":
			# If using temporary memory:
			# Restore saved roles and remove Bandit role
			#saved_roles = [ctx.guild.get_role(role_id) for role_id in MyGlobals.user_roles[user.id]]
			# Filter out None roles (in case a role was deleted)
			#saved_roles = [role for role in saved_roles if role is not None]
			#await user.edit(roles=saved_roles, reason=reason)
			#del MyGlobals.user_roles[user.id]  # Remove from dictionary

			await user.remove_roles(bandit_role, reason=reason)
		else:
			# If using temporary memory:
			# Save current roles, remove all roles, and add Bandit role
			#MyGlobals.user_roles[user.id] = [role.id for role in user.roles if role != ctx.guild.default_role]
			#await user.edit(roles=[bandit_role], reason=reason)

			# Remove all roles from the member
			await user.edit(roles=[])
			await user.add_roles(bandit_role, reason=reason)

	@bandit.error
	async def bandit_error(self, ctx, error):
		"""Error handler for the 'bandit' command."""
		if isinstance(error, commands.MemberNotFound):
			await ctx.channel.send(f"**{ctx.author.display_name}:** User not found. :thinking:")
		elif isinstance(error, NoHFGuild):
			await ctx.channel.send(error)
		else:
			await ctx.channel.send(f"An unexpected error occurred: {error}")

async def setup(client):
	await client.add_cog(Moderation(client))
