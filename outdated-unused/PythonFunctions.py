import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pytz import timezone

import json
import discord

from pyrez.api import PaladinsAPI
import my_utils as helper


file_name = "token"
# Gets ID and KEY from a file
with open(file_name, 'r') as f:
    TOKEN = f.readline().strip()  # Does nothing
    ID = int(f.readline())
    KEY = f.readline()
f.close()


paladinsAPI = PaladinsAPI(devId=ID, authKey=KEY)


# Get the player id for a player based on their name. First it checks a dictionary and if they are not in there then
# it does an API call to get the player's id. Then it writes that id to the dictionary. Helps save API calls.
def get_player_id(player_name):
    player_name = player_name.lower()
    with open("player_ids") as json_f:
        player_ids = json.load(json_f)

    # This player is already in the dictionary and therefor we don't need to waste an api call to get the player id.
    if player_name in player_ids:
        return player_ids[player_name]
    else:
        player = paladinsAPI.getPlayer(player_name)
        if not player:  # invalid name
            return -1
        new_id = player.playerId
        player_ids[player_name] = new_id  # store the new id in the dictionary

        # need to update the file now
        print("Added a new player the dictionary: " + player_name)
        with open("player_ids", 'w') as json_f:
            json.dump(player_ids, json_f)
        return new_id


# Calculates the kda
def cal_kda(kills, deaths, assists):
    if assists == 0:  # Could happen
        assists = 1
    if deaths == 0:  # Prefect KDA
        return str(kills + (assists/2))
    return str('{0:.2f}'.format(float(kills + (assists/2))/deaths))


# Est Time zone for logging function calls
def get_est_time():
    # using just timezone 'EST' does not include daylight savings
    return datetime.now(timezone('US/Eastern')).strftime("%H:%M:%S %m/%d/%Y")


def get_champ_image(champ_name):
    champ_name = champ_name.lower()
    # These are special cases that need to ge checked
    if "bomb" in champ_name:
        return "https://web2.hirez.com/paladins/champion-icons/bomb-king.jpg"
    if "mal" in champ_name:
        return "https://web2.hirez.com/paladins/champion-icons/maldamba.jpg"
    if "sha" in champ_name:
        return "https://web2.hirez.com/paladins/champion-icons/sha-lin.jpg"

    url = "https://web2.hirez.com/paladins/champion-icons/" + str(champ_name) + ".jpg"
    return url


# Converts the match name so that its small enough to fit on one line
def convert_match_type(match_name):
    if "Practice" in match_name:
        return "Bot Match"
    elif "TDM" in match_name:
        return "TDM"
    elif "Onslaught" in match_name:
        return "Onslaught"
    elif "Ranked" in match_name:
        return "Ranked"
    elif "End Times" in match_name:     # Event name
        return "End Times"
    elif "(Siege)" in match_name:       # Test Maps (WIP Thrones)
        return "Test Maps"
    else:
        return "Siege"


# Returns simple match history details for many matches
# TODO Once this is in a cog just have the client send two messages once amount > 30
def get_history(player_name, amount):
    if amount > 30 or amount <= 1:
        return "Please enter an amount between 2-30"
    player_id = get_player_id(player_name)
    if player_id == -1:
        return "Can't find the player: " + player_name + \
               ". Please make sure the name is spelled correctly (Capitalization does not matter)."
    paladins_data = paladinsAPI.getMatchHistory(player_id)
    # paladins_data = paladinsAPI.getMatchDetailsBatch(player_id) # Need to look into this
    count = 0
    match_data = ""
    for match in paladins_data:
        # Check to see if this player does have match history
        if match.playerName is None:
            if count == 0:
                return "Player does not have recent match data."
            else:
                break
        count += 1
        ss = str('+{:10}{:4}{:3}:00 {:9} {:9} {:5} ({}/{}/{})\n')
        kills = match.kills
        deaths = match.deaths
        assists = match.assists
        kda = cal_kda(kills, deaths, assists)
        ss = ss.format(match.godName, match.winStatus, match.matchMinutes, convert_match_type(match.mapGame),
                       match.matchId, kda, kills, deaths, assists)
        # Used for coloring
        if match.winStatus == "Loss":
            ss = ss.replace("+", "-")

        match_data += ss
        if count == amount:
            break

    title = str('{}\'s last {} matches:\n\n').format(str(player_name), count)
    title += str('{:11}{:4}  {:4} {:9} {:9} {:5} {}\n').format("Champion", "Win?", "Time", "Mode", "Match ID", "KDA",
                                                               "Detailed")
    title += match_data
    return title


