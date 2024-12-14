from .common import *

@client.event
async def on_command_completion(ctx):
	await ctx.message.add_reaction('\N{WHITE HEAVY CHECK MARK}')

"""
@client.event
async def on_command_error(error, ctx):
	if isinstance(error, commands.CommandNotFound):
		return await client.send_message(ctx.message.channel, ":thinking: I don't know that command.")

	# In case the bot failed to send a message to the channel, the try except pass statement is to prevent another error
	try:
		await client.send_message(ctx.message.channel, error)
	except:
		pass
	log.error("An error occured while executing the {} command: {}".format(ctx.command.qualified_name, error))
"""
