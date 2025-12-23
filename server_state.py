import os
import json
import time
import logging

logger = logging.getLogger(__name__)

def now() -> int:
    """Returns now as int in unix timestamp"""
    return int(time.time())

class ServerState:
    """A class to represent a server population state. Can be read from or saved to a JSON file

    Some logic for handy reference:
    - If login > logout: player is online
    - If login < logout: player is offline
    - "Last seen" is the last time the player appeared during a query
    - Player list is a complete list of all players that have logged on.

    """

    def __init__(self, filepath:str=""):
        """If a filepath is provided, read from state file automatically.

        :param filepath: file to read from
        """
        if filepath != "":
            self.read_from_file(filepath)
        else:
            self.read_from_file()


    def read_from_file(self, filepath:str="server_state.json") -> None:
        """Read previous state from file. Uses defaults if file doesn't exist.

        :param filepath: file to read from, defaults to "server_state.json"
        """
        if os.path.exists(filepath):
            with open(filepath, 'r') as open_file:
                file = json.load(open_file)
                self.version = file['version']
                self.server_last_queried = file['server_last_queried']
                self.player_details = file['player_details'] if file['player_details'] != None else {}
        else:
            self.version = 2 # schema version
            self.server_last_queried = now()
            self.player_details = {}


    def save_to_file(self, filepath:str="server_state.json") -> None:
        """Saves the server state to a file.

        :param filepath: file to save to, defaults to "server_state.json"
        """
        server_population = {
            "version": 2,
            "server_last_queried": self.server_last_queried,
            "player_details": self.player_details if len(self.player_details) > 0 else None,
        }

        with open(filepath, 'w') as output:
            json.dump(server_population, output, indent=4)
            logger.info(f"Saved server state to {filepath}")


    def get_online_players(self) -> list:
        """Returns a list of players where is_online = True

        :return: _description_
        """
        online_players = []
        for player, details in self.player_details.items():
            if details["is_online"] == True:
                online_players.append(player)

        return online_players


    def add_new_player(self, player:str) -> None:
        """Adds a new player with default values and mark them as online. Assumption: we only call this function when discovering them online for the first time
        """
        self.player_details[player] = {
            "last_login": now(),
            "last_logout": 0,
            "is_online": True
        }


    def get_player_seconds_since_last_logout(self, player: str) -> int:
        """
        Returns the time difference in seconds between the player's last logout and next login.
        If the player is currently online, returns the difference between last_logout and last_login.
        Else, return -1

        :param player: name of the player
        :return diff: time in seconds between last logout and current login, -1 otherwise
        """
        diff = -1

        last_login = self.get_player_detail(player, 'last_login')
        last_logout = self.get_player_detail(player, 'last_logout')

        # only return positive difference if login > logout (i.e. currently online)
        if last_login > last_logout:
            diff = last_login - last_logout
    
        return diff


    def get_list_of_players_online_since_last_logout(self, target_player: str) -> list:
        """Return a list of other players who have been online since the target player was last offline
        Does not include other players who are currently still online

        :param target_player: player to compare to
        :return: a list of players
        """

        players_since_last_logout = []

        last_logout = self.get_player_detail(target_player, 'last_logout')
        for player, details in self.get_player_details().items():
            if player != target_player and details["last_logout"] > last_logout:
                players_since_last_logout.append(player)
        
        return players_since_last_logout



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

    def set_player_detail(self, player: str, detail: str, value) -> None:
        self.player_details[player][detail] = value

    def get_player_detail(self, player: str, detail: str) -> dict:
        return self.player_details[player][detail]

    def __str__(self) -> str:

        state_as_string = str({
            "version": 2,
            "server_last_queried": self.server_last_queried,
            "player_details": self.player_details
        })

        return state_as_string