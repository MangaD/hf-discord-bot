from .common import *

@client.event
async def on_command_completion(ctx):
	"""Add a checkmark reaction upon successful command completion."""
	await ctx.message.add_reaction('\N{WHITE HEAVY CHECK MARK}')

"""
@client.event
async def on_command_error(ctx, error):
	\"\"\"Handle errors raised when commands are invoked.\"\"\"

	# If the command is not found, respond with a thoughtful message
	if isinstance(error, commands.CommandNotFound):
		await ctx.send(":thinking: I don't recognize that command.")
		return

	# Handle all other errors by notifying the user and logging the error
	try:
		await ctx.send(f"An error occurred: {error}")
	except discord.Forbidden:
		# Log an error if the bot lacks permission to send messages in the channel
		log.error(f"Failed to send error message in {ctx.channel}: insufficient permissions.")

	# Log the error for further inspection
	log.error(f"An error occurred while executing the {ctx.command.qualified_name} command: {error}")
"""
