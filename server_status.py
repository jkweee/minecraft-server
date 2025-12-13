import sys
import docker
import json
import os
import re
import time
import logging
from enum import Enum
from telert import send

logger = logging.getLogger(__name__)

def now() -> int:
    """Returns now as int in unix timestamp"""
    return int(time.time())


class ServerStatus:
    """A class to represent a server status. Can be read from or saved to a JSON file

    Some logic for handy reference:
    - If login > logout: player is online
    - If login < logout: player is offline
    - "Last seen" is the last time the player appeared during a query
    - Player list is a complete list of all players that have logged on.

    """

    def __init__(self, filepath:str=""):
        """If a filepath is provided, read from status file automatically.

        :param filepath: file to read from
        """
        if filepath != "":
            self.read_from_file(filepath)
        else:
            self.read_from_file()


    def read_from_file(self, filepath:str="server_status.json") -> None:
        """Read previous status from file. Uses defaults if file doesn't exist.

        :param filepath: file to read from, defaults to "server_status.json"
        """
        if os.path.exists(filepath):
            with open(filepath, 'r') as open_file:
                file = json.load(open_file)
                self.version = file['version']
                self.server_last_queried = file['server_last_queried']
                self.player_details = file['player_details']
        else:
            self.version = 2 # schema version
            self.server_last_queried = now()
            self.player_details = {}


    def save_to_file(self, filepath:str="server_status.json") -> None:
        """Saves the server status to a file.

        :param filepath: file to save to, defaults to "server_status.json"
        """
        server_population = {
            "version": 2,
            "server_last_queried": self.server_last_queried,
            "player_details": self.player_details if len(self.player_details) > 0 else "null",
        }

        with open(filepath, 'w') as output:
            json.dump(server_population, output, indent=4)


    def get_online_players(self) -> list:
        """Returns a list of players where is_online = True

        :return: _description_
        """
        online_players = []
        for player, details in self.player_details.items():
            if details["is_online"] == True:
                online_players.append(player)

        return online_players


    # boilerplate (sigh)
    def set_version(self, version: int) -> None:
        self.version = version

    def get_version(self) -> int:
        return self.version

    def set_server_last_queried(self, timestamp: int) -> None:
        self.server_last_queried = timestamp

    def get_server_last_queried(self) -> int:
        return self.server_last_queried

    def set_player_details(self, player_details: dict) -> None:
        self.player_details = player_details

    def get_player_details(self) -> dict:
        return self.player_details

    def set_player_detail(self, player: str, detail: dict, value) -> None:
        self.player_details[player][detail] = value

    def get_player_detail(self, player: str, detail: dict) -> dict:
        return self.player_details[player][detail]

    def __str__(self) -> str:

        status_as_string = str({
            "version": 2,
            "server_last_queried": self.server_last_queried,
            "player_details": self.player_details
        })

        return status_as_string



def query_server(command:str) -> str:
    """Execute a minecraft command via docker container

    :param command: a string representing the command to send
    :return: the command results from the server as a string
    """

    client = docker.from_env()
    # container = client.containers.get('minecraft-mc-1')
    container = client.containers.get('minecraft-dev-mc-1') # should this throw error???

    exec_log = container.exec_run(f"rcon-cli {command}", stdout=True, stderr=True).output.decode()

    return str(exec_log)


def query_online_players() -> list:
    """Query server for players who are online

    :return: a list of online players
    """
    
    list_players = str(query_server("list"))  # e.g. "There are 1 of a max of 10 players online: m1nefury"

    players_match = re.search(r"online: (.+)", list_players)
    players = players_match.group(1).split(", ") if players_match else []

    return players


def get_previous_server_status() -> ServerStatus:
    """Gets the previous server status by reading from server_status.json

    :return: a ServerStatus object
    """
    return ServerStatus("server_status.json")


def get_current_server_status() -> ServerStatus:

    status = ServerStatus("server_status.json") # read from file as default

    # update status on who is online and last seen
    current_players = query_online_players()
    status.set_server_last_queried(now())
    for player in status.get_player_details().keys():
        if player in current_players:
            status.set_player_detail(player, "is_online", True)
        else:
            status.set_player_detail(player, "is_online", False)

    return status


def compare_population_difference(previous_status:ServerStatus, current_status:ServerStatus) -> tuple:
    """Given the previous and current status, get a list of who logged on and who logged off in between
    Returns a tuple of (logins, logout)

    :param previous_status: _description_
    :param current_status: _description_
    :return: a tuple (list of players who logged in, list of players who logged out)
    """

    # we want: a list of logins, a list of logouts, based on the states
    previously_online = set(previous_status.get_online_players())
    currently_online = set(current_status.get_online_players())

    logins = list(currently_online - previously_online)
    logouts = list(previously_online - currently_online)

    return (logins, logouts)


def update_login_and_logout_details(current_status:ServerStatus) -> ServerStatus:
    # argument should be a ServerStatus representing the latest status

    previous_status = get_previous_server_status()

    new_logins, new_logouts = compare_population_difference(previous_status, current_status)
    for player in new_logins:
        current_status.set_player_detail(player, "last_login", now())
    for player in new_logouts:
        current_status.set_player_detail(player, "last_logout", now())

    return current_status



def send_telegram_updates() -> None:

    """
        This function sends a Telegram update whenever there is a change in server population
        Note:
        - Uses logic built for the old status json
        - This doesn't update the last_login or last_logout details
    """

    # read previous state and get current state
    previous_status = get_previous_server_status()
    previous_player_count = len(previous_status.get_online_players())
    current_status = get_current_server_status()
    current_players = current_status.get_online_players()
    current_player_count = len(current_players)

    # construct status message
    diff = current_player_count - previous_player_count
    difference_in_players = f"+{str(diff)}" if diff > 0 else str(diff)

    status_message = f"There are {current_player_count} players online ({difference_in_players} △)"
    if current_player_count > 0:
        status_message += f": {current_players}"
    if previous_player_count != current_player_count:
        send(status_message)

    # save and log
    current_status.save_to_file('server_status.json')
    logger.info(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {status_message}")




if __name__ == "__main__":

    # change working directory to file path
    script_directory = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_directory)
    logger.info(f"Current working directory: {os.getcwd()}")

    # set up logging
    logging.basicConfig(
        filename='server_status.log', 
        level=logging.INFO,
        format='%(asctime)s %(levelname)-8s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    logging.getLogger('').addHandler(console)

    send_telegram_updates()
