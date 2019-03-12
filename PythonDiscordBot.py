import discord
from discord import Game
from discord.ext import commands
from discord.ext.commands import Bot

from concurrent.futures import ThreadPoolExecutor

import time
import asyncio
import random

import PythonFunctions as Pf


# Discord Variables
BOT_PREFIX = ("!!", ">>")
BOT_STATUS = "!!help or >>help"

BOT_AUTHOR = "FeistyJalapeno#9045"
BOT_VERSION = "Version 3.1.0 Beta"
UPDATE_NOTES = "Overrode the default helps commands to make them easier to understand."
ABOUT_BOT = "This bot was created since when Paladins selects random champions its not random. Some people are highly "\
            "likely to get certain roles and if you have a full team not picking champions sometime the game fails to "\
            "fill the last person causing the match to fail to start and kick everyone. This could be due to the game" \
            "trying to select a champion that has already been selected."
GAME = ["Paladins", BOT_STATUS, BOT_VERSION, BOT_STATUS, "Errors"]


file_name = "token"
# Gets token from a file
with open(file_name, 'r') as f:
    TOKEN = f.readline().strip()
f.close()

# Creating client for bot
client = Bot(command_prefix=BOT_PREFIX)
client.remove_command('help')  # Removing default help command.


# Get simple stats for a player's last amount of matches.
@client.command(name='history',
                pass_context=True)
async def history(ctx, player_name, amount=10):
    await client.send_typing(ctx.message.channel)
    # Prevents blocking so that function calls are not delayed
    executor = ThreadPoolExecutor(max_workers=1)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, Pf.get_history, player_name, amount)
    await client.say("```diff\n" + result + "```")


# Get stats for a player in their last match.
@client.command(name='last')
async def last(player_name):
    # Prevents blocking so that function calls are not delayed
    executor = ThreadPoolExecutor(max_workers=1)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, Pf.get_history_simple, player_name)
    # await client.say("```" + result + "```")
    await client.say(embed=result)


# Get stats for a player's current match.
@client.command(name='current',
                pass_context=True,
                aliases=['cur', 'c'])
async def current(ctx, player_name, option="-s"):
    await client.send_typing(ctx.message.channel)
    # Prevents blocking so that function calls are not delayed
    executor = ThreadPoolExecutor(max_workers=1)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, Pf.get_player_in_match, player_name, option)
    await client.say("```diff\n" + result + "```")


# Calls different random functions based on input
@client.command(name='rand',
                aliases=['random', 'r'])
async def rand(command):
    command = str(command).lower()
    if command == "damage":
        await client.say("Your random Damage champion is: " + "```css\n" + Pf.pick_damage() + "```")
    elif command == "flank":
        await client.say("Your random Flank champion is: " + "```css\n" + Pf.pick_flank() + "```")
    elif command == "healer":
        await client.say("Your random Support/Healer champion is: " + "```css\n" + Pf.pick_support() + "```")
    elif command == "tank":
        await client.say("Your random FrontLine/Tank champion is: " + "```css\n" + Pf.pick_tank() + "```")
    elif command == "champ":
        await client.say("Your random champion is: " + "```css\n" + Pf.pick_random_champ() + "```")
    elif command == "team":
        await  client.say("Your random team is: " + "```css\n" + Pf.gen_team() + "```")
    elif command == "map" or command == "stage":
        await  client.say("Your random map is: " + "```css\n" + Pf.pick_map() + "```")
    else:
        await client.say("Invalid command. For the random command please choose from one following options: "
                         "damage, flank, healer, tank, champ, team, or map. "
                         "\n For example: `>>random damage` will pick a random damage champion")


# Says a little more about the bot to discord users
@client.command(name='about',
                aliases=['info', 'update'])
async def about():
    await client.say("Bot Author: " + BOT_AUTHOR + "\n"
                     "Bot Version: " + BOT_VERSION + "\n"
                     "Updated Notes: " + UPDATE_NOTES + "\n\n"
                     "About: " + ABOUT_BOT)


# Returns simple stats based on the option they choose (champ_name, me, or elo)
@client.command(name='stats',
                aliases=['stat'])
async def stats(player_name, option="me", space=""):
    if space != "":
        option += " " + space
    # Prevents blocking so that function calls are not delayed
    executor = ThreadPoolExecutor(max_workers=1)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, Pf.get_stats, player_name, option)
    if option == "me" or option == "elo":
        await client.say("```" + result + "```")
    else:
        # await client.say("```" + result + "```")
        await client.say(embed=result) #WHY IS THIS NoT WORKING?


