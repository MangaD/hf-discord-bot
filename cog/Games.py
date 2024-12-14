from .common import *

import re

class Games(commands.Cog): # Class shows as category in ".help" command

	"""For bored personal."""

	def __init__(self, client):
		self.client = client

	@commands.command(pass_context=True,
		description='Ping Pong!') # description appears when using ".help ping"
	async def ping(self, ctx):
		"""Ping Pong!""" # Appears in ".help"
		await ctx.channel.send("**{0}:** Pong!".format(ctx.message.author.name))

	@commands.command(pass_context=True,
		description='2-4-6 Task') # description appears when using ".help 246"
	async def tfs(self, ctx, *, word : str = None):
		"""2-4-6 Task""" # Appears in ".help"
		if word is None:
			e = discord.Embed(
				title='2-4-6 Task',
				colour = discord.Colour.orange(),
				description='This is not just a game. This is a lesson. '
					'If you research this task without trying to solve '
					'it first, you won\'t learn from it.\n\n'
					'I have a rule - known to me, but not to you - which '
					'fits some triplets of three numbers, but not others. '
					'2-4-6 is one example of a triplet which fits the rule. '
					'Now the way this game works, is that you give me triplets '
					'of three numbers, and I\'ll tell you \'Yes\' if the three '
					'numbers are an instance of the rule, and \'No\' if they\'re '
					'not. I am Nature, the rule is one of my laws, and you are '
					'investigating me. You already know that 2-4-6 gets a \'Yes\'. '
					'When you\'ve performed all the further experimental tests you '
					'want - asked me as many triplets as you feel necessary - you '
					'stop and guess the rule, and then I will tell you how you did.\n\n'
					'To test a triplet, type: _.tfs 2 4 6_\n'
					'To guess the rule and get your answer, type: _.tfs guess The rule is bananas._'
				)
			return await ctx.channel.send(embed=e)

		# Check if triplet was given
		if re.match(r'^(\d+) +(\d+) +(\d+) *$', word) is not None:
			triplet = re.findall(r'\d+', word)
			if triplet[0] < triplet[1] < triplet[2]:
				return await ctx.channel.send('Yes.')
			else:
				return await ctx.channel.send('No.')

		# Check if guess was given
		if re.match(r'^ *guess +.+$', word) is not None:
			guess = re.search(r'^ *guess +(.+)$', word)
			e = discord.Embed(
                                title='2-4-6 Task',
                                colour = discord.Colour.orange(),
                                description='Your guess was: _' + guess.group(1) + '_\n'
					'The rule is: _Three real numbers in increasing order, lowest to highest._\n\n'
					'In 1960, Peter Cathcart Wason developed the first of many tasks he '
					'would devise to reveal the failures of human reasoning. '
					'The "2-4-6" task was the first experiment that showed people to be '
					'illogical and irrational. In this study, subjects were told that the '
					'experimenter had a rule in mind that only applied to sets of threes. '
					'The "2-4-6" rule the experimenter had in mind was "any ascending sequence". '
					'In most cases, subjects not only formed hypotheses that were more specific '
					'than necessary, but they also **only tested positive examples** of their '
					'hypothesis. Wason was surprised by the large number of subjects who failed '
					'to get the task correct. The subjects **failed to test instances inconsistent '
					'with their own hypothesis**, which further supported Wason’s hypothesis '
					'of **confirmation bias**. Confirmation bias is the tendency to search for, '
					'interpret, favor, and recall information in a way that confirms or supports '
					'one\'s prior beliefs or values. It is an important type of cognitive bias '
					'that has a significant effect on the proper functioning of society by '
					'distorting evidence-based decision-making.'
			)
			return await ctx.channel.send(embed=e)

		return await ctx.channel.send('Invalid input. For instructions, type: _.tfs_')


async def setup(client):
	await client.add_cog(Games(client))
