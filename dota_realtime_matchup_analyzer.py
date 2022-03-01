from urllib.request import urlopen, Request
from urllib.error import HTTPError
from multiprocessing.dummy import Pool as ThreadPool
import json
import time
import re
import os

own_location = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
try:
    with open(os.path.join(own_location, "config.json")) as config_file:
        config = json.load(config_file)
        PATH_TO_CONFIG = config["dota2_folder"] + "\\game\\dota\\server_log.txt"
        NUMBER_OF_MATCHES_TO_ANALYZE = config["number_of_matches_to_analyze"]
        NUMBER_OF_HEROES_DISPLAYED = config["number_of_heroes_displayed"]
        API_URL = config["api_url"]

except FileNotFoundError:
    print("""No "config.json" file found. Please make sure it exists.""")
    os._exit(0)

try:
    with open(os.path.join(own_location, "heroes.json")) as heroes_data_file:
        hero_data = json.load(heroes_data_file)
        HERO_NAMES = dict()
        for hero in hero_data["result"]["heroes"]:
            HERO_NAMES[hero["id"]] = hero["localized_name"]

except FileNotFoundError:
    print("""No "heroes.json" file found. Please make sure it exists.""")
    os._exit(0)


class Player:
    def __init__(self, player_id):
        self.player_id = player_id
        self.profile_is_private = False

        if player_id != "":
            self.profile = get_json_from_url(API_URL + self.player_id)
            if "profile" in self.profile.keys():  # Check if the profile is public.
                self.last_matches = get_json_from_url(
                    API_URL + self.player_id + "/matches?limit=" + str(NUMBER_OF_MATCHES_TO_ANALYZE))
                self.last_matches_won = get_json_from_url(
                    API_URL + self.player_id + "/matches?limit=" + str(NUMBER_OF_MATCHES_TO_ANALYZE) + "&win=1")
                self.win_rate = self.get_win_rate()
                self.nickname = self.get_nickname()
                self.most_played_heroes = self.get_most_played_heroes()
            else:
                self.nickname = "???"
                self.profile_is_private = True

    def get_win_rate(self):
        number_of_matches_won = 0
        current_match = 0
        current_match_won = 0
        while current_match < len(self.last_matches) and current_match_won < len(self.last_matches_won):
            if self.last_matches[current_match]["match_id"] == self.last_matches_won[current_match_won]["match_id"]:
                number_of_matches_won += 1
                current_match_won += 1
            current_match += 1
        return number_of_matches_won / len(self.last_matches)

    def get_nickname(self):
        if self.profile["profile"]["name"] is not None:
            return self.profile["profile"]["name"]
        if self.profile["profile"]["personaname"] is None:  # Sometimes a non private profile does not have a name.
            return "???"
        return self.profile["profile"]["personaname"]

    def get_most_played_heroes(self):
        """Returns a dictionary containing the number of matches played and matches won for each heroes."""
        most_played_heroes = {}
        for match in self.last_matches:
            if match["hero_id"] in most_played_heroes.keys():
                most_played_heroes[match["hero_id"]][0] += 1
            else:
                most_played_heroes[match["hero_id"]] = [1, 0]
            if match in self.last_matches_won:
                most_played_heroes[match["hero_id"]][1] += 1
        return most_played_heroes


def get_hero_name(hero_id):
    """Returns the name of the hero with the given id."""
    if hero_id in HERO_NAMES:
        return HERO_NAMES[hero_id]
    return "UnknownHero"


def get_json_from_url(url):
    """Returns an json object."""
    request = Request(url, headers={'User-Agent': 'Mozilla/5.0'})  # User-Agent is required.
    try:
        with urlopen(request) as x:
            return json.loads(x.read())
    except HTTPError as err:
        print("HTTP error", err.code, "- Please try again later.")
        os._exit(0)


def extract_players(path):
    """Extracts the latest player ids from the server_log file."""
    with open(path, "r+") as file:
        for line in reversed(file.readlines()):
            for i in range(len(line)):
                result = re.findall(r"\[U:\d:\d*", line)
                if result:
                    return [id_string[5:] for id_string in result]
    return []


def player_data_to_string(players):
    player_data = [[] for _ in players]
    if players:
        for i in range(len(players)):
            player_data[i].append(players[i].nickname[:15])
            if not players[i].profile_is_private:
                player_data[i].append(str(round(players[i].win_rate, 2)))
                heroes_sorted = sorted(list(players[i].most_played_heroes.items()), key=lambda x: x[1], reverse=True)
                for hero in heroes_sorted[:NUMBER_OF_HEROES_DISPLAYED]:
                    player_data[i].append(get_hero_name(hero[0]))
                    player_data[i].append(str(hero[1][1]) + "/" + str(hero[1][0]))
                while len(player_data[i]) < 2 + 2*NUMBER_OF_HEROES_DISPLAYED:
                    player_data[i].append("")
                    player_data[i].append("")
            else:
                player_data[i].append("")
                for _ in range(NUMBER_OF_HEROES_DISPLAYED):
                    player_data[i].append("")
                    player_data[i].append("")
    return player_data


def print_analysis(players):
    """Prints the analysis."""
    player_data = player_data_to_string(players)
    max_entry_per_column = [0 for _ in range(len(player_data[0]))]
    for j in range(len(player_data[0])):
        max_length = len(player_data[0][j])
        for i in range(1, len(player_data)):
            max_length = max(max_length, len(player_data[i][j]))
        max_entry_per_column[j] = max_length

    for i in range(len(player_data)):
        for j in range(len(player_data[0])):
            player_data[i][j] = player_data[i][j].ljust(max_entry_per_column[j], " ")
    n = 0
    for player in player_data:
        print(" ".join(player))
        n += 1
        if n == 5:
            print("")


if __name__ == "__main__":
    while True:
        print("Analyzing...\n")
        player_ids = extract_players(PATH_TO_CONFIG)
        player_ids_no_duplicates = list(dict.fromkeys(player_ids))
        print_analysis(ThreadPool(len(player_ids)).map(Player, player_ids_no_duplicates))
        print("Waiting for a new match...")
        while player_ids == extract_players(PATH_TO_CONFIG):  # Wait for a change in the server_log file.
            time.sleep(0.5)