# Handles errors when a user messes up the spelling or forgets an argument to a command or an error occurs
@client.event
async def on_command_error(error, ctx):
    channel = ctx.message.channel
    if isinstance(error, commands.MissingRequiredArgument):
        await client.send_message(channel, "A required argument to the command you called is missing"+"\N{CROSS MARK}")
        return 0
    if isinstance(error, commands.BadArgument):  # This should do nothing since I check in functions for input error
        await client.send_message(channel, "Make sure the command is in the correct format.")
    elif isinstance(error, commands.CommandNotFound):
        await client.send_message(channel, f"\N{WARNING SIGN} {error}")
    else:
        print("An uncaught error occurred: ", error)  # More error checking
        await client.send_message(channel, "Welp, something messed up. If you entered the command correctly just wait a"
                                           "few seconds and then try again.")


# We can use this code to track when people message this bot (a.k.a asking it commands)
@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    # Seeing if someone is using the bot_prefix and calling a command
    if message.content.startswith(BOT_PREFIX):
        print(message.author, message.content, message.channel, message.server, Pf.get_est_time())
        # if str(message.author) == "FeistyJalapeno#9045":  # This works ^_^
        #    print("Hello creator.")
    # Seeing if someone is using the bot_prefix and calling a command
    if message.content.startswith(">> ") or message.content.startswith("!! "):
        msg = 'Oops looks like you have a space after the bot prefix {0.author.mention}'.format(message)
        try:
            await client.send_message(message.author, msg)
        except:
            print("Bot does not have permission to print to this channel")  # Temp fix

    # on_message has priority over function commands
    await client.process_commands(message)


@client.command(name='test',
                aliases=['t'])
async def test():
    """
    embed = discord.Embed(
        colour=discord.colour.Color.dark_teal()
    )
    embed.add_field(name="image", value="http://paladins.guru/assets/img/champions/maldamba.jpg", inline=False)
    await client.say(embed=embed)
    """
    await client.say("<:yinglove:544651722371366924> <:yinglove:544651722371366924> <:yinglove:544651722371366924> "
                     "<:yinglove:544651722371366924> <:yinglove:544651722371366924>")


# Custom help commands
@client.group(pass_context=True)
async def help(ctx):
    # await client.say("Help commands are currently being reworked. If you have a question just dm FeistyJalapeno#9045")

    if ctx.invoked_subcommand is None:
        embed = discord.Embed(
            description="Check your dms for a full list of commands. For more help on a specific command call `>>help "
                        "<command>`",
            colour=discord.colour.Color.dark_teal()
        )
        await client.say(embed=embed)
        # Also if you want more information on help with the bot feel free to "
        #                 "join the bots help server [here](https://discord.gg/JTZ6cJQ) [https://discord.gg/JTZ6cJQ]")



        author = ctx.message.author
        embed = discord.Embed(
            colour=discord.colour.Color.dark_teal()
        )

        my_message = "Note to get the best experience when using PaladinsAssistant it is recommended that you use " \
                     "discord on desktop since over half of the commands use color and colors do not show up on Mobil."\
                     " Also if you want more information on how to use the bot to its full extent, feel free to join " \
                     "the support server here: https://discord.gg/JTZ6cJQ"

        embed.set_author(name='PaladinsAssistant Commands: ')
        embed.set_thumbnail(url="http://paladins.guru/assets/img/champions/grohk.jpg")
        # embed.set_image(url="https://mypaladins.com/images/paladins/champions/2417.jpg?v=nBF1oAzzG0m0XfoBSuWFwlHsLkORCTHVLyLdqDK1C9A")
        embed.set_footer(icon_url="https://cdn.discordapp.com/embed/avatars/0.png",
                         text="Bot created by FeistyJalapeno#9045.")
        # If you have questions, suggestions, found a bug, etc. feel free to DM me.")
        embed.add_field(name='help', value='Returns this message.', inline=False)
        embed.add_field(name='about', value='Returns more information about the bot.', inline=False)
        embed.add_field(name='last', value='Returns stats for a player\'s last match.', inline=False)
        embed.add_field(name='stats', value='Returns simple overall stats for a player.', inline=False)
        embed.add_field(name='random', value='Randomly chooses a map, champion, or team to help with custom matches.',
                        inline=False)
        embed.add_field(name='current', value='Returns stats for a player\'s current match.', inline=False)
        embed.add_field(name='history', value='Returns simple stats for a player\'s last amount of matches.',
                        inline=False)

        await client.send_message(author, my_message)
        await client.send_message(author, embed=embed)


@help.command()
async def about():
    await client.say("```Returns more information about the bot.```")


