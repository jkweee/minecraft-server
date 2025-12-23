import time
import random
import json
import logging

class WelcomeBackMessage:
    """Builds a custom welcome back message with additional fun flavours depending on server population characteristics.
    """

    def __init__(self):

        # Templates
        self.simple_templates = [
            "Welcome back {username}!",
            "It's been some time {username}, welcome back!",
        ]

        # Templates for new players
        self.templates_for_new_players = [
            "Welcome to our server {username}!",
            "A new face joins us! Welcome, {username}!",
            "Are you a miner or a crafter? Either way, welcome {username}!"
        ]

        # Templates for quick login-logouts
        self.templates_for_quick_relogs = [
            "Well, that was quick. Welcome back {username}!",
            "And the quickest relog award goes to... {username}!",
        ]

        # Templates with count of players (basic)
        self.templates_with_counts = [
            "Welcome back {username}! There were {count} players since we last saw you.",
            "Hey {username}! {count} adventurers passed through while you were away.",
            "Glad you're back, {username}! {count} players mined and crafted since your last login.",
            "The land remembers you, {username}! {count} travelers crossed paths here.",
            "Welcome home, {username}! {count} heroes came and went while you were gone.",
        ]

        # Templates with count of players and last-seen details
        self.templates_with_counts_and_last_seen = [
            "Welcome back {username}! {count} players joined since you left. Last seen: {last_seen_player}, {last_seen_time}.",
            "Hey {username}! {count} friends stopped by. The most recent was {last_seen_player}, {last_seen_time}.",
            "Welcome back {username}! Since you left, {count} players logged on. Last sighting: {last_seen_player}, {last_seen_time}.",
        ]

        # Subtle flavor lines
        self.flavor_lines = [
            "The villagers are still gossiping about it.",
            "The cows remain unimpressed.",
            "The Enderman says hi.",
            "The chickens staged a minor rebellion.",
            "The creepers were suspiciously quiet.",
            "The campfire still smells of adventure.",
            "The wolves are waiting for belly rubs.",
            "The redstone contraptions kept humming along.",
        ]


    def unix_to_relative_descriptor(past_timestamp: int) -> str:
        """
        Converts a unix timestamp to a relative English descriptor (e.g., '1 minute ago', '2 days ago').
        Uses the largest appropriate unit (days, hours, minutes, seconds).
        """
        now = int(time.time())
        diff = max(0, now - past_timestamp)
        if diff < 60:
            return f"{diff} second{'s' if diff != 1 else ''} ago"
        elif diff < 3600:
            minutes = diff // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif diff < 86400:
            hours = diff // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = diff // 86400
            return f"{days} day{'s' if days != 1 else ''} ago"


    def build_message(self, username:str, count:int=0, last_seen_player:str=None, last_seen_time:int=None, quick_relog:bool=False, new_player:bool=False) -> str:
        """Builds a welcome message with optional flavours depending on what is passed in.

        Both last_seen_player and last_seen_time need to be passed in for the base message to change.

        :param username: player to send message to
        :param count: number of players missed since the player last logged on
        :param last_seen_player: username of latest missed player, defaults to None
        :param last_seen_time: logout timestamp of latest missed player, defaults to None
        :param quick_relog: if this was a message for someone who quickly relogged, defaults to None
        :return: a formatted tellraw command string containing the welcome message
        """

        # build the base text by applying params to the templates
        if new_player:
            template = random.choice(self.templates_for_new_players)
            base_text = template.format(
                username=username
            )
        elif quick_relog:
            template = random.choice(self.templates_for_quick_relogs)
            base_text = template.format(
                username=username
            )
        elif count == 0:
            template = random.choice(self.simple_templates)
            base_text = template.format(
                username=username
            )
        elif last_seen_player and last_seen_time:
            template = random.choice(self.templates_with_counts_and_last_seen)
            base_text = template.format(
                username=username,
                count=count,
                last_seen_player=last_seen_player,
                last_seen_time=self.unix_to_relative_descriptor(last_seen_time) # convert timestamp to descriptor
            )
        else:
            template = random.choice(self.templates_with_counts)
            base_text = template.format(
                username=username, 
                count=count
            )

        # apply formatting to different components of the base text (mainly: emphasise the username)
        idx = base_text.find(username)
        components = []
        if idx != -1:
            pre = base_text[:idx]
            post = base_text[idx + len(username):]
            # pre-text
            if pre:
                components.append({"text": pre, "color": "white"})
            # username
            components.append({"text": username, "bold": False, "italic": False,"color": "aqua"})
            # post-text
            if post:
                components.append({"text": post, "color": "white"})
        else:
            # Fallback: no username found (shouldn't happen if templates include it)
            components.append({"text": base_text, "color": "white"})

        # Optional flavor line (subtle)
        if random.random() < 0.6 and not quick_relog and not new_player:
            flavor = random.choice(self.flavor_lines)
            components.append({"text": " " + flavor, "color": "gray", "italic": True})

        # Build tellraw JSON with per-part styling
        # A note on escape characters:
        # - Escape all double quotes inside the JSON when sending to rcon-cli
        # - However, we also need to escape the escape character so that Python doesn't remove it
        tellraw_json = {"text": "", "extra": components}
        tellraw_string = json.dumps(tellraw_json).replace('"', '\\"')  # escape the escape characters
        command = "tellraw " + username + " \"" + tellraw_string + "\""

        return command
