from .common import *

# Room List
from random import randint
import urllib.request
from xml.dom import minidom
import requests

def URLStatus(url, timeout_):
	from urllib.error import URLError, HTTPError
	from socket import timeout
	try:
		code = urllib.request.urlopen(url, timeout=timeout_).getcode()
		if code == 200:
			return True
		else:
			return False
	except (HTTPError, URLError) as error:
		return False
	except timeout:
		return False

def searchUser(forum : str, word : str, max_users_to_display : int):
	query = urllib.parse.quote(word)
	url = forum + "/memberlist.php?sort=postnum&username_match=contains&username=" + query
	r = requests.get(url, stream=True)
	reg = '(?:(?:<td class="trow[12]">)|(?:<div class="plink text-center col-sm-12">)|(?:<h4 class="memberlistname">))<a href="(.*?)">(<span.*?>)?(.*)?</a>'
	i = 0
	message = ""
	for (url2, garbage, user) in re.findall(reg, r.text):
		i+=1
		user = user.replace("<strong>", "")
		user = user.replace("</strong>", "")
		user = user.replace("</span>", "")
		url2 = url2.replace("&amp;", "&")
		if i <= max_users_to_display:
			message += user + " - <" + url2 + ">\n"
		else:
			message += "\nFor more users go to: <" + url + ">\n"
			break
	return message

def chunks(s, n):
	"""Produce `n`-character chunks from `s`."""
	for start in range(0, len(s), n):
		yield s[start:start+n]

class HeroFighter(commands.Cog):
	"""Everything concerning Hero Fighter goes here."""

	def __init__(self, client):
		self.client = client

	@commands.command(pass_context=False, description='Provides the link for downloading HF and RS.')
	async def download(self, ctx):
		"""Provides the link for downloading HF and RS."""
		await ctx.channel.send('**HFX (mobile):** <https://hf-empire.com/hfx-empire/download>\n'
		                      '**HFv0.7+ w/ RS (PC):** <https://www.mediafire.com/file/6ik4w1t1qsd4ci1/HFv0.7%252B.zip/file>\n'
		                      '**Room Server:** <https://www.mediafire.com/file/s1ehbcqqtzvycve/RS_v0.7%252B_2021-01-21.zip/file>\n'
		                      '**HF Workshop:** <https://hf-empire.com/downloads/hf-workshop/HFWorkshop_x86.exe>\n'
		                      '**HF Equilibrium (mod):** <https://hf-empire.com/forum/showthread.php?tid=339>\n'
		                      '**HFE BD Skin (mod):** <https://hf-empire.com/forum/showthread.php?tid=328>\n'
		                      '**ALL MODS:** <https://hf-empire.com/forum/forumdisplay.php?fid=37>');

	@commands.command(description='Checks if the Hero Fighter v0.7 services are up and running.')
	async def status(self, ctx):
		"""Checks if the Hero Fighter v0.7 services are up and running."""
		message = ''
		if URLStatus("http://herofighter.com", 2):
			message += 'Hero Fighter website is **up**!\n'
		else:
			message += 'Hero Fighter website is **down**!\n'
		if URLStatus("https://hf-empire.com", 2):
			message += 'Hero Fighter Empire website is **up**!\n'
		else:
			message += 'Hero Fighter Empire website is **down**!\n'
		if URLStatus("http://s.herofighter.com", 2):
			message += 'Hero Fighter v0.7 services are **up**!'
		else:
			message += 'Hero Fighter v0.7 services are **down**!'

		await ctx.channel.send(message)



	@commands.command(description='Prints the HF Room List.')
	async def rl(self, ctx):
		"""Prints the HF Room List."""
		try:
		        f = urllib.request.urlopen('http://herofighter.com/hf/rlg.php?ver=700&cc=de&s=' + str(randint(0, 99999)))
		        data = f.read();
		        f.close();
		except IOError:
		        await ctx.channel.send('Failed to connect to the server.');
		        return;
		data = minidom.parseString(data);
		rooms = data.getElementsByTagName('room');
		if rooms.length <= 0:
		        await ctx.channel.send('No rooms available.');
		        return;
		i = 1; room_s = "";
		for room in rooms:
		        room_s += ( str(i) + '. **' + room.getElementsByTagName("rn")[0].firstChild.nodeValue + '**'
					'\t' + room.getElementsByTagName("dc")[0].firstChild.nodeValue +
		                        '\t' + room.getElementsByTagName("cc")[0].firstChild.nodeValue +
		                        '\t' + room.getElementsByTagName("n")[0].firstChild.nodeValue +
		                        '/' + room.getElementsByTagName("nl")[0].firstChild.nodeValue );
		        ppl = room.getElementsByTagName("ppl");
		        if ppl[0].firstChild != None:
		                room_s += '\t' + ppl[0].firstChild.nodeValue;
		        room_s += '\n'
		        i+=1;
		for chunk in chunks( encode_string_with_links(room_s), 2000):
			await ctx.channel.send( chunk );

	@commands.command(pass_context=True, description='Searches for a user in HFE and LFE.')
	async def search(self, ctx, *, word : str = None):
		"""Searches for a user in HFE and LFE."""
		max_users_to_display = 5
		if word is None:
			return await ctx.channel.send('**{0}:** You must tell me what to look up!'.format(ctx.message.author.name))
		message1 = searchUser("https://hf-empire.com/forum", word, max_users_to_display);
		if message1 != "":
			message1 = "**Hero Fighter Empire**\n\n" + message1

		message2 = searchUser("https://lf-empire.de/forum", word, max_users_to_display);
		if message2 != "":
			if message1 != "":
				message2 = "\n**Little Fighter Empire**\n\n" + message2
			else:
				message2 = "**Little Fighter Empire**\n\n" + message2

		message3 = searchUser("http://hf-empire.top/forum", word, max_users_to_display);

		if message3 != "":
			if message1 != "" or message2 != "":
				message3 = "\n**Hero Fighter Empire CN**\n\n" + message3
			else:
				message3 = "**Hero Fighter Empire CN**\n\n" + message3

		message = message1 + message2 + message3
		if message == "":
			return await ctx.channel.send("No users matching the criteria.")
		else:
			return await ctx.channel.send(message)

def setup(client):
    client.add_cog(HeroFighter(client))
