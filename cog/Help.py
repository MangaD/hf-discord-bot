import discord
from discord.ext import commands
from .common import BOT_URL, ICON_URL, DESCRIPTION

# Define emojis for each cog/category
COG_EMOJIS = {
	"Help": "🙋‍♂️",
	"Games": "🎮",
	"Utilities": "🛠️",
	"Discord": "🗣️",
	"HeroFighter": "🦹‍♂️",
	"Moderation": "🔰"
	# Add more categories and their emojis as needed
}

class HelpDropdown(discord.ui.Select):
	def __init__(self, bot, help_command):
		self.client = bot
		self.help_command = help_command
		# Dropdown options for each category (cog) with emojis, name, and description
		options = [
			discord.SelectOption(
				label=name,
				description=cog.__doc__ or "No description available.",
				emoji=COG_EMOJIS.get(name, "❓")
			)
			for name, cog in bot.cogs.items()
		]
		super().__init__(placeholder="Select a category...", min_values=1, max_values=1, options=options)

	async def callback(self, interaction: discord.Interaction):
		cog = self.client.get_cog(self.values[0])
		if cog:
			embed = self.help_command.create_category_embed(cog)
			view = HelpView(self.client, self.help_command, show_main=False)
			await interaction.response.edit_message(embed=embed, view=view)


class HelpView(discord.ui.View):
	def __init__(self, bot, help_command, show_main=True):
		super().__init__(timeout=None)
		self.add_item(HelpDropdown(bot, help_command))
		if not show_main:
			self.add_item(IndexButton(bot, help_command))
		self.add_item(QuitButton())


class IndexButton(discord.ui.Button):
	def __init__(self, bot, help_command):
		super().__init__(style=discord.ButtonStyle.secondary, label="Index", emoji="📖")
		self.client = bot
		self.help_command = help_command

	async def callback(self, interaction: discord.Interaction):
		embed = self.help_command.create_main_help_embed(self.client)
		view = HelpView(self.client, self.help_command)
		await interaction.response.edit_message(embed=embed, view=view)


class QuitButton(discord.ui.Button):
	def __init__(self):
		super().__init__(style=discord.ButtonStyle.danger, label="Quit", emoji="❌")

	async def callback(self, interaction: discord.Interaction):
		await interaction.message.delete()


class Help(commands.Cog):
	"""Displays help information for bot commands."""

	def __init__(self, client):
		self.client = client

	@commands.command(description="Displays this help message.")
	async def help(self, ctx, *, query: str = None):
		"""Displays this help message."""
		if query:
			# Check if the query matches a command
			command = self.client.get_command(query)
			if command:
				embed = self.create_command_embed(command)
				await ctx.send(embed=embed)
				return

			# Check if the query matches a category (cog)
			cog = self.client.get_cog(query)
			if cog:
				embed = self.create_category_embed(cog)
				await ctx.send(embed=embed)
				return

			# If no match, send an error message
			await ctx.send(f"No category or command found for '{query}'.")
		else:
			# If no query is provided, show the main help embed with categories
			embed = self.create_main_help_embed(self.client)
			await ctx.send(embed=embed, view=HelpView(self.client, self))

	def create_main_help_embed(self, bot) -> discord.Embed:
		"""Creates and returns the main help embed with category list."""
		description_text = (
			f"{DESCRIPTION}\n\nUse `.help command` for more info on a command.\nUse `.help category` for more info on a category.\nUse the dropdown menu below to select a category.\n\nYou can see my code on [GitLab](https://gitlab.com/MangaD/hf-discord-bot)!"
		)
		embed = discord.Embed(title="Help", description=description_text, colour=discord.Colour.orange())

		# List all categories (cogs) with their descriptions
		#for name, cog in bot.cogs.items():
		#	embed.add_field(name=f"{COG_EMOJIS.get(name, '❓')} {name}", value=cog.__doc__ or "No description available.", inline=False)
		embed.set_footer(text=BOT_URL, icon_url=ICON_URL)
		return embed

	def create_category_embed(self, cog) -> discord.Embed:
		"""Creates and returns an embed for a specific command category (cog)."""
		embed = discord.Embed(
			title=f"{COG_EMOJIS.get(cog.qualified_name, '❓')} {cog.qualified_name} Commands",
			description=cog.description or "No description available.",
			colour=discord.Colour.orange()
		)

		# List all commands in the specified category
		for command in cog.get_commands():
			if not command.hidden:
				embed.add_field(
					name=f"`{self.client.command_prefix}{command.name}`",
					value=command.description or "No description available.",
					inline=False
				)
		embed.set_footer(text=BOT_URL, icon_url=ICON_URL)
		return embed

	def create_command_embed(self, command) -> discord.Embed:
		"""Creates and returns an embed for a specific command."""
		embed = discord.Embed(
			title=f"Help: `{self.client.command_prefix}{command.name}`",
			description=command.help or "No description available.",
			colour=discord.Colour.blue()
		)
		# Show usage details, if available
		usage = f"{self.client.command_prefix}{command.qualified_name} {command.signature}"
		embed.add_field(name="Usage", value=usage, inline=False)
		return embed


async def setup(client):
	await client.add_cog(Help(client))