# Returns simple match history details
def get_last(player_name, match_id):
    player_id = get_player_id(player_name)

    if player_id == -1:
        match_data = "Can't find the player: " + player_name + \
               ". Please make sure the name is spelled correctly (Capitalization does not matter)."
        embed = discord.Embed(
            description=match_data,
            colour=discord.colour.Color.dark_teal()
        )
        return embed

    paladins_data = paladinsAPI.getMatchHistory(player_id)
    for match in paladins_data:
        # Check to see if this player does have match history
        if match.playerName is None:
            break

        if match_id == -1 or match_id == match.matchId:
            match_data = str('{}\'s {} match:\n\n').format(str(player_name), str(match.mapGame).replace("LIVE", ""))
            ss = str('`Match Status: {} ({} mins)\nChampion: {}\nKDA: {} ({}-{}-{})\nDamage: {}\nDamage Taken: {}'
                     '\nHealing: {} \nObjective Time: {}`\n')
            kills = match.kills
            deaths = match.deaths
            assists = match.assists
            kda = cal_kda(kills, deaths, assists)
            match_data += ss.format(match.winStatus, match.matchMinutes, match.godName, kda, kills, deaths, assists,
                                    match.damage, match.damageTaken, match.healing, match.objectiveAssists)

            embed = discord.Embed(
                description=match_data,
                colour=discord.colour.Color.dark_teal()
            )

            embed.set_thumbnail(url=get_champ_image(match.godName))

            return embed

    # If the match id could not be found
    embed = discord.Embed(
        description="Could not find a match with the match id: " + str(match_id),
        colour=discord.colour.Color.dark_teal()
    )

    # If player has not played recently
    if match_id == -1:
        embed.description = "Player does not have recent match data."

    return embed


# n1 = wins and n2 = total matches
def create_win_rate(n1, n2):
    if n2 == 0:  # This means they have no data for the ranked split/season
        return "0"
    return str('{0:.2f}'.format((n1 / n2) * 100))


# (Currently unused)
# Converts the number to the proper name
def convert_rank(x):
    return {
        1: "Bronze 5",
        2: "Bronze 4",
        3: "Bronze 3",
        4: "Bronze 2",
        5: "Bronze 1",
        6: "Silver 5",
        7: "Silver 4",
        8: "Silver 3",
        9: "Silver 2",
        10: "Silver 1",
        11: "Gold 5",
        12: "Gold 4",
        13: "Gold 3",
        14: "Gold 2",
        15: "Gold 1",
        16: "Platinum 5",
        17: "Platinum 4",
        18: "Platinum 3",
        19: "Platinum 2",
        20: "Platinum 1",
        21: "Diamond 5",
        22: "Diamond 4",
        23: "Diamond 3",
        24: "Diamond 2",
        25: "Diamond 1",
        26: "Master",
        27: "GrandMaster",
    }.get(x, "Un-Ranked")


# Uses Paladins API to get overall stats for a player
def get_player_stats_api(player_name):
    # Player level, played hours, etc
    player_id = get_player_id(player_name)
    if player_id == -1:
        return "Can't find the player: " + player_name + \
               ". Please make sure the name is spelled correctly (Capitalization does not matter)."
    info = paladinsAPI.getPlayer(player_id)

    ss = ""

    # Basic Stats
    ss += "Casual stats: \n"
    ss += "Name: " + str(info.playerName) + "\n"
    ss += "Account Level: " + str(info.accountLevel) + "\n"
    total = int(info.wins) + int(info.losses)
    ss += "Win Rate: " + create_win_rate(int(info.wins), total) + "% out of " + str(total) + " matches.\n"
    ss += "Times Deserted: " + str(info.leaves) + "\n\n"

    # Ranked Info
    ranked = info.rankedKeyboard
    ss += "Ranked stats for Season " + str(ranked.currentSeason) + ":\n"
    # Rank (Masters, GM, Diamond, etc)
    ss += "Rank: " + str(ranked.currentRank) + "\nTP: " + str(ranked.currentTrumpPoints) + " Position: " + \
          str(ranked.leaderboardIndex) + "\n"

    win = int(ranked.wins)
    lose = int(ranked.losses)

    ss += "Win Rate: " + create_win_rate(win, win + lose) + "% (" + '{}-{}'.format(win, lose) + ")\n"
    ss += "Times Deserted: " + str(ranked.leaves) + "\n\n"

    # Extra info
    ss += "Extra details: \n"
    ss += "Account created on: " + str(info.createdDatetime).split()[0] + "\n"
    ss += "Last login on: " + str(info.lastLoginDatetime).split()[0] + "\n"
    ss += "Platform: " + str(info.platform) + "\n"
    data = info.json
    ss += "MasteryLevel: " + str(data["MasteryLevel"]) + "\n"
    ss += "Steam Achievements completed: " + str(info.totalAchievements) + "/58\n"

    return ss


