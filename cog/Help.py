import re
from .common import *

class Help(commands.Cog): # Class shows as category in ".help" command

	"""Shows help regarding my commands."""

	def __init__(self, client):
		self.client = client

	@commands.command(pass_context=True, description='Shows this message.')
	async def help(self, ctx, *commands : str):
		"""Shows this message."""

		embed = discord.Embed(title = 'Help', description = description, colour = discord.Colour.orange())
		#embed.set_author(name=client.user.name, icon_url=str(client.user.avatar_url))

		if len(commands) == 0:
			embed.description = description + "\n\n" + "Type '.help category' for a list of commands in that category."
			# Print categories and their descriptions
			for name, cog in ctx.bot.cogs.items():
				embed.add_field(name=name, value=cog.__doc__, inline=False)
		elif len(commands) >= 1:

			# For some reason, get_cog fails for HeroFighter
			#command_name = commands[0].capitalize()
			#cog = ctx.bot.get_cog(command_name)

			cog = None
			for name, c in ctx.bot.cogs.items():
				if name.lower() == commands[0].lower():
					cog = c
			if cog is None:
				await ctx.channel.send("No such category.")
				return

			embed.title = cog.qualified_name
			embed.description = '\u200b'
			for c in cog.get_commands():
				if c.hidden is False:
					embed.add_field(name=c.name, value=c.description, inline=False)


		embed.set_footer(text=bot_url, icon_url=icon_url)

		await ctx.channel.send(embed=embed)


async def setup(client):
	await client.add_cog(Help(client))
