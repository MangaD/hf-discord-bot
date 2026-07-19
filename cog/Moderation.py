import re
from .common import *
from .checks import *
from discord.ext import commands
import sqlite3
import asyncio
import aiohttp


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

	@commands.group(
		invoke_without_command=True,
		description=(
			"View or configure per-guild cross-channel spam settings."
		)
	)
	@commands.has_permissions(administrator=True)
	async def spamconfig(self, ctx):
		"""Display detailed help for the cross-channel anti-spam system."""

		if ctx.guild is None:
			await ctx.send("This command can only be used in a server.")
			return

		embed = discord.Embed(
			title="Cross-Channel Spam Configuration",
			description=(
				"This system detects users who post the same message in multiple "
				"channels within a short period of time.\n\n"
				"When a violation is detected, matching recent messages are deleted, "
				"the configured penalty is applied, and a report is sent to the "
				"configured staff channel."
			),
			color=discord.Color.blue()
		)

		embed.add_field(
			name="Commands",
			value=(
				"`​.​spamconfig show`\n"
				"Shows the server's current anti-spam configuration.\n\n"
				"`​.​spamconfig set <option> <value>`\n"
				"Changes one configuration option.\n\n"
				"`​.​spamconfig reset`\n"
				"Restores all anti-spam options to their defaults."
			),
			inline=False
		)

		embed.add_field(
			name="How detection works",
			value=(
				"1. The bot records each non-command message sent by a user.\n"
				"2. It checks whether the same message was posted in different channels.\n"
				"3. The messages must be sent within `window_seconds`.\n"
				"4. The number of distinct channels must reach `trigger_count`.\n"
				"5. Matching recent messages are deleted and the penalty is applied.\n\n"
				"Repeated messages in only one channel do not trigger this "
				"cross-channel detector."
			),
			inline=False
		)

		embed.add_field(
			name="`enabled`",
			value=(
				"Turns cross-channel spam detection on or off.\n"
				"Accepted values: `on`, `off`, `yes`, `no`, `true`, `false`, `1`, `0`\n"
				"Default: `on`\n"
				"Example: `.spamconfig set enabled on`"
			),
			inline=False
		)

		embed.add_field(
			name="`staff_channel`",
			value=(
				"The channel where spam reports are sent.\n"
				"Accepts a channel mention, channel ID, or exact channel name.\n"
				"Default: not configured\n"
				"Examples:\n"
				"`.spamconfig set staff_channel #staff-log`\n"
				"`.spamconfig set staff_channel staff-log`"
			),
			inline=False
		)

		embed.add_field(
			name="`trigger_count`",
			value=(
				"The number of different channels containing the same message "
				"required to trigger the detector.\n"
				"Must be a positive whole number.\n"
				"Default: `3`\n"
				"Example: `.spamconfig set trigger_count 3`"
			),
			inline=False
		)

		embed.add_field(
			name="`window_seconds`",
			value=(
				"The time period during which matching cross-channel messages count "
				"toward a violation.\n"
				"Accepted range: `1` to `15` seconds\n"
				"Default: `15`\n"
				"Example: `.spamconfig set window_seconds 10`"
			),
			inline=False
		)

		embed.add_field(
			name="`penalty`",
			value=(
				"Controls what happens when cross-channel spam is detected.\n\n"
				"`bandit` — Applies the configured Bandit role. If no valid Bandit "
				"role is configured, the user is timed out for 24 hours.\n\n"
				"`kick` — Always kicks the user.\n\n"
				"`kick_recent` — Kicks users who joined recently. Other users receive "
				"the Bandit role, or a 24-hour timeout if that role is unavailable.\n\n"
				"`ban` — Always bans the user.\n\n"
				"`ban_recent` — Bans users who joined recently. Other users receive "
				"the Bandit role, or a 24-hour timeout if that role is unavailable.\n\n"
				"Default: `bandit`\n"
				"Example: `.spamconfig set penalty kick_recent`"
			),
			inline=False
		)

		embed.add_field(
			name="`bandit_role`",
			value=(
				"The role applied by the `bandit` penalty and as the fallback for "
				"`kick_recent` or `ban_recent` when the user is not considered recent.\n"
				"The user's existing assignable roles are replaced by this role.\n"
				"Accepts a role mention, role ID, or exact role name.\n"
				"Default: not configured\n"
				"Examples:\n"
				"`.spamconfig set bandit_role @Bandit`\n"
				"`.spamconfig set bandit_role Bandit`"
			),
			inline=False
		)

		embed.add_field(
			name="`recent_join_seconds`",
			value=(
				"Defines how long after joining a user is considered recent for "
				"`kick_recent` and `ban_recent`.\n"
				"Must be a positive whole number.\n"
				"Default: `259200` seconds, which is 3 days.\n"
				"Examples:\n"
				"`.spamconfig set recent_join_seconds 86400` — 1 day\n"
				"`.spamconfig set recent_join_seconds 604800` — 7 days"
			),
			inline=False
		)

		embed.add_field(
			name="Recommended setup",
			value=(
				"```text\n"
				".spamconfig set staff_channel #staff-log\n"
				".spamconfig set bandit_role @Bandit\n"
				".spamconfig set trigger_count 3\n"
				".spamconfig set window_seconds 15\n"
				".spamconfig set penalty kick_recent\n"
				".spamconfig set recent_join_seconds 259200\n"
				".spamconfig set enabled on\n"
				"```"
			),
			inline=False
		)

		embed.set_footer(
			text="Administrators only • Use `.spamconfig show` to view the values currently active in this server."
		)

		await ctx.send(embed=embed)

	@spamconfig.command(name="show")
	@commands.has_permissions(administrator=True)
	async def spamconfig_show(self, ctx):
		if ctx.guild is None:
			await ctx.send("This command can only be used in a server.")
			return
		if not ctx.author.guild_permissions.administrator:
			await ctx.send(f"**{ctx.author.display_name}:** You must be a server administrator to use this command.")
			return

		settings = MyGlobals.db.get_guild_settings(ctx.guild.id)
		staff_channel = None
		if settings.get("staff_channel_id"):
			staff_channel = ctx.guild.get_channel(settings["staff_channel_id"])

		bandit_role_id = settings.get("bandit_role_id")
		bandit_role = ctx.guild.get_role(int(bandit_role_id)) if bandit_role_id else None

		embed = discord.Embed(
			title="Guild Spam Configuration",
			color=discord.Color.blue()
		)
		embed.add_field(name="Enabled", value="Yes" if settings.get("spam_enabled", 1) else "No", inline=True)
		embed.add_field(name="Staff Channel", value=staff_channel.mention if staff_channel else "Not configured", inline=True)
		embed.add_field(name="Bandit Role", value=bandit_role.mention if bandit_role else "Not configured", inline=True)
		embed.add_field(name="Trigger Count", value=str(settings.get("spam_trigger_channel_count", 3)), inline=True)
		embed.add_field(name="Window Seconds", value=str(settings.get("spam_window_seconds", 15)), inline=True)
		embed.add_field(name="Penalty", value=str(settings.get("spam_penalty", "bandit")), inline=True)
		embed.add_field(name="Recent Join Seconds", value=str(settings.get("spam_recent_join_seconds", 259200)), inline=True)
		await ctx.send(embed=embed)

	@spamconfig.command(name="set")
	@commands.has_permissions(administrator=True)
	async def spamconfig_set(self, ctx, key: str = None, *, value: str = None):
		if ctx.guild is None:
			await ctx.send("This command can only be used in a server.")
			return
		if not ctx.author.guild_permissions.administrator:
			await ctx.send(f"**{ctx.author.display_name}:** You must be a server administrator to use this command.")
			return
		if key is None or value is None:
			await ctx.invoke(self.spamconfig)
			return

		key = key.lower()
		normalized = {
			"staff_channel": "staff_channel_id",
			"bandit_role": "bandit_role_id",
			"trigger_count": "spam_trigger_channel_count",
			"window_seconds": "spam_window_seconds",
			"penalty": "spam_penalty",
			"recent_join_seconds": "spam_recent_join_seconds",
			"enabled": "spam_enabled",
		}.get(key)

		if normalized is None:
			await ctx.send(
				"Unknown configuration option.\n\n"
				"Use `.spamconfig` to view all available settings and what they do, "
				"or `.spamconfig show` to view the current configuration."
			)
			return

		# Default confirmation value for ordinary settings.
		display_value = value

		if normalized == "staff_channel_id":
			channel_input = value.strip()

			if not channel_input:
				await ctx.send("Please provide a valid channel mention, name, or ID.")
				return

			channel = None

			# Case 1: Channel mention (<#123456789>)
			mention_match = re.fullmatch(r"<#(\d+)>", channel_input)

			if mention_match:
				channel_id = int(mention_match.group(1))
				channel = ctx.guild.get_channel(channel_id)

			# Case 2: Raw channel ID
			elif channel_input.isdigit():
				channel_id = int(channel_input)
				channel = ctx.guild.get_channel(channel_id)

			# Case 3: Exact channel name, with optional leading #
			else:
				channel_name = channel_input.removeprefix("#")
				channel = discord.utils.get(ctx.guild.channels, name=channel_name)

			if channel is None:
				await ctx.send(
					"That channel was not found in this server. "
					"Please mention it, give its ID, or provide its exact name."
				)
				return

			# Optional: only permit message-capable server channels
			if not isinstance(
				channel,
				(
					discord.TextChannel,
					discord.ForumChannel,
					discord.VoiceChannel,
					discord.StageChannel,
				),
			):
				await ctx.send("That channel cannot be used as the staff channel.")
				return

			MyGlobals.db.set_guild_setting(ctx.guild.id, normalized, channel.id)

			# Displays as a clickable Discord channel mention.
			display_value = channel.mention

		elif normalized == "bandit_role_id":
			role_input = value.strip()
			if not role_input:
				await ctx.send("Please provide a valid role mention, name, or ID.")
				return

			role = None

			# Case 1: Role mention (<@&123456789>)
			mention_match = re.search(r'<@&(\d+)>', role_input)
			if mention_match:
				role_id = int(mention_match.group(1))
				role = ctx.guild.get_role(role_id)

			# Case 2: Raw ID
			elif role_input.isdigit():
				role_id = int(role_input)
				role = ctx.guild.get_role(role_id)

			# Case 3: Role name
			else:
				role = discord.utils.get(ctx.guild.roles, name=role_input)

			if role is None:
				await ctx.send("That role was not found in this server. Please mention it, give its ID, or exact name.")
				return

			# Store the ID
			MyGlobals.db.set_guild_setting(ctx.guild.id, "bandit_role_id", role.id)

			# Displays as a clickable Discord role mention.
			display_value = role.mention

		elif normalized == "spam_window_seconds":
			try:
				num_value = int(value)
				if num_value < 1 or num_value > 15:
					raise ValueError
			except ValueError:
				await ctx.send("Please provide a positive whole number up to 15.")
				return
			MyGlobals.db.set_guild_setting(ctx.guild.id, normalized, num_value)

		elif normalized in {"spam_trigger_channel_count", "spam_recent_join_seconds"}:
			try:
				num_value = int(value)
				if num_value < 1:
					raise ValueError
			except ValueError:
				await ctx.send("Please provide a positive whole number.")
				return
			MyGlobals.db.set_guild_setting(ctx.guild.id, normalized, num_value)

		elif normalized == "spam_penalty":
			option = value.strip().lower()
			if option not in {"bandit", "kick_recent", "kick", "ban", "ban_recent"}:
				await ctx.send("Penalty must be one of: bandit, kick_recent, kick, ban, ban_recent")
				return
			MyGlobals.db.set_guild_setting(ctx.guild.id, normalized, option)

		elif normalized == "spam_enabled":
			option = value.strip().lower()
			if option in {"yes", "on", "true", "1"}:
				stored = 1
			elif option in {"no", "off", "false", "0"}:
				stored = 0
			else:
				await ctx.send("Enabled must be one of: on/off, yes/no, true/false")
				return
			MyGlobals.db.set_guild_setting(ctx.guild.id, normalized, stored)

		await ctx.send(f"Updated spam setting `{key}` to {display_value}.")

	@spamconfig.command(name="reset")
	@commands.has_permissions(administrator=True)
	async def spamconfig_reset(self, ctx):
		if ctx.guild is None:
			await ctx.send("This command can only be used in a server.")
			return
		if not ctx.author.guild_permissions.administrator:
			await ctx.send(f"**{ctx.author.display_name}:** You must be a server administrator to use this command.")
			return
		MyGlobals.db.reset_guild_settings(ctx.guild.id)
		await ctx.send("Spam settings have been reset to defaults for this server.")

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

	async def _ensure_owner(self, ctx):
		if ctx.author.id != MANGAD_ID:
			await ctx.send(f"**{ctx.author.display_name}:** You lack permission to use this command. :angry:")
			return False
		return True

	async def _fetch_image_bytes(self, ctx, image_url: str = None):
		image_data = None
		if image_url is None:
			if ctx.message.attachments:
				image_data = await ctx.message.attachments[0].read()
			elif ctx.message.reference:
				replied_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
				if replied_msg.attachments:
					image_data = await replied_msg.attachments[0].read()
				else:
					await ctx.send(f"**{ctx.author.display_name}:** No image found in the replied message.")
					return None
			else:
				await ctx.send(f"**{ctx.author.display_name}:** Please provide an image URL, attach an image, or reply to a message with an image.")
				return None
		else:
			try:
				async with aiohttp.ClientSession() as session:
					async with session.get(image_url) as resp:
						if resp.status != 200:
							await ctx.send(f"**{ctx.author.display_name}:** Failed to download image from URL.")
							return None
						image_data = await resp.read()
			except (aiohttp.ClientError, asyncio.TimeoutError) as e:
				await ctx.send(f"**{ctx.author.display_name}:** Failed to download image: {e}")
				return None
		return image_data

	@commands.command(
		description=(
			"Changes the bot account's username.\n"
			"Usage: `.setaccountnick [name]`\n"
			"This command can only be used by the bot owner."
		)
	)
	async def setaccountnick(self, ctx, *, name: str = None):
		"""Set the bot account's username."""
		if not await self._ensure_owner(ctx):
			return
		if name is None:
			await ctx.send(f"**{ctx.author.display_name}:** Please provide a username.")
			return
		if len(name) > 32:
			await ctx.send(f"**{ctx.author.display_name}:** Username must be 32 characters or less.")
			return
		try:
			await self.client.user.edit(username=name)
		except discord.Forbidden:
			await ctx.send(f"**{ctx.author.display_name}:** I lack permission to change my username!")
		except discord.HTTPException as e:
			await ctx.send(f"**{ctx.author.display_name}:** An error occurred while changing username: {e}")
		except Exception as e:
			await ctx.send(f"**{ctx.author.display_name}:** An unexpected error occurred: {e}")

	@commands.command(
		description=(
			"Changes the bot account's avatar.\n"
			"Usage:\n"
			"  `.setaccountavatar [image_url]` - Provide a direct image URL\n"
			"  `.setaccountavatar` with an attachment - Upload an image with the command\n"
			"  Reply to a message with an image, then use `.setaccountavatar` - Extract from replied message\n"
			"This command can only be used by the bot owner."
		)
	)
	async def setaccountavatar(self, ctx, image_url: str = None):
		"""Set the bot account's avatar."""
		if not await self._ensure_owner(ctx):
			return
		avatar_data = await self._fetch_image_bytes(ctx, image_url)
		if avatar_data is None:
			return
		try:
			await self.client.user.edit(avatar=avatar_data)
		except discord.Forbidden:
			await ctx.send(f"**{ctx.author.display_name}:** I lack permission to change my avatar!")
		except discord.HTTPException as e:
			await ctx.send(f"**{ctx.author.display_name}:** An error occurred while changing avatar: {e}")
		except Exception as e:
			await ctx.send(f"**{ctx.author.display_name}:** An unexpected error occurred: {e}")

	@commands.command(
		description=(
			"Changes the bot account's banner.\n"
			"Usage:\n"
			"  `.setaccountbanner [image_url]` - Provide a direct image URL\n"
			"  `.setaccountbanner` with an attachment - Upload an image with the command\n"
			"  Reply to a message with an image, then use `.setaccountbanner` - Extract from replied message\n"
			"This command can only be used by the bot owner."
		)
	)
	async def setaccountbanner(self, ctx, image_url: str = None):
		"""Set the bot account's banner."""
		if not await self._ensure_owner(ctx):
			return
		banner_data = await self._fetch_image_bytes(ctx, image_url)
		if banner_data is None:
			return
		try:
			await self.client.user.edit(banner=banner_data)
		except discord.Forbidden:
			await ctx.send(f"**{ctx.author.display_name}:** I lack permission to change my banner!")
		except discord.HTTPException as e:
			await ctx.send(f"**{ctx.author.display_name}:** An error occurred while changing banner: {e}")
		except Exception as e:
			await ctx.send(f"**{ctx.author.display_name}:** An unexpected error occurred: {e}")

	@commands.command(
		description=(
			"Changes the bot account's bio (about me).\n"
			"Usage: `.setaccountbio [text]`\n"
			"This command can only be used by the bot owner."
		)
	)
	async def setaccountbio(self, ctx, *, text: str = None):
		"""Inform the user that account bio changes are not supported by the current Discord library version."""
		if not await self._ensure_owner(ctx):
			return
		await ctx.send("Changing the bot account bio is not supported by the current Discord library version.")

	@commands.command(
		description=(
			"Changes the bot's display name (nickname) in the current guild.\n"
			"Usage: `.setnick [name]`\n"
			"To remove the nickname, use `.setnick` with no arguments.\n"
			"Max 32 characters."
		)
	)
	@commands.has_permissions(administrator=True)
	async def setnick(self, ctx, *, name: str = None):
		"""Set the bot's nickname in the guild."""
		
		if not ctx.author.guild_permissions.manage_guild:
			await ctx.channel.send(f"**{ctx.author.display_name}:** You lack permission to use this command. :angry:")
			return
		
		# Check if the bot has permission to change its own nickname
		if not ctx.guild.me.guild_permissions.change_nickname:
			await ctx.send(f"**{ctx.author.display_name}:** I don't have permission to change my nickname!")
			return
		
		try:
			if name is None:
				await ctx.guild.me.edit(nick=None, reason=f"Nickname reset by {ctx.author.display_name}")
			else:
				if len(name) > 32:
					await ctx.send(f"**{ctx.author.display_name}:** Nickname must be 32 characters or less.")
					return
				await ctx.guild.me.edit(nick=name, reason=f"Nickname changed by {ctx.author.display_name}")
		except discord.Forbidden:
			await ctx.send(f"**{ctx.author.display_name}:** I lack permission to change my nickname!")
		except discord.HTTPException as e:
			await ctx.send(f"**{ctx.author.display_name}:** An error occurred while changing nickname: {e}")
		except Exception as e:
			await ctx.send(f"**{ctx.author.display_name}:** An unexpected error occurred: {e}")

	@commands.command(
		description=(
			"Changes the bot's avatar.\n"
			"Usage:\n"
			"  `.setavatar [image_url]` - Provide a direct image URL\n"
			"  `.setavatar` with an attachment - Upload an image with the command\n"
			"  Reply to a message with an image, then use `.setavatar` - Extract from replied message\n"
			"Supported formats: PNG, JPG, GIF, WebP (max 10 MB)\n"
			"This requires administrator permissions."
		)
	)
	@commands.has_permissions(administrator=True)
	async def setavatar(self, ctx, image_url: str = None):
		"""Set the bot's avatar."""
		
		if not ctx.author.guild_permissions.administrator:
			await ctx.channel.send(f"**{ctx.author.display_name}:** You lack permission to use this command. :angry:")
			return
		
		avatar_data = await self._fetch_image_bytes(ctx, image_url)
		if avatar_data is None:
			return
		
		try:
			await ctx.guild.me.edit(avatar=avatar_data, reason=f"Avatar changed by {ctx.author.display_name}")
		except discord.Forbidden:
			await ctx.send(f"**{ctx.author.display_name}:** I lack permission to change my avatar!")
		except discord.HTTPException as e:
			await ctx.send(f"**{ctx.author.display_name}:** An error occurred while changing avatar: {e}")
		except Exception as e:
			await ctx.send(f"**{ctx.author.display_name}:** An unexpected error occurred: {e}")

	@commands.command(
		description=(
			"Changes the bot's banner.\n"
			"Usage:\n"
			"  `.setbanner [image_url]` - Provide a direct image URL\n"
			"  `.setbanner` with an attachment - Upload an image with the command\n"
			"  Reply to a message with an image, then use `.setbanner` - Extract from replied message\n"
			"Supported formats: PNG, JPG, GIF, WebP (max 10 MB)\n"
			"This requires administrator permissions."
		)
	)
	@commands.has_permissions(administrator=True)
	async def setbanner(self, ctx, image_url: str = None):
		"""Set the bot's banner."""
		
		if not ctx.author.guild_permissions.administrator:
			await ctx.channel.send(f"**{ctx.author.display_name}:** You lack permission to use this command. :angry:")
			return
		
		banner_data = await self._fetch_image_bytes(ctx, image_url)
		if banner_data is None:
			return
		
		try:
			await ctx.guild.me.edit(banner=banner_data, reason=f"Banner changed by {ctx.author.display_name}")
		except discord.Forbidden:
			await ctx.send(f"**{ctx.author.display_name}:** I lack permission to change my banner!")
		except discord.HTTPException as e:
			await ctx.send(f"**{ctx.author.display_name}:** An error occurred while changing banner: {e}")
		except Exception as e:
			await ctx.send(f"**{ctx.author.display_name}:** An unexpected error occurred: {e}")

	@commands.command(
		description=(
			"Changes the bot's bio (about me).\n"
			"Usage: `.setbio [text]`\n"
			"To remove the bio, use `.setbio` with no arguments.\n"
			"Max 190 characters.\n"
			"This requires administrator permissions."
		)
	)
	@commands.has_permissions(administrator=True)
	async def setbio(self, ctx, *, text: str = None):
		"""Set the bot's bio."""
		
		if not ctx.author.guild_permissions.administrator:
			await ctx.channel.send(f"**{ctx.author.display_name}:** You lack permission to use this command. :angry:")
			return
		
		try:
			if text is None:
				await ctx.guild.me.edit(bio=None, reason=f"Bio reset by {ctx.author.display_name}")
			else:
				if len(text) > 190:
					await ctx.send(f"**{ctx.author.display_name}:** Bio must be 190 characters or less.")
					return
				await ctx.guild.me.edit(bio=text, reason=f"Bio changed by {ctx.author.display_name}")
		except discord.Forbidden:
			await ctx.send(f"**{ctx.author.display_name}:** I lack permission to change my bio!")
		except discord.HTTPException as e:
			await ctx.send(f"**{ctx.author.display_name}:** An error occurred while changing bio: {e}")
		except Exception as e:
			await ctx.send(f"**{ctx.author.display_name}:** An unexpected error occurred: {e}")

async def setup(client):
	await client.add_cog(Moderation(client))
