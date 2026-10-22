from datetime import datetime, timezone

import discord


def _channel_type(channel):
	if isinstance(channel, discord.CategoryChannel):
		return "category"
	if isinstance(channel, discord.StageChannel):
		return "stage"
	if isinstance(channel, discord.ForumChannel):
		return "forum"
	if isinstance(channel, discord.VoiceChannel):
		return "voice"
	if isinstance(channel, discord.TextChannel):
		return "news" if channel.is_news() else "text"
	return None


def _serialize_overwrites(channel):
	overwrites = []
	for target, overwrite in channel.overwrites.items():
		if isinstance(target, discord.Role):
			target_type = "role"
		else:
			target_type = "member"
		allow, deny = overwrite.pair()
		overwrites.append({
			"type": target_type,
			"id": target.id,
			"allow": allow.value,
			"deny": deny.value,
		})
	return overwrites


async def capture_guild(guild):
	members = []
	async for member in guild.fetch_members(limit=None):
		if member.id == guild.me.id:
			continue
		members.append({
			"user_id": member.id,
			"username": str(member),
			"display_name": member.display_name,
			"nick": member.nick,
			"roles": [role.id for role in member.roles if role != guild.default_role],
		})

	bans = []
	async for entry in guild.bans(limit=None):
		bans.append({
			"user_id": entry.user.id,
			"username": str(entry.user),
			"reason": entry.reason,
		})

	roles = [{
		"id": role.id,
		"name": role.name,
		"permissions": role.permissions.value,
		"color": role.color.value,
		"hoist": role.hoist,
		"mentionable": role.mentionable,
		"position": role.position,
		"managed": role.managed,
	} for role in guild.roles]

	channels = []
	for channel in guild.channels:
		channel_kind = _channel_type(channel)
		if channel_kind is None:
			continue

		data = {
			"id": channel.id,
			"name": channel.name,
			"type": channel_kind,
			"position": channel.position,
			"category_id": channel.category_id,
			"overwrites": _serialize_overwrites(channel),
		}
		if channel_kind in {"text", "news", "forum"}:
			data.update({
				"topic": channel.topic,
				"nsfw": channel.nsfw,
				"slowmode_delay": channel.slowmode_delay,
				"default_auto_archive_duration": getattr(channel, "default_auto_archive_duration", 1440),
				"default_thread_slowmode_delay": getattr(channel, "default_thread_slowmode_delay", 0),
			})
		if channel_kind == "forum":
			data["available_tags"] = [{
				"name": tag.name,
				"moderated": tag.moderated,
				"emoji": str(tag.emoji) if tag.emoji else None,
			} for tag in channel.available_tags]
			data.update({
				"default_sort_order": (
					channel.default_sort_order.value if channel.default_sort_order is not None else None
				),
				"default_layout": channel.default_layout.value if channel.default_layout is not None else None,
				"default_reaction_emoji": (
					str(channel.default_reaction_emoji)
					if channel.default_reaction_emoji else None
				),
			})
		if channel_kind in {"voice", "stage"}:
			data.update({
				"bitrate": channel.bitrate,
				"user_limit": channel.user_limit,
				"rtc_region": str(channel.rtc_region) if channel.rtc_region else None,
				"video_quality_mode": channel.video_quality_mode.value if channel.video_quality_mode else None,
				"nsfw": channel.nsfw,
			})
		channels.append(data)

	guild_config = {
		"name": guild.name,
		"description": guild.description,
		"afk_timeout": guild.afk_timeout,
		"default_notifications": guild.default_notifications.value,
		"verification_level": guild.verification_level.value,
		"explicit_content_filter": guild.explicit_content_filter.value,
		"preferred_locale": str(guild.preferred_locale),
		"system_channel_id": guild.system_channel.id if guild.system_channel else None,
		"rules_channel_id": guild.rules_channel.id if guild.rules_channel else None,
		"public_updates_channel_id": (
			guild.public_updates_channel.id if guild.public_updates_channel else None
		),
		"afk_channel_id": guild.afk_channel.id if guild.afk_channel else None,
		"system_channel_flags": guild.system_channel_flags.value,
		"premium_progress_bar_enabled": guild.premium_progress_bar_enabled,
	}

	return {
		"version": 1,
		"created_at": datetime.now(timezone.utc).isoformat(),
		"guild": guild_config,
		"roles": roles,
		"channels": channels,
		"members": members,
		"bans": bans,
	}


def _find_role(guild, saved_role):
	role = guild.get_role(saved_role["id"])
	if role is None:
		role = discord.utils.get(guild.roles, name=saved_role["name"])
	return role


def _find_channel(guild, saved_channel, channel_type):
	channel = guild.get_channel(saved_channel["id"])
	if channel is not None and _channel_type(channel) == channel_type:
		return channel
	return discord.utils.find(
		lambda current: current.name == saved_channel["name"] and _channel_type(current) == channel_type,
		guild.channels
	)


