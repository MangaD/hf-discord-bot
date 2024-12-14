import re
from .common import *
from discord.ext import commands

class Help(commands.Cog):
	"""Displays help information for bot commands."""

	def __init__(self, client):
		self.client = client

	@commands.command(description="Displays this help message.")
	async def help(self, ctx, *commands: str):
		"""Displays this help message."""

		if not commands:
			embed = self.create_help_embed(ctx)
		else:
			embed = await self.create_category_embed(ctx, commands[0])

			if embed is None:  # If the category is not found
				await ctx.channel.send("No such category.")
				return

		embed.set_footer(text=BOT_URL, icon_url=ICON_URL)
		await ctx.channel.send(embed=embed)

	def create_help_embed(self, ctx) -> discord.Embed:
		"""Creates and returns the main help embed with category list."""
		description_text = (
			f"{DESCRIPTION}\n\nType '.help <category>' for a list of commands in that category."
		)
		embed = discord.Embed(title="Help", description=description_text, colour=discord.Colour.orange())
		
		# List all categories (cogs) with their descriptions
		for name, cog in ctx.bot.cogs.items():
			embed.add_field(name=name, value=cog.__doc__, inline=False)

		return embed

	async def create_category_embed(self, ctx, category_name: str) -> discord.Embed:
		"""Creates and returns an embed for a specific command category (cog)."""
		cog = self.get_cog_by_name(ctx, category_name)
		if cog is None:
			return None

		embed = discord.Embed(title=cog.qualified_name, description='\u200b', colour=discord.Colour.orange())
		
		# List all commands in the specified category
		for command in cog.get_commands():
			if not command.hidden:
				embed.add_field(name=command.name, value=command.description or "No description available.", inline=False)

		return embed

	def get_cog_by_name(self, ctx, name: str):
		"""Find and return a cog by name, case-insensitively."""
		for cog_name, cog in ctx.bot.cogs.items():
			if cog_name.lower() == name.lower():
				return cog
		return None

async def setup(client):
	await client.add_cog(Help(client))
