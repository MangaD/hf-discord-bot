import sqlite3
import asyncio
import discord

class Database:

	def __init__(self, client):
		self.client = client
		self.FILE_NAME='guild_users.db'

	def init_db(self):
		conn = sqlite3.connect(self.FILE_NAME)
		cursor = conn.cursor()
		cursor.execute('''
			CREATE TABLE IF NOT EXISTS users (
				user_id INTEGER PRIMARY KEY,
				username TEXT NOT NULL,
				display_name TEXT NOT NULL,
				nick TEXT,
				guild_id INTEGER NOT NULL,
				roles TEXT NOT NULL
			)
		''')
		conn.commit()
		conn.close()

	async def update_user_in_db(self, user_id, username, display_name, nick, guild_id, roles):
		try:
			conn = sqlite3.connect(self.FILE_NAME)
			cursor = conn.cursor()
			roles_str = ','.join(str(role.id) for role in roles if role != self.client.get_guild(guild_id).default_role)
			cursor.execute('''
				INSERT OR REPLACE INTO users (user_id, username, display_name, nick, guild_id, roles)
				VALUES (?, ?, ?, ?, ?, ?)
			''', (user_id, username, display_name, nick, guild_id, roles_str))
			conn.commit()
			conn.close()
		except sqlite3.Error as e:
			#notification_channel = self.client.get_channel("1305142334286991460")
			#await notification_channel.send(f"Database error: {e}")
			pass

	async def remove_user_from_db(self, user_id, guild_id):
		try:
			conn = sqlite3.connect(self.FILE_NAME)
			cursor = conn.cursor()
			cursor.execute('DELETE FROM users WHERE user_id = ? AND guild_id = ?', (user_id, guild_id))
			conn.commit()
			conn.close()
		except sqlite3.Error as e:
			#notification_channel = self.client.get_channel("1305142334286991460")
			#await notification_channel.send(f"Database error: {e}")
			pass


	async def has_role(self, user_id, guild_id, role):
		notification_channel = self.client.get_channel("1305142334286991460")
		try:
			# Get the guild
			guild = self.client.get_guild(guild_id)
			if not guild:
				#await notification_channel.send(f"Guild {guild_id} not found")
				return False

			# Resolve the role by name or ID
			if isinstance(role, str):
				target_role = discord.utils.get(guild.roles, name=role)
			elif isinstance(role, int):
				target_role = guild.get_role(role)
			else:
				#await notification_channel.send(f"Invalid role parameter type: {type(role)}")
				return False

			if not target_role:
				#await notification_channel.send(f"Role {role} not found in guild {guild_id}")
				return False

			# Query the database for the user's roles
			conn = sqlite3.connect(self.FILE_NAME)
			cursor = conn.cursor()
			cursor.execute('SELECT roles FROM users WHERE user_id = ? AND guild_id = ?', (user_id, guild_id))
			result = cursor.fetchone()
			conn.close()

			if not result or not result[0]:  # No user or no roles
				return False

			# Check if the target role ID is in the stored roles
			role_ids = result[0].split(',')
			return str(target_role.id) in role_ids
		except sqlite3.Error as e:
			#await notification_channel.send(f"Database error: {e}")
			return False

	async def update_user_global_name(self, user_id, username, display_name):
		notification_channel = self.client.get_channel("1305142334286991460")
		try:
			conn = sqlite3.connect(self.FILE_NAME)
			cursor = conn.cursor()
			cursor.execute('SELECT guild_id, nick, roles FROM users WHERE user_id = ?', (user_id,))
			rows = cursor.fetchall()
			for guild_id, nick, roles in rows:
				cursor.execute('''
					INSERT OR REPLACE INTO users (user_id, username, display_name, nick, guild_id, roles)
					VALUES (?, ?, ?, ?, ?, ?)
				''', (user_id, username, display_name, nick, guild_id, roles))
			conn.commit()
			conn.close()
			#await notification_channel.send(f"Updated global username for user {user_id} across {len(rows)} guilds")
		except sqlite3.Error as e:
			#await notification_channel.send(f"Database error: {e}")
			pass

	async def restore_user_data(self, member):
		notification_channel = self.client.get_channel("1305142334286991460")
		try:
			guild = self.client.get_guild(member.guild.id)
			if not guild.me.guild_permissions.manage_roles or not guild.me.guild_permissions.manage_nicknames:
				#await notification_channel.send(f"Missing permissions to restore roles/nickname for {member} in guild {member.guild.id}")
				return False

			if member.top_role and member.top_role >= guild.me.top_role:
				#await notification_channel.send(f"User's highest role is above or equal to mine for {member} in guild {member.guild.id}")
				return False

			conn = sqlite3.connect(self.FILE_NAME)
			cursor = conn.cursor()
			cursor.execute('SELECT roles, nick FROM users WHERE user_id = ? AND guild_id = ?', (member.id, member.guild.id))
			result = cursor.fetchone()

			if result:
				roles_str, nick = result
				if roles_str:
					bandit_role = discord.utils.get(member.guild.roles, name="Bandit")
					role_ids = roles_str.split(',')
					roles = [guild.get_role(int(rid)) for rid in role_ids if guild.get_role(int(rid))]
					if roles:
						if bandit_role in roles:
							await member.edit(roles=[bandit_role], reason="Restoring bandit role")
						else:
							await member.edit(roles=roles, reason="Restoring roles from database")
				if nick:
					await member.edit(nick=nick, reason="Restoring nickname from database")
				conn.commit()
				conn.close()
				#await notification_channel.send(f"Restored roles and nickname for {member} in guild {member.guild.id}")
				return True
			conn.close()
			return False
		except discord.Forbidden:
			#await notification_channel.send(f"Missing permissions to edit roles/nickname for {member} in guild {member.guild.id}")
			return False
		except sqlite3.Error as e:
			#await notification_channel.send(f"Database error for {member} in guild {member.guild.id}: {e}")
			return False
		except discord.HTTPException as e:
			#await notification_channel.send(f"Discord API error for {member} in guild {member.guild.id}: {e}")
			return False
