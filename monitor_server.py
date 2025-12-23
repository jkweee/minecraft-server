import docker
import os
import re
import logging
from server_state import ServerState
from server_state import now
from telert import send
from welcome_message_builder import WelcomeBackMessage

logger = logging.getLogger(__name__)


def send_command(command:str) -> str:
    """Execute a minecraft command via docker container

    :param command: a string representing the command to send
    :return: the command results from the server as a string
    """

    client = docker.from_env()
    container = client.containers.get('minecraft-mc-1')
    # container = client.containers.get('minecraft-dev-mc-1') # dev container

    full_command = 'rcon-cli ' + command 
    exec_log = container.exec_run(full_command, stdout=True, stderr=True).output.decode()

    return str(exec_log)


def query_online_players() -> list:
    """Query server for players who are online

    :return: a list of online players
    """
    
    list_players = str(send_command("list"))  # e.g. "There are 1 of a max of 10 players online: m1nefury"

    players_match = re.search(r"online: (.+)", list_players)
    players = players_match.group(1).split(", ") if players_match else []

    # strip dimension from player name (modrinth: show-dimension-in-name)
    players = [player.replace("Overworld | ", "").replace("Nether | ", "").replace("End | ", "") for player in players]

    return players


def get_previous_server_state() -> ServerState:
    """Read a server state file to get the previous server state

    :return: a ServerState object representing the last time it was queried
    """
    return ServerState("server_state.json")


def get_current_server_state() -> ServerState:
    """Read a server state file and query the server to get the current server state

    :return: a ServerState object representing the server as of now
    """

    state = ServerState("server_state.json") # read from file as default

    # update state on who is online and last seen
    current_players = query_online_players()
    state.set_server_last_queried(now())

    # update existing players
    known_players = state.get_player_details().keys()
    for player in known_players:
        if player in current_players:
            state.set_player_detail(player, "is_online", True)
        else:
            state.set_player_detail(player, "is_online", False)

    # handle new players
    new_players = set(current_players) - set(known_players)
    for player in new_players:
        state.add_new_player(player)
        # TODO: log new player added/detected whatever

    return state


def compare_population_difference(previous_state:ServerState, current_state:ServerState) -> tuple:
    """Get a list of players logging in and out between the previous and current server state.

    Returns a tuple of (logins, logout)

    :param previous_state: previous state of the server
    :param current_state: current state of the server
    :return: a tuple ([login], [logout])
    """

    # we want: a list of logins, a list of logouts, based on the states
    previously_online = set(previous_state.get_online_players())
    currently_online = set(current_state.get_online_players())

    logins = list(currently_online - previously_online)
    logouts = list(previously_online - currently_online)

    return (logins, logouts)


def update_login_and_logout_details(previous_state:ServerState, current_state:ServerState) -> ServerState:
    """Update some player details a current state that can only be done by comparing it to a previous state.

    Specifically, update:
    - last_login
    - last_logout

    :param previous_state: previous state of the server
    :param current_state: current state of the server
    :return: an _updated_ current_state
    """

    # TODO: This should be a function of the class - "update me with a previous state". Arguably can be part of current_state's constructor?
    # by getting a list of who logged in and out, we can update the login details of each of those players
    new_logins, new_logouts = compare_population_difference(previous_state, current_state)
    for player in new_logins:
        current_state.set_player_detail(player, "last_login", now())
    for player in new_logouts:
        current_state.set_player_detail(player, "last_logout", now())

    logger.info("Finished updating a current_state object with latest player information")

    return current_state