# Gets stats for a champ using Paladins API
def get_champ_stats_api(player_name, champ, simple):
    # Gets player id and error checks
    player_id = get_player_id(player_name)
    if player_id == -1:
        match_data = "Can't find the player: " + player_name + \
                     ". Please make sure the name is spelled correctly (Capitalization does not matter)."
        embed = discord.Embed(
            description=match_data,
            colour=discord.colour.Color.dark_teal()
        )
        return embed
    stats = paladinsAPI.getChampionRanks(player_id)

    if "Mal" in champ:
        champ = "Mal Damba"

    ss = ""
    t_wins = 0
    t_loses = 0
    t_kda = 0
    count = 0

    for stat in stats:
        count += 1
        wins = stat.wins
        losses = stat.losses
        kda = cal_kda(stat.kills, stat.deaths, stat.assists)
        # champ we want to get the stats on
        if stat.godName == champ:
            win_rate = create_win_rate(wins, wins + losses)
            level = stat.godLevel

            last_played = str(stat.lastPlayed)
            if not last_played:  # Bought the champ but never played them
                break

            ss = str('Champion: {} (Lv {})\nKDA: {} ({}-{}-{}) \nWin Rate: {}% ({}-{}) \nLast Played: {}')

            ss = ss.format(champ, level, kda, stat.kills, stat.deaths, stat.assists,
                           win_rate, wins, losses, str(stat.lastPlayed).split()[0])
            if simple == 1:
                win_rate += " %"
                kda = "(" + kda + ")"
                ss = str('*{:18} Lv. {:3}  {:7}  {:6}\n')
                ss = ss.format(champ, str(level), win_rate, kda)
                """This Block of code adds color based on Win Rate"""
                if "???" in win_rate:
                    pass
                elif (float(win_rate.replace(" %", ""))) > 55.00:
                    ss = ss.replace("*", "+")
                elif (float(win_rate.replace(" %", ""))) < 50.00:
                    ss = ss.replace("*", "-")
                """^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"""
        # Global win rate and kda
        t_wins += wins
        t_loses += losses
        t_kda += float(kda)

    # They have not played this champion yet
    if ss == "":
        ss = "No data for champion: " + champ + "\n"
        if simple == 1:
            ss = str('*{:18} Lv. {:3}  {:7}  {:6}\n')
            ss = ss.format(champ, "???", "???", "???")

    # Global win rate and kda
    global_ss = str("\n\nGlobal KDA: {}\nGlobal Win Rate: {}% ({}-{})")
    win_rate = create_win_rate(t_wins, t_wins + t_loses)
    t_kda = str('{0:.2f}').format(t_kda / count)
    global_ss = global_ss.format(t_kda, win_rate, t_wins, t_loses)
    ss += global_ss

    # Create an embed
    if simple != 1:
        embed = discord.Embed(
            colour=discord.colour.Color.dark_teal()
        )
        embed.add_field(name=player_name + "'s stats: ", value='`' + ss + '`', inline=False)
        embed.set_thumbnail(url=get_champ_image(champ))
        return embed

    return ss

# print(get_champ_stats_api("FeistyJalapeno", "evie", 0))


# Creates Json we can use
def create_json(raw_data):
    json_data = str(raw_data).replace("'", "\"").replace("None", "0").replace("Mal\"", "Mal\'")
    return json.loads(json_data)


