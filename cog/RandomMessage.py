import asyncio
import random
from random import randint
from .common import *

@asyncio.coroutine
async def RandomMessage():
	txt_file = open("random_phrases.txt", "r")
	random_phrases = txt_file.readlines()
	while True:
		await asyncio.sleep(randint(1800, 86400))
		await client.send_message(client.get_channel(english_general_id), random.choice(random_phrases))
