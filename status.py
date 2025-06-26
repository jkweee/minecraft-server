import docker
import subprocess

client = docker.from_env()
container = client.containers.get('minecraft-mc-1')
# command = "list"
command = "help"

"""
TODO: the point of this script is to let us know who is currently on, who has been on since I last checked, and whether the server has been backed up since the last player left
"""

exec_log = container.exec_run(f"rcon-cli {command}", stdout=True, stderr=True).output.decode()

print(exec_log)
