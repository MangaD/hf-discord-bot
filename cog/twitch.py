import asyncio
import aiohttp
import logging
from .common import *

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

async def twitch():
	"""Check if a Twitch channel is live and send notifications to the specified Discord channel."""
	t_channel = "hfstream"
	twitch_url = f"https://api.twitch.tv/kraken/streams/{t_channel}"
	headers = {"Client-ID": twitch_client_id, "Accept": "application/vnd.twitchtv.v5+json"}
	t_is_live = False

	while True:
		try:
			async with aiohttp.ClientSession() as session:
				async with session.get(twitch_url, headers=headers) as response:
					if response.status != 200:
						log.warning(f"Twitch API returned status {response.status}. Retrying in 2 minutes.")
						await asyncio.sleep(120)
						continue

					data = await response.json()

					# Check live status and notify Discord
					if data.get("stream") is not None:
						if not t_is_live:
							msg = f"**{t_channel}** has just gone live! Watch their stream here: https://www.twitch.tv/{t_channel}"
							channel = client.get_channel(PVP_ID)
							if channel:
								await channel.send(msg)
							log.info(f"Notified that {t_channel} is live.")
						t_is_live = True
					else:
						if t_is_live:
							msg = f"**{t_channel}** is no longer live! Sorry, you missed them this time."
							channel = client.get_channel(PVP_ID)
							if channel:
								await channel.send(msg)
							log.info(f"Notified that {t_channel} is no longer live.")
						t_is_live = False

		except aiohttp.ClientError as e:
			log.error(f"Failed to fetch Twitch stream status: {e}")
		
		await asyncio.sleep(120)
