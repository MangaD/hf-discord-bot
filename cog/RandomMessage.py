import asyncio
import random
from .common import *

async def random_message():
	"""Send a random message to the specified channel at random intervals."""
	try:
		# Load random phrases once
		with open("random_phrases.txt", "r") as file:
			random_phrases = file.readlines()

		channel = client.get_channel(ENGLISH_GENERAL_ID)
		if not channel:
			log.error(f"Channel with ID {ENGLISH_GENERAL_ID} not found.")
			return

		while True:
			sleep_duration = random.randint(1800, 86400)
			await asyncio.sleep(sleep_duration)

			phrase = random.choice(random_phrases).strip()
			try:
				await channel.send(phrase)
			except discord.Forbidden:
				log.error(f"Permission denied to send messages to channel {ENGLISH_GENERAL_ID}.")
			except discord.HTTPException as e:
				log.error(f"Failed to send random message to channel {ENGLISH_GENERAL_ID}: {e}")
	except FileNotFoundError:
		log.error("File 'random_phrases.txt' not found. Please ensure it is available in the correct directory.")
