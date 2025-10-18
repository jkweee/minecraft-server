# How this works

crontab -e 
`*/1 * * * * bash /home/jk1/Docker/minecraft/server_status.sh`

points to
`server_status.sh` activates venv and runs server_status.py
