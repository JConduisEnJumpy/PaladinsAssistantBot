import random
import traceback
import asyncio

from discord import Game
from discord.ext.commands import Bot

# Discord Variables
BOT_PREFIX = ("!!", ">>")
BOT_STATUS = "!!help or >>help"
client = Bot(command_prefix=BOT_PREFIX)
TOKEN = "NTM3MzQ1ODE3MDcwMTQxNDUw.Dyptmw.zHrf5ozKflMqoBEDDxywOI9T0XA"


# List of Champs by Class
Damage = ["Cassie", "Kinessa", "Drogoz", "Bomb King", "Viktor", "Sha Lin", "Tyra", "Willo", "Lian", "Strix", "Vivian",
          "Dredge", "Imani"]
Flank = ["Skye", "Buck", "Evie", "Androxus", "Maeve", "Lex", "Zhin", "Talus", "Moji", "Koga"]
FrontLine = ["Barik", "Fernado", "Ruckus", "Makoa", "Trovald", "Inara", "Ash", "Terminus", "Khan"]
Support = ["Grohk", "Grover", "Ying", "Mal'Damba", "Seris", "Jenos", "Furia"]


# Picks a random damage champion.
def pick_damage():
    secure_random = random.SystemRandom()
    return secure_random.choice(Damage)


# Picks a random flank champion.
def pick_flank():
    secure_random = random.SystemRandom()
    return secure_random.choice(Flank)


# Picks a random tank champion.
def pick_tank():
    secure_random = random.SystemRandom()
    return secure_random.choice(FrontLine)


# Picks a random support champion.
def pick_support():
    secure_random = random.SystemRandom()
    return secure_random.choice(Support)


# Picks a random champion from any class.
def pick_random_champ():
    secure_random = random.SystemRandom()
    return secure_random.choice([pick_damage, pick_support, pick_tank, pick_flank])()


# Uses the random functions about to generate team of random champions
# It will always pick (1 Damage, 1 Flank, 1 Support, and 1 FrontLine, and then one other champion.)
def gen_team():
    team = []
    print("Random Team")
    team.append(pick_damage())
    team.append(pick_flank())
    team.append(pick_support())
    team.append(pick_tank())

    fill = pick_random_champ()
    """Keep Generating a random champ until its not one we already have"""
    while fill in team:
        fill = pick_random_champ()

    team.append(fill)

    """Shuffle the team so people get different roles"""
    random.shuffle(team)
    return team


"""End of Python Functions"""


# Calls python functions
@client.command(name='random',
                description="Picks a random champ(s) based on the given input. \n"
                            "damage - Picks a random Damage champion. \n"
                            "healer - Picks a random Support/Healer champion. \n"
                            "flank -  Picks a random Flank champion. \n"
                            "tank -   Picks a random FrontLine/Tank champion. \n"
                            "champ -  Picks a random champion from any class. \n"
                            "team -   Picks a random team. "
                            "It will always pick (1 Damage, 1 Flank, 1 Support, and 1 FrontLine, "
                            "and then one other champion.) \n",
                brief="Picks a random champ(s) based on the given input.\n",
                aliases=['rand', 'r'])
async def rand(command):
    command = str(command).lower()
    if command == "damage":
        await client.say("Your random Damage champion is: " + pick_damage())
    elif command == "flank":
        await client.say("Your random Flank champion is: " + pick_flank())
    elif command == "healer":
        await client.say("Your random Support/Healer champion is: " + pick_support())
    elif command == "tank":
        await client.say("Your random FrontLine/Tank champion is: " + pick_tank())
    elif command == "champ":
        await client.say("Your random champion is: " + pick_random_champ())
    elif command == "team":
        await  client.say("Your random team is: " + str(gen_team()))
    else:
        await client.say("Invalid command. For the random command please choose from one following options: "
                         "damage, flank, healer, tank, champ, or team.")


# This code for some reason does not work other discord functions and cause the bot to only respond to these commands
"""
@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    if message.content.startswith('*hello'):
        msg = 'Hello {0.author.mention}'.format(message)
        await client.send_message(message.channel, msg)
    elif message.content.startswith('*team'):
        await client.send_message(message.channel, str(gen_team()))
"""


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    # Status of the bot
    await client.change_presence(game=Game(name=BOT_STATUS))


# Not sure if this will do anything but have it here anyway
@client.event
async def on_error(event, *args, **kwargs):
    message = args[0] # Gets the message object
    # logging.warning(traceback.format_exc()) #logs the error
    await client.send_message(message.channel, "You caused an error!") # send the message to the channel

"""
async def list_servers():
    await client.wait_until_ready()
    while not client.is_closed:
        print("Current servers: ")
        for server in client.servers:
            print(server.name)
        await asyncio.sleep(600)
"""

"""
@client.command()
async def bitcoin():
    url = "Uasdasd"
    responce = requests.get(url)
    value = responce.json()['bpi']['USD']['rate']
    await client.say(value)
"""

#client.loop.create_task(list_servers())

# Must be called after Discord functions
client.run(TOKEN)


"""Main Function"""
"""
def main():
    gen_team()
    print(pick_random_champ())


main()
"""