@help.command(pass_context=True)
async def last():
    command_name = "last"
    command_description = "Returns stats for a player\'s last match."
    parameters = ["player_name"]
    descriptions = ["Player's Paladins IGN"]
    await client.say(embed=create_embed(command_name, command_description, parameters, descriptions))


@help.command()
async def history():
    command_name = "history"
    command_description = "Returns simple stats for a player\'s last amount of matches."
    parameters = ["player_name", "amount"]
    descriptions = ["Player's Paladins IGN", "Amount of matches you want to see (2-30 matches)"]
    await client.say(embed=create_embed(command_name, command_description, parameters, descriptions))


@help.command()
async def current():
    command_name = "current"
    command_description = "Get stats for a player's current match."
    parameters = ["player_name"]
    descriptions = ["Player's Paladins IGN"]
    await client.say(embed=create_embed(command_name, command_description, parameters, descriptions))


@help.command()
async def stats():
    command_name = "stats"
    command_description = "Returns simple overall stats for a player."
    parameters = ["player_name", "option"]
    long_string = "can be one of the following: \n\n" \
                  "1. <me>: will return the player's overall stats. \n" \
                  "2. <elo>: will return the player's Guru elo.\n" \
                  "3. <champion_name>: will return the player's stats on the name of the champion entered."
    descriptions = ["Player's Paladins IGN", long_string]

    await client.say(embed=create_embed(command_name, command_description, parameters, descriptions))


@help.command()
async def rand():
    command_name = "rand"
    command_description = "Returns a random (champ, team, or map)."
    parameters = ["option"]
    long_string = "can be one of the following: \n\n" \
                  "1. <damage>: Picks a random Damage champion. \n" \
                  "2. <healer>: Picks a random Support/Healer champion. \n" \
                  "3. <flank>: Picks a random Flank champion. \n" \
                  "4. <tank>: Picks a random FrontLine/Tank champion. \n"\
                  "5. <champ>: Picks a random champion from any class. \n" \
                  "6. <map>: Picks a random siege/ranked map. \n" \
                  "7. <team>: Picks a random team. "\
                  "It will always pick (1 Damage, 1 Flank, 1 Support, and 1 FrontLine, "\
                  "and then one other random champion.)"
    descriptions = [long_string]

    await client.say(embed=create_embed(command_name, command_description, parameters, descriptions))


# Creates an embed base for the help commands. This way if I every want to change the look of all my help commands
# I can just change the look of all the help commands from this one function.
def create_embed(name, info, pars, des):
    embed = discord.Embed(
        colour=discord.colour.Color.dark_teal()
    )

    embed.add_field(name='Command Name:', value='```md\n' + name + '```', inline=False)
    embed.add_field(name='Description:', value='```fix\n' + info + '```',
                    inline=False)
    format_string = ""
    description_string = ""
    for par, de in zip(pars, des):
        format_string += " <" + par + ">"
        description_string += "<" + par + "> " + de + "\n"

    embed.add_field(name='Format:', value='```md\n>>' + name + format_string + '```', inline=False)
    embed.add_field(name='Parameters:', value='```md\n' + description_string + '```', inline=False)
    embed.set_footer(text="Bot created by FeistyJalapeno#9045. If you have questions, suggestions, "
                          "found a bug, etc. feel free to DM me.")

    return embed


sleep_time = 5
backoff_multiplier = 1


# Launching the bot function
@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    # print(client.user.id)
    print('------')
    # Status of the bot
    global backoff_multiplier
    backoff_multiplier = 1
    await client.change_presence(game=Game(name=BOT_STATUS, type=0), status='dnd')  # Online, idle, invisible, dnd
    print("Client is fully online and ready to go...")
    await list_servers()


async def list_servers():
    await client.wait_until_ready()
    while not client.is_closed:
        print("Current servers: ", len(client.servers))
        # for server in client.servers:
        #    print(server.name)
        break
        # await asyncio.sleep(600)


# Testing bot presence changing
async def change_bot_presence():
    await client.wait_until_ready()
    secure_random = random.SystemRandom()
    while not client.is_closed:
        await client.change_presence(game=Game(name=secure_random.choice(GAME), type=0), status='dnd')
        await asyncio.sleep(60)  # Ever min


# Fails if the server disconnects
client.loop.create_task(change_bot_presence())


# Loop that allows the bot to reconnect if the internet goes out
while True:
    try:
        client.loop.run_until_complete(client.start(TOKEN))
    except BaseException:  # Bad practice but is fine to use in this case
        print("Disconnected, going to try to reconnect in " + str(sleep_time*backoff_multiplier) + " seconds.")
        time.sleep(sleep_time*backoff_multiplier)
        backoff_multiplier += 1