def _make_overwrites(guild, entries, role_map):
	overwrites = {}
	for entry in entries:
		if entry["type"] == "role":
			target = role_map.get(entry["id"])
		else:
			target = guild.get_member(entry["id"]) or discord.Object(id=entry["id"])
		if target is not None:
			overwrites[target] = discord.PermissionOverwrite.from_pair(
				discord.Permissions(entry["allow"]),
				discord.Permissions(entry["deny"])
			)
	return overwrites


async def restore_guild(guild, snapshot):
	role_map = {}
	default_role_data = next((role for role in snapshot["roles"] if role["id"] == guild.id), None)
	if default_role_data:
		await guild.default_role.edit(
			permissions=discord.Permissions(default_role_data["permissions"]),
			reason="Guild recovery"
		)
		role_map[default_role_data["id"]] = guild.default_role

	for saved_role in sorted(snapshot["roles"], key=lambda role: role["position"]):
		if saved_role["id"] == guild.id:
			continue
		role = _find_role(guild, saved_role)
		if saved_role["managed"]:
			if role is not None:
				role_map[saved_role["id"]] = role
			continue
		if role is None:
			role = await guild.create_role(
				name=saved_role["name"],
				permissions=discord.Permissions(saved_role["permissions"]),
				color=discord.Color(saved_role["color"]),
				hoist=saved_role["hoist"],
				mentionable=saved_role["mentionable"],
				reason="Guild recovery"
			)
		else:
			await role.edit(
				name=saved_role["name"],
				permissions=discord.Permissions(saved_role["permissions"]),
				color=discord.Color(saved_role["color"]),
				hoist=saved_role["hoist"],
				mentionable=saved_role["mentionable"],
				reason="Guild recovery"
			)
		role_map[saved_role["id"]] = role

	for saved_role in sorted(snapshot["roles"], key=lambda role: role["position"]):
		role = role_map.get(saved_role["id"])
		if role is not None and not role.is_default() and not role.managed:
			await role.edit(position=saved_role["position"], reason="Guild recovery")

	channel_map = {}
	saved_channels = snapshot["channels"]
	for channel_type in ("category", "text", "news", "voice", "stage", "forum"):
		for saved_channel in sorted(
			(channel for channel in saved_channels if channel["type"] == channel_type),
			key=lambda channel: channel["position"]
		):
			channel = _find_channel(guild, saved_channel, channel_type)
			category = channel_map.get(saved_channel["category_id"])
			overwrites = _make_overwrites(guild, saved_channel["overwrites"], role_map)
			if channel is None:
				common = {
					"reason": "Guild recovery",
					"position": saved_channel["position"],
					"overwrites": overwrites,
				}
				if channel_type == "category":
					channel = await guild.create_category(saved_channel["name"], **common)
				elif channel_type in {"text", "news"}:
					channel = await guild.create_text_channel(
						saved_channel["name"],
						category=category,
						topic=saved_channel["topic"] or "",
						nsfw=saved_channel["nsfw"],
						slowmode_delay=saved_channel["slowmode_delay"],
						default_auto_archive_duration=saved_channel["default_auto_archive_duration"],
						default_thread_slowmode_delay=saved_channel["default_thread_slowmode_delay"],
						news=channel_type == "news",
						**common
					)
				elif channel_type in {"voice", "stage"}:
					create_channel = guild.create_stage_channel if channel_type == "stage" else guild.create_voice_channel
					channel = await create_channel(
						saved_channel["name"],
						category=category,
						bitrate=saved_channel["bitrate"],
						user_limit=saved_channel["user_limit"],
						rtc_region=saved_channel["rtc_region"],
						video_quality_mode=(
							discord.VideoQualityMode(saved_channel["video_quality_mode"])
							if saved_channel["video_quality_mode"] is not None else discord.VideoQualityMode(1)
						),
						nsfw=saved_channel.get("nsfw", False),
						**common
					)
				else:
					forum_options = {
						"topic": saved_channel["topic"] or "",
						"nsfw": saved_channel["nsfw"],
						"slowmode_delay": saved_channel["slowmode_delay"],
						"default_auto_archive_duration": saved_channel["default_auto_archive_duration"],
						"default_thread_slowmode_delay": saved_channel["default_thread_slowmode_delay"],
						"available_tags": [
							discord.ForumTag(
								name=tag["name"],
								moderated=tag["moderated"],
								emoji=discord.PartialEmoji.from_str(tag["emoji"]) if tag["emoji"] else None,
							)
							for tag in saved_channel["available_tags"]
						],
					}
					if saved_channel["default_sort_order"] is not None:
						forum_options["default_sort_order"] = discord.ForumOrderType(
							saved_channel["default_sort_order"]
						)
					if saved_channel["default_layout"] is not None:
						forum_options["default_layout"] = discord.ForumLayoutType(
							saved_channel["default_layout"]
						)
					if saved_channel["default_reaction_emoji"] is not None:
						forum_options["default_reaction_emoji"] = discord.PartialEmoji.from_str(
							saved_channel["default_reaction_emoji"]
						)
					channel = await guild.create_forum(
						saved_channel["name"],
						category=category,
						**forum_options,
						**common
					)
			else:
				options = {
					"position": saved_channel["position"],
					"overwrites": overwrites,
					"category": category,
				}
				if channel_type in {"text", "news", "forum"}:
					options.update({
						"topic": saved_channel["topic"] or "",
						"nsfw": saved_channel["nsfw"],
						"slowmode_delay": saved_channel["slowmode_delay"],
						"default_auto_archive_duration": saved_channel["default_auto_archive_duration"],
						"default_thread_slowmode_delay": saved_channel["default_thread_slowmode_delay"],
					})
				if channel_type == "forum":
					if saved_channel["default_sort_order"] is not None:
						options["default_sort_order"] = discord.ForumOrderType(
							saved_channel["default_sort_order"]
						)
					if saved_channel["default_layout"] is not None:
						options["default_layout"] = discord.ForumLayoutType(
							saved_channel["default_layout"]
						)
					if saved_channel["default_reaction_emoji"] is not None:
						options["default_reaction_emoji"] = discord.PartialEmoji.from_str(
							saved_channel["default_reaction_emoji"]
						)
					options["available_tags"] = [
						discord.ForumTag(
							name=tag["name"],
							moderated=tag["moderated"],
							emoji=discord.PartialEmoji.from_str(tag["emoji"]) if tag["emoji"] else None,
						)
						for tag in saved_channel["available_tags"]
					]
				if channel_type in {"voice", "stage"}:
					options.update({
						"bitrate": saved_channel["bitrate"],
						"user_limit": saved_channel["user_limit"],
						"rtc_region": saved_channel["rtc_region"],
						"video_quality_mode": (
							discord.VideoQualityMode(saved_channel["video_quality_mode"])
							if saved_channel["video_quality_mode"] is not None else discord.VideoQualityMode(1)
						),
						"nsfw": saved_channel["nsfw"],
					})
				await channel.edit(reason="Guild recovery", **options)
			channel_map[saved_channel["id"]] = channel

	guild_settings = snapshot["guild"]
	guild_edit = {
		"name": guild_settings["name"],
		"description": guild_settings["description"],
		"afk_timeout": guild_settings["afk_timeout"],
		"default_notifications": discord.NotificationLevel(guild_settings["default_notifications"]),
		"verification_level": discord.VerificationLevel(guild_settings["verification_level"]),
		"explicit_content_filter": discord.ContentFilter(guild_settings["explicit_content_filter"]),
		"preferred_locale": discord.Locale(guild_settings["preferred_locale"]),
		"system_channel_flags": discord.SystemChannelFlags._from_value(guild_settings["system_channel_flags"]),
		"premium_progress_bar_enabled": guild_settings["premium_progress_bar_enabled"],
	}
	for setting, key in (
		("system_channel", "system_channel_id"),
		("rules_channel", "rules_channel_id"),
		("public_updates_channel", "public_updates_channel_id"),
		("afk_channel", "afk_channel_id"),
	):
		channel_id = guild_settings[key]
		guild_edit[setting] = channel_map.get(channel_id) if channel_id else None
	await guild.edit(reason="Guild recovery", **guild_edit)

	members = {
		member.id: member
		async for member in guild.fetch_members(limit=None)
	}
	member_count = 0
	skipped_member_count = 0
	for saved_member in snapshot["members"]:
		member = members.get(saved_member["user_id"])
		if member is None:
			continue
		if member.id == guild.owner_id or member.top_role >= guild.me.top_role:
			skipped_member_count += 1
			continue
		roles = [
			role_map[role_id]
			for role_id in saved_member["roles"]
			if role_id in role_map and role_map[role_id] != guild.default_role
		]
		await member.edit(roles=roles, nick=saved_member["nick"], reason="Guild recovery")
		member_count += 1

	ban_count = 0
	current_bans = {entry.user.id for entry in await guild.bans(limit=None)}
	for saved_ban in snapshot["bans"]:
		if saved_ban["user_id"] not in current_bans:
			await guild.ban(
				discord.Object(id=saved_ban["user_id"]),
				reason=saved_ban["reason"] or "Restored from guild backup",
				delete_message_seconds=0
			)
			ban_count += 1

	return {
		"roles": len(role_map),
		"channels": len(channel_map),
		"members": member_count,
		"skipped_members": skipped_member_count,
		"bans": ban_count,
		"role_map": role_map,
	}
