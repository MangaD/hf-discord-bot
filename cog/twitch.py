# Twitch
import asyncio
import urllib.request
import json

from . import common

t_is_live = False

async def twitch():
	global t_is_live
	t_channel = "hfstream"
	t_url = "https://api.twitch.tv/kraken/streams/{0}?client_id={1}".format(t_channel, twitch_client_id)
	while True:
		try:
			f = urllib.request.urlopen(t_url)
			data = f.read().decode('utf-8')
			f.close();
		except IOError:
			await asyncio.sleep(2*60)
			continue
		j_data = json.loads(data)
		if j_data["stream"] is not None:
			if not t_is_live:
				msg = "**{0}** has just gone live! Watch their stream here: https://www.twitch.tv/{0}".format(t_channel)
				await common.client.send_message(common.client.get_channel(common.pvp_id), msg) # id of pvp channel
			t_is_live = True
		else:
			if t_is_live:
				msg = "**{0}** is no longer live!  Sorry, you missed them this time.".format(t_channel)
				await common.client.send_message(common.client.get_channel(common.pvp_id), msg)
			t_is_live = False
		await asyncio.sleep(2*60)
