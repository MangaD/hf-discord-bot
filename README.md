# Hero Fighter &ndash; Discord Bot

[![Discord server invite](https://discord.com/api/guilds/234364433344888832/widget.png)](https://discord.gg/3PUwmY8) [![License](https://img.shields.io/badge/license-MIT-red?style=flat)](LICENSE) ![Python 3.8+](https://img.shields.io/badge/python-v3.8+-blue?style=flat)

![Bot Avatar](resources/bot_avatar.png)

## Introduction

A Discord bot for the Hero Fighter server. Created in July 8th, 2017. Receives occasional updates and new features.

### Set up

#### Linux specific

```sh
sudo apt install libav-tools
sudo apt install libsodium-dev
```

#### All platforms

```sh
pip install -U -r requirements.txt
```

#### Configuration

Create a `config.py` file in the root directory, with the following template:

```py
bot_private_token = "" # The bot's token
twitch_client_id = "" # The client ID of Twitch for notifying when a stream goes live
```

If using the random phrases feature, create a `random_phrases.txt` file in the root directory with a list of phrases separated by new lines.

### Requirements

- Python 3.8+

### Features

- In the Hero Fighter server, tells the user to introduce himself in the `#introductions` channel when he joins. Or welcomes him back if he already introduced himself in the past.
- Removes text messages in the `#media` and `#artwork` channels of the Hero Fighter server.
- In the Hero Fighter server, assigns the 'Bandit' role to a member that had this role and tried to rejoin.
- In the Hero Fighter server, assigns the 'Chinese' role to a member that joins and has Chinese characters in the name. 

### Commands

- Games
  - **ping:** Ping Pong!

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
  - use f-strings
  - use decorators
  - create HFGuild class with the info of this guild in it
  - create Bot class with bot info in it
  - Redo Help command (check RoboDanny for this)
  - Check tutorial: https://vcokltfre.dev/tutorial/
- Create reminder command (look into RoboDanny)
  - use sqlite
- Store members (roles, notes, etc) and chat history in database. When a member rejoins, the roles are re-attributed.
