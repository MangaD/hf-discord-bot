import sqlite3
import asyncio
import discord
import json

class Database:

	def __init__(self, client):
		self.client = client
		self.FILE_NAME='guild_users.db'
		self._settings_cache = {}

	def init_db(self):
		conn = sqlite3.connect(self.FILE_NAME)
		try:
			with conn:
				cursor = conn.cursor()
				cursor.execute('''
					CREATE TABLE IF NOT EXISTS users (
						user_id INTEGER NOT NULL,
						username TEXT NOT NULL,
						display_name TEXT NOT NULL,
						nick TEXT,
						guild_id INTEGER NOT NULL,
						roles TEXT NOT NULL,
						PRIMARY KEY (user_id, guild_id)
					)
				''')

				cursor.execute('''
					CREATE TABLE IF NOT EXISTS guild_settings (
						guild_id INTEGER PRIMARY KEY,
						staff_channel_id INTEGER,
						bandit_role_id TEXT DEFAULT 'Bandit',
						spam_trigger_channel_count INTEGER DEFAULT 3,
						spam_window_seconds INTEGER DEFAULT 15,
						spam_penalty TEXT DEFAULT 'bandit',
						spam_recent_join_seconds INTEGER DEFAULT 259200,
						spam_enabled INTEGER DEFAULT 1
					)
				''')
				cursor.execute('''
					CREATE TABLE IF NOT EXISTS guild_backups (
						guild_id INTEGER PRIMARY KEY,
						created_at TEXT NOT NULL,
						snapshot_json TEXT NOT NULL
					)
				''')
		finally:
			conn.close()

	def save_guild_backup(self, guild_id, created_at, snapshot, users):
		conn = sqlite3.connect(self.FILE_NAME)
		try:
			with conn:
				conn.execute('DELETE FROM users WHERE guild_id = ?', (guild_id,))
				conn.executemany('''
					INSERT INTO users (user_id, username, display_name, nick, guild_id, roles)
					VALUES (?, ?, ?, ?, ?, ?)
				''', users)
				conn.execute('''
					INSERT OR REPLACE INTO guild_backups (guild_id, created_at, snapshot_json)
					VALUES (?, ?, ?)
				''', (guild_id, created_at, json.dumps(snapshot)))
		finally:
			conn.close()

	def get_guild_backup(self, guild_id):
		conn = sqlite3.connect(self.FILE_NAME)
		try:
			row = conn.execute(
				'SELECT created_at, snapshot_json FROM guild_backups WHERE guild_id = ?',
				(guild_id,)
			).fetchone()
		finally:
			conn.close()
		if row is None:
			return None
		return row[0], json.loads(row[1])

	def _default_guild_settings(self):
		return {
			"staff_channel_id": None,
			"bandit_role_id": None,
			"spam_trigger_channel_count": 3,
			"spam_window_seconds": 15,
			"spam_penalty": "bandit",
			"spam_recent_join_seconds": 259200,
			"spam_enabled": 1,
		}

	def get_guild_settings(self, guild_id):
		if guild_id in self._settings_cache:
			return self._settings_cache[guild_id]

		defaults = self._default_guild_settings()
		conn = sqlite3.connect(self.FILE_NAME)
		cursor = conn.cursor()
		cursor.execute('SELECT * FROM guild_settings WHERE guild_id = ?', (guild_id,))
		row = cursor.fetchone()
		if not row:
			conn.close()
			self._settings_cache[guild_id] = defaults
			return defaults
		columns = [col[0] for col in cursor.description]
		settings = dict(zip(columns, row))
		conn.close()
		for key, value in defaults.items():
			settings.setdefault(key, value)
		self._settings_cache[guild_id] = settings
		return settings

	def set_guild_setting(self, guild_id, key, value):
		allowed_columns = {
			"staff_channel_id",
			"bandit_role_id",
			"spam_trigger_channel_count",
			"spam_window_seconds",
			"spam_penalty",
			"spam_recent_join_seconds",
			"spam_enabled",
		}
		if key not in allowed_columns:
			return False

		conn = sqlite3.connect(self.FILE_NAME)
		cursor = conn.cursor()
		cursor.execute('INSERT OR IGNORE INTO guild_settings (guild_id) VALUES (?)', (guild_id,))
		cursor.execute(f'UPDATE guild_settings SET {key} = ? WHERE guild_id = ?', (value, guild_id))
		conn.commit()
		conn.close()
		# Update cache
		if guild_id in self._settings_cache:
			self._settings_cache[guild_id][key] = value
		return True

	def reset_guild_settings(self, guild_id):
		conn = sqlite3.connect(self.FILE_NAME)
		cursor = conn.cursor()
		cursor.execute('DELETE FROM guild_settings WHERE guild_id = ?', (guild_id,))
		conn.commit()
		conn.close()
		if guild_id in self._settings_cache:
			del self._settings_cache[guild_id]

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
		try:
			guild = member.guild
			if not guild.me.guild_permissions.manage_roles or not guild.me.guild_permissions.manage_nicknames:
				return False

			if member.top_role and member.top_role >= guild.me.top_role:
				return False

			with sqlite3.connect(self.FILE_NAME) as conn:
				result = conn.execute(
					'SELECT roles, nick FROM users WHERE user_id = ? AND guild_id = ?',
					(member.id, member.guild.id)
				).fetchone()

			if result:
				roles_str, nick = result
				backup = self.get_guild_backup(member.guild.id)
				saved_role_names = {
					role["id"]: role["name"]
					for role in backup[1]["roles"]
				} if backup else {}
				roles = []
				if roles_str:
					for role_id in (int(value) for value in roles_str.split(',')):
						role = guild.get_role(role_id)
						if role is None and role_id in saved_role_names:
							role = discord.utils.get(guild.roles, name=saved_role_names[role_id])
						if role is not None:
							roles.append(role)
				bandit_role = discord.utils.get(member.guild.roles, name="Bandit")
				if bandit_role in roles:
					roles = [bandit_role]
				await member.edit(roles=roles, nick=nick, reason="Restoring member data from backup")
				return True
			return None
		except discord.Forbidden:
			return False
		except sqlite3.Error as e:
			return False
		except discord.HTTPException as e:
			return False
