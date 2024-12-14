from .common import *
import re
from discord.ext import commands

class Games(commands.Cog):
	"""Games and tasks for entertainment and learning."""

	def __init__(self, client):
		self.client = client
		self.triplet_pattern = re.compile(r'^(\d+)\s+(\d+)\s+(\d+)\s*$')
		self.guess_pattern = re.compile(r'^ *guess +(.+)$')

	@commands.command(description="Ping Pong!")
	async def ping(self, ctx):
		"""Respond with Pong!"""
		await ctx.channel.send(f"**{ctx.author.name}:** Pong!")

	@commands.command(description="2-4-6 Task")
	async def tfs(self, ctx, *, word: str = None):
		"""Play the 2-4-6 Task game."""
		if word is None:
			return await ctx.send(embed=self.get_instructions_embed())

		# Check if a triplet was given
		if self.triplet_pattern.match(word):
			triplet = list(map(int, self.triplet_pattern.findall(word)[0]))
			response = "Yes." if triplet[0] < triplet[1] < triplet[2] else "No."
			return await ctx.channel.send(response)

		# Check if a guess was given
		if self.guess_pattern.match(word):
			guess = self.guess_pattern.findall(word)[0]
			return await ctx.channel.send(embed=self.get_guess_embed(guess))

		# If input is invalid
		return await ctx.channel.send("Invalid input. For instructions, type: `.tfs`")

	def get_instructions_embed(self) -> discord.Embed:
		"""Generate and return the instructions embed for the 2-4-6 Task."""
		return discord.Embed(
			title="2-4-6 Task",
			colour=discord.Colour.orange(),
			description=(
				"This is not just a game. This is a lesson. "
				"If you research this task without trying to solve it first, you won't learn from it.\n\n"
				"I have a rule - known to me, but not to you - which fits some triplets of numbers, but not others. "
				"2-4-6 is an example of a triplet that fits the rule.\n\n"
				"To play, give me a triplet of numbers, and I'll say 'Yes' if it fits the rule, or 'No' if it doesn't. "
				"When you're ready, guess the rule.\n\n"
				"**Example Commands:**\n"
				"To test a triplet: `.tfs 2 4 6`\n"
				"To guess the rule: `.tfs guess [your guess]`"
			)
		)

	def get_guess_embed(self, guess: str) -> discord.Embed:
		"""Generate and return the embed for a guess attempt with explanation."""
		return discord.Embed(
			title="2-4-6 Task",
			colour=discord.Colour.orange(),
			description=(
				f"Your guess was: _{guess}_\n"
				"The rule is: _Any three real numbers in ascending order._\n\n"
				"This task was designed by Peter Cathcart Wason in 1960 to illustrate **confirmation bias** - the "
				"tendency to favor information that confirms our existing beliefs. Many participants only test examples "
				"that fit their hypothesis, failing to consider cases that might disprove it.\n\n"
				"Confirmation bias is an important cognitive bias that can distort decision-making by skewing evidence "
				"toward one's prior beliefs. Reflect on this as you make your next decision!"
			)
		)

async def setup(client):
	await client.add_cog(Games(client))
