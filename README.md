# minecraft-server

Using Docker Compose to deploy and maintain our Minecraft server.

Some custom scripts are used for monitoring and sending custom welcome messages.

Server details:

- Fabric for Minecraft **1.21.10**
- 🛍️ Keep inventory is **on**
- Server mods - all vanilla clients can connect seamlessly:
    - [Fabric API](https://modrinth.com/mod/fabric-api)
    - [Fabric Language Kotlin](https://modrinth.com/mod/fabric-language-kotlin)
    - [Lithium](https://modrinth.com/mod/lithium)
    - [spark](https://modrinth.com/mod/spark)
    - [FallingTree](https://modrinth.com/mod/fallingtree)
    - [Collective](https://modrinth.com/mod/collective)
    - [Villager Names](https://modrinth.com/mod/villager-names-serilum)

We're a long way away from 12 y.o. Jason's green laptop running 24-7 😊


## How this project works

### 1. Starting the Server

- The server is managed via Docker Compose using the [itzg/minecraft-server](https://github.com/itzg/docker-minecraft-server) image.
- All configuration is handled in `docker-compose.yml`:
    - Sets up environment variables for server name, MOTD, version, difficulty, mods, and more.
    - Includes startup RCON commands and mod/project lists.

To start the server:
```sh
docker compose up -d
```

### 2. Monitoring & Automation

- A cron job runs every minute:
    - Run `server_status.sh`: activate venv and run `server_status.py` to check server status and send notifications
    - There is an included `cron_simulator.py` for local testing
- (WIP) `welcome_message_builder.py` generates custom welcome-back messages for players.

## Roadmap

What's currently in the works? What are we thinking of adding?


- **Automated Backups**
    - Implement regular world backups
- **Player Activity Alerts**
    - Notify players when other players join/leave, or notify admins if the server goes down
- **Dynamic README**
    - Automatically update the markdown file with latest mods installed, server settings, and minecraft version