# Gets KDA and Win Rate for a player from Guru
def get_global_kda(player_name):
    url = "http://paladins.guru/profile/pc/" + player_name

    soup = BeautifulSoup(requests.get(url, headers={'Connection': 'close'}).text, 'html.parser')
    sup = str(soup.get_text())

    sup = sup.split(" ")
    data = list(filter(None, sup))

    stats = []

    # Gets account name and level
    for i, row in enumerate(data):
        if data[i] == "Giveaway":
            stats.append(data[i + 2])
            stats.append(data[i + 1])
            break

    # Gets Global wins and loses
    for i, row in enumerate(data):
        if data[i] == "Loss":
            new_s = str(data[i + 4].replace("(", "") + " %")
            stats.append(new_s)
            break

    # Gets Global KDA
    for i, row in enumerate(data):
        if data[i] == "KDA":
            stats.append(data[i + 6])
            break

    # Error checking to make sure that the player was found on the site
    if 'not' in stats:
        # error = "Could not the find player " + player_name + \
        #       ". Please make sure the name is spelled right (capitalization does not matter)."
        error = [player_name, "???", "???", "???"]
        return error

    # Puts all the info into one string to print
    # global_stats = "Name: " + stats.pop(0) + " (Lv. " + stats.pop(0) + ")\n" + "Win Rate: " + \
    #                stats.pop(0) + "\n" + "Global KDA: " + stats.pop(0)
    # return global_stats
    return stats


# Gets details about a player in a current match using the Paladins API
def get_player_in_match(player_name, option):
    # Data Format
    # {'Match': 795950194, 'match_queue_id': 452, 'personal_status_message': 0, 'ret_msg': 0, 'status': 3,
    # 'status_string': 'In Game'}

    # Gets player id and error checks
    player_id = get_player_id(player_name)
    if player_id == -1:
        return "Can't find the player: " + player_name + \
               ". Please make sure the name is spelled correctly (Capitalization does not matter)."
    # j = create_json(paladinsAPI.getPlayerStatus(player_id))
    # """ JSON FIX
    data = paladinsAPI.getPlayerStatus(player_id)
    data = data.json
    # """
    # print(type(paladinsAPI.getPlayerStatus(player_id)))
    # data = paladinsAPI.getPlayerStatus(player_id)
    # print(data)

    if data == 0:
        return str("Player " + player_name + " is not found.")
    match_id = data["Match"]
    if data['status'] == 0:
        return "Player is offline."
    elif data['status'] == 1:
        return "Player is in lobby."
    elif data['status'] == 2:
        return "Player in champion selection."

    # match_queue_id = 424 = Siege
    # match_queue_id = 445 = Test Maps (NoneType) --> no json data
    # match_queue_id = 452 = Onslaught
    # match_queue_id = 469 = DTM
    # match_queue_id = 486 = Ranked (Invalid)

    match_string = "Unknown match Type"
    if data["match_queue_id"] == 424:
        match_string = "Siege"
    elif data["match_queue_id"] == 445:
        return "No data for Test Maps."
    elif data["match_queue_id"] == 452:
        match_string = "Onslaught"
    elif data["match_queue_id"] == 469:
        match_string = "Team Death Match"
    elif data["match_queue_id"] == 486:  # Should be fixed now
        match_string = "Ranked"
        # return "Ranked is currently not working."

    # Data Format
    # {'Account_Level': 17, 'ChampionId': 2493, 'ChampionName': 'Koga', 'Mastery_Level': 10, 'Match': 795511902,
    # 'Queue': '424', 'SkinId': 0, 'Tier': 0, 'playerCreated': '11/10/2017 10:00:03 PM', 'playerId': '12368291',
    # 'playerName': 'NabbitOW', 'ret_msg': None, 'taskForce': 1, 'tierLosses': 0, 'tierWins': 0}
    try:
        players = paladinsAPI.getMatchPlayerDetails(match_id)
    except helper.MyException:
        return "An problem occurred. Please make sure you are not using this command on the event mode."
    # print(players)
    team1 = []
    team1_champs = []
    team2 = []
    team2_champs = []
    for player in players:
        # j = create_json(player)
        # name = (j["playerName"])
        name = str(player.playerName)  # Some names are not strings (example: symbols, etc.)

        # testing to see if character name is avaiable
        # print(player.playerName, player.godName) # Yes it is

        if int(player.taskForce) == 1:
            team1.append(name)
            team1_champs.append(player.godName)
        else:
            team2.append(name)
            team2_champs.append(player.godName)

    match_data = ""
    match_data += player_name + " is in a " + match_string + " match."  # Match Type
    # print(match_data)
    match_data += str('\n\n{:18}  {:7}  {:8}  {:6}\n\n').format("Player name", "Level", "Win Rate", "KDA")

    for player, champ in zip(team1, team1_champs):
        # print(get_global_kda(player))
        pl = get_global_kda(player)
        ss = str('*{:18} Lv. {:3}  {:8}  {:6}\n')
        ss = ss.format(pl[0], str(pl[1]), pl[2], pl[3])
        """This Block of code adds color based on Win Rate"""
        if "???" in pl[2]:
            pass
        elif(float(pl[2].replace(" %", ""))) > 55.00:
            ss = ss.replace("*", "+")
        elif (float(pl[2].replace(" %", ""))) < 50.00:
            ss = ss.replace("*", "-")
        """^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"""
        match_data += ss

        # Add in champ stats
        if option == "-a":
            match_data += get_champ_stats_api(player, champ, 1)

    match_data += "\n"

    for player, champ in zip(team2, team2_champs):
        # print(get_global_kda(player))
        pl = get_global_kda(player)
        ss = str('*{:18} Lv. {:3}  {:8}  {:6}\n')
        ss = ss.format(pl[0], str(pl[1]), pl[2], pl[3])
        """This Block of code adds color based on Win Rate"""
        if "???" in pl[2]:
            pass
        elif (float(pl[2].replace(" %", ""))) > 55.00:
            ss = ss.replace("*", "+")
        elif (float(pl[2].replace(" %", ""))) < 50.00:
            ss = ss.replace("*", "-")
        """^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"""
        match_data += ss

        # Add in champ stats
        if option == "-a":
            match_data += get_champ_stats_api(player, champ, 1)

    return match_data


