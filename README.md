# Hero Fighter &ndash; Discord Bot

[![Discord server invite](https://discord.com/api/guilds/234364433344888832/widget.png)](https://discord.gg/3PUwmY8) [![License](https://img.shields.io/badge/license-MIT-red?style=flat)](LICENSE) ![Python 3.11+](https://img.shields.io/badge/python-v3.11+-blue?style=flat)

![Bot Avatar](resources/avatar/bot_avatar_v2.png)

## Introduction

A Discord bot for the Hero Fighter server, created in July 8th, 2017. This bot provides a wide range of functionalities, including YouTube video playback, text-to-speech, translation, and more. It is built using Python 3.11+ and leverages the discord.py library for seamless integration with Discord.

### Set up

#### Linux specific

```sh
sudo apt install libav-tools
sudo apt install libsodium-dev
sudo apt install libffi-dev libnacl-dev python3-dev
```

#### All platforms

```sh
python3 -m venv hfbot
source hfbot/bin/activate
pip install -U -r requirements.txt
```

Run with:

```sh
source hfbot/bin/activate
python3 HFBot.py
```

#### Configuration

Create a `config.py` file in the root directory, with the following template:

```py
import openai

bot_private_token = "" # The bot's token
twitch_client_id = "" # The client ID of Twitch for notifying when a stream goes live
bad_words = ["@#$%", ")/%/"] # If the Urban Dictionary answer contains one of the specified badwords, "- nsfw -" will be the only output.
openai.api_key = "YOUR_API_KEY"
```

If using the random phrases feature, create a `random_phrases.txt` file in the root directory with a list of phrases separated by new lines.

### Requirements

- Python 3.11+

### Features

- In the Hero Fighter server, tells the user to introduce himself in the `#introductions` channel when he joins. Or welcomes him back if he already introduced himself in the past.
- Removes text messages (unless youtube, deviantart, or image links) in the `#media`, `#artwork`, `#memes`, and `#hf_memes` channels of the Hero Fighter server.
- In the Hero Fighter server, sends notifications on channel modifications, member joins, leaves, kicks, bans, and changed roles.
- In the Hero Fighter server, assigns the 'Bandit' role to a member that had this role and tried to rejoin.
- In the Hero Fighter server, assigns the 'Chinese' role to a member that joins and has Chinese characters in the name. 

### Commands

- Games
  - **ping:** Ping Pong!
  - **tfs:** Play the 2-4-6 Task game.

- Help
  - **help:** Shows the command list.

- HeroFighter
  - **status:** Checks if the Hero Fighter v0.7 services are up and running.
  - **download:** Provides the link for downloading [HF](http://www.mediafire.com/file/ifqnas78z6eosyy/Hero_Fighter_v0.7.exe) and [RS](http://herofighter-empire.com/downloads/servers/RS_0.7_1.0a_MangaD.zip).
  - **search:** Searches for a user in [HFE](http://www.herofighter-empire.com/forum/) and [LFE](https://www.lf-empire.de/forum/).
  - **rl:** Prints the [HF Room List](http://herofighter-empire.com/hf-empire/multiplayer/room-list).

- Moderation
  - **bandit:** Gives the Bandit role to a user in the Hero Fighter server, even if the user rejoins the server.

- Utilities
  - **ud:** Look up a word on UrbanDictionary.
  - **8:** Ask the magic 8ball a question!
  - **mangle:** Repeatedly translate the input until it makes absolutely no sense.
  - **yt:** Look up a video on YouTube.
  - **ytc:** Play a YouTube video in voice channel.
  - **ytp:** Pause / resume audio from voice channel.
  - **ytd:** Disconnect from voice channel.
  - **wt:** Look up a word on Wiktionary.
  - **w:** Look up something on Wikipedia.
  - **tr:** Translates a phrase, with an optional language hint.
  - **tts:** Text to speech with optional language hint.
  - **time:** Returns the date & time for a given timezone.
  - **weight:** Converts kg to lbs and vice-versa.
  - **height:** Converts heights.
  - **length:** General length converter.
  - **fx:** Currency converter using up-to-date reference rates (e.g. `.fx 10 usd to eur`).
  - **fxlist:** Lists all supported currency codes.
  - **ai:** Interacts with OpenAI.
  - **ai_img:** Asks OpenAI to generate images given a description.

- Discord
  - **uptime:** Returns the uptime of HF Bot.
  - **avatar:** Get the avatar image of a user.
  - **serversplash:** Displays the splash image of the guild.
  - **serverbanner:** Displays the banner image of the guild.
  - **serverdiscoverysplash:** Displays the discovery splash image of the guild.
  - **serverinfo:** Shows info related to the guild.
  - **channelinfo:** Shows info related to a channel.
  - **userinfo:** Shows info related to a user.
  - **botinfo:** Shows info about the bot.

### To do

- Do more checks:
  - look into modules/checks.py and modules/Moderation.py
  - look into https://discordpy.readthedocs.io/en/stable/ext/commands/commands.html
  - look into https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/utils/checks.py
- Look into RoboDanny (https://github.com/Rapptz/RoboDanny)
  - Try out its commands in the discord.py server
- Refactor code
  - use decorators
  - create HFGuild class with the info of this guild in it
  - create Bot class with bot info in it
  - Check tutorial: https://vcokltfre.dev/tutorial/
- Create reminder command (look into RoboDanny)
  - use sqlite
- Store members (roles, notes, etc) and chat history in database. When a member rejoins, the roles are re-attributed.
- Look for a word in the Oxford and Cambridge dictionaries.
- Unit tests: https://www.youtube.com/watch?v=1Lfv5tUGsn8