def send_welcome_message(current_state:ServerState, target_player:str) -> None:
    """Send a fun welcome message to a player.

    The welcome message can change depending on:
    - Whether the player is new to the server
    - Whether the player has just logged off and back on again

    :param current_state: current state of the server
    :param target_player: username of the player to send the welcome message to
    """
    # This function is to send a message to 1 player only!

    message = ""
    wb = WelcomeBackMessage()

    target_player_is_new = current_state.get_player_detail(target_player, "last_logout") == 0
    target_player_recently_logged_on = current_state.get_player_seconds_since_last_logout(target_player) <= 5 # 60
    
    missed_players = list(current_state.get_list_of_players_online_since_last_logout(target_player))
    target_player_missed_players_while_offline = len(missed_players) > 0

    option_chosen = -1 # debugging

    # construct different welcome message depending on server population since you last logged off
    if target_player_is_new:
        # option 1: new player
        option_chosen = 1
        message = wb.build_message(
            username=target_player,
            new_player=True,
        )
    
    elif not target_player_recently_logged_on and target_player_missed_players_while_offline:
        # you missed a few people since you last logged on - who was the last one?
        count_of_missed_players = 0
        latest_missed_player = ""
        latest_missed_player_logout_timestamp = 0

        for missed_player in missed_players:
            count_of_missed_players += 1
            missed_player_logout_timestamp = current_state.get_player_detail(missed_player, "last_logout")
            if missed_player_logout_timestamp > latest_missed_player_logout_timestamp:
                latest_missed_player_logout_timestamp = missed_player_logout_timestamp
                latest_missed_player = missed_player

        latest_is_less_than_one_hour_ago = (now() - latest_missed_player_logout_timestamp) <= 3600
        if count_of_missed_players > 0 and latest_is_less_than_one_hour_ago:
            # option 2: you missed a few people, the last one just left less than an hour ago
            option_chosen = 2
            message = wb.build_message(
                username=target_player,
                count=count_of_missed_players,
                last_seen_player=latest_missed_player,
                last_seen_time=latest_missed_player_logout_timestamp,
            )
        elif count_of_missed_players > 0:
            # option 3: you missed a few people
            option_chosen = 3
            message = wb.build_message(
                username=target_player,
                count=count_of_missed_players,
            )

    elif target_player_recently_logged_on:
        # option 4: quick login-logout
        option_chosen = 4
        message = wb.build_message(
            username=target_player,
            quick_relog=True,
        )

    else:
        # option 5: generic message
        option_chosen = 5
        message = wb.build_message(
            username=target_player,
        )

    logger.info(f"Sending server message to {target_player} with option {option_chosen}")
    send_command(message)


def send_telegram_updates(previous_state:ServerState, current_state:ServerState) -> None:
    """This function sends a Telegram update whenever there is a change in server population

    :param previous_state: previous state of the server
    :param current_state: current state of the server
    """

    # read previous state and get current state
    previous_player_count = len(previous_state.get_online_players())
    current_players = current_state.get_online_players()
    current_player_count = len(current_players)

    # construct state message
    diff = current_player_count - previous_player_count
    difference_in_players = f"+{str(diff)}" if diff > 0 else str(diff)

    state_message = f"There are {current_player_count} players online ({difference_in_players} △)"
    if current_player_count > 0:
        state_message += f": {current_players}"
    if previous_player_count != current_player_count:
        send(state_message)


if __name__ == "__main__":

    # change working directory to file path
    script_directory = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_directory)
    logger.info(f"Current working directory: {os.getcwd()}")

    # set up logging
    logging.basicConfig(
        filename='monitor_server.log', 
        level=logging.INFO,
        format='%(asctime)s %(levelname)-8s %(filename)s:%(funcName)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    logging.getLogger('').addHandler(console)

    """
        The main function orchestrates ServerState objects and their states
        Its reponsibility is to, in order:
         - Read from state file
         - Update a ServerState object
         - Call other functions that wants to do things with state objects
         - Save to state file

    """

    # 1. Get current and previous state
    previous_state = get_previous_server_state()
    current_state = get_current_server_state()
    current_state = update_login_and_logout_details(previous_state, current_state)

    # 2. App logic goes here
    try:
        send_telegram_updates(previous_state, current_state)
    except Exception as e:
        logger.error(f"Something went wrong when sending Telegram updates: {e}")

    # try:
    #     new_players = compare_population_difference(previous_state, current_state)[0]
    #     for player in new_players:
    #         send_welcome_message(current_state, player)
    # except Exception as e:
    #     logger.error(f"Something went wrong when trying to send welcome message: {e}")

    # 3. Save state to file
    current_state.save_to_file('server_state.json')

