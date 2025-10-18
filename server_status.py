import sys
import docker
import json
import os
import re
import time
import logging
from telert import send

logger = logging.getLogger(__name__)

"""
TODO: the point of this script is to let us know who is currently on, who has been on since I last checked, and whether the server has been backed up since the last player left
- Approach 1: 5-minute timer (additional logic required to see if msg required)
- Approach 2: Read logs as it gets streamed
"""

def execute_minecraft_command(command:str) -> str:
    """Execute a minecraft command via docker container

    :param command: a string representing the command to send
    :return: the command results from the server as a string
    """

    client = docker.from_env()
    container = client.containers.get('minecraft-mc-1')

    exec_log = container.exec_run(f"rcon-cli {command}", stdout=True, stderr=True).output.decode()

    return exec_log


def get_server_population() -> dict:
    """Query server for players and return a dict of the server population

    :return: a dictionary similar to the schema of status.json
    """
    logger.info(f"Querying server to get server population using the 'list' command")

    list_players = str(execute_minecraft_command("list"))  # e.g. "There are 1 of a max of 10 players online: m1nefury"

    num_match = re.search(r"There are (\d+)", list_players)
    num_players = int(num_match.group(1)) if num_match else 0

    players_match = re.search(r"online: (.+)", list_players)
    players = players_match.group(1).split(", ") if players_match else []

    server_population = {
        "version": 1,
        "player_count": num_players,
        "player_list": players,
        "last_checked": int(time.time()),
    }

    logger.info(f"Finished querying server to get server population using the 'list' command and returned {server_population}")

    return server_population


def get_previous_server_population() -> dict:
    """Read previous server population from a json file

    :return: dict representing the last known server population
    """

    logger.info(f"Reading the last known server population")

    if os.path.exists('server_status.json'):
        with open('server_status.json', 'r') as open_file:
            last_population = json.load(open_file)
    else:
        # increment version when making changes
        last_population = {
            "version": 1,
            "player_count": 0,
            "player_list": [],
            "last_checked": int(time.time()),
        }

    logger.info(f"Finished reading the last known server population")

    return last_population


def save_server_population_to_file(server_population:dict) -> None:
    """Save server population to json file

    :param server_population: dict representing the last known server population
    """
    
    logger.info(f"Saving server population data to json")

    with open('server_status.json', 'w') as output:
        json.dump(server_population, output)

    logger.info(f"Finished saving server status to json file")


def main():
    
    # change working directory to file path
    script_directory = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_directory)
    logger.info(f"Current working directory: {os.getcwd()}")

    # set up logging
    logging.basicConfig(filename='server_status.log', level=logging.INFO)
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    logging.getLogger('').addHandler(console)

    # get previous server population
    previous_server_population = get_previous_server_population()
    previous_player_count = previous_server_population["player_count"]

    # get server population
    server_population = get_server_population()
    current_player_count = server_population["player_count"]
    current_players = server_population["player_list"]

    # format difference in players
    diff = current_player_count - previous_player_count
    difference_in_players = f"+{str(diff)}" if diff > 0 else str(diff)

    # construct status message
    status_message = f"There are {current_player_count} players online ({difference_in_players} △)"
    if current_player_count > 0:
        status_message += f": {current_players}"
    if previous_player_count != current_player_count:
        send(status_message)


    logger.info(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {status_message}")

    # save current server population to json
    save_server_population_to_file(server_population)


if __name__ == "__main__":
    main()