# Helper function to the get_player_elo(player_name) function
def return_mode(name):
    mode = ""
    if name == "Siege":
        mode += "Siege rating: \n"
    elif name == "Survival":
        mode += "Onslaught rating: \n"  # Rename to onslaught
    elif name == "Deathmatch":
        mode += "Team Deathmatch rating: \n"
    else:
        mode += "Overall Guru Score: \n"
    return mode


# Gets elo's for a player from the Paladins Guru site?
def get_player_elo(player_name):
    url = "http://paladins.guru/profile/pc/" + str(player_name) + "/casual"
    soup = BeautifulSoup(requests.get(url, headers={'Connection': 'close'}).text, 'html.parser')
    soup = str(soup.get_text()).split(" ")
    data = list(filter(None, soup))

    stats = ""
    mode = ""

    # Gets elo information below
    for i, row in enumerate(data):
        if data[i] == "Siege" or data[i] == "Survival" or data[i] == "Deathmatch" or data[i] == "Score":
            if data[i+1] == "Rank":
                mode = return_mode(data[i])
                mode += str("Rank: " + data[i + 2])             # Rank
                mode += str(" (Top " + data[i + 5] + ")\n")     # Rank %
                mode += str("Elo: " + data[i + 6] + "\n")       # Elo
                mode += str("Win Rate: " + data[i + 8])         # Win Rate
                mode += str(" (" + data[i + 10] + "-")          # Wins
                mode += data[i + 11] + ")"                      # Loses
                stats += mode + "\n\n"
            elif data[i+1] == "-":
                mode = return_mode(data[i])
                mode += str("Rank: ???")                    # Rank
                mode += str(" (Top " + "???" + ")\n")       # Rank %
                mode += str("Elo: " + data[i + 2] + "\n")   # Elo
                mode += str("Win Rate: " + data[i + 4])     # Win Rate
                mode += str(" (" + data[i + 6] + "-")       # Wins
                mode += data[i + 7] + ")"                   # Loses
                stats += mode + "\n\n"
        if data[i] == "Siege":
            if data[i+1] == "Normal:":
                break

    # Checking if the player has any data for this season
    if mode == "":
        return "The player: " + player_name + " does not have any matches this season."

    return stats


# based on the user input decides which function to call
def get_stats(player_name, champ):
    player_name = str(player_name)
    champ = str(champ).lower().title()  # Need since some champ names are two words

    # Personal overall stats
    if champ == "Me":
        # return get_global_stats(player_name)
        return get_player_stats_api(player_name)

    # Personal elo stats
    if champ == "Elo":
        return get_player_elo(player_name)

    # Stats for a certain champion
    return get_champ_stats_api(player_name, champ, simple=0)
