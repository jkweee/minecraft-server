#!/bin/bash
# TO USE: run from minecraft/minecraft-backups
logfile="./backup-data.log"
current_datetime=$(date +"%Y.%m.%d %H.%M.%S")
source="../minecraft-data"
destination="./minecraft-data $current_datetime"

# Create backup: turn off saving, save all, copy the directory, turn on saving
echo "$current_datetime Creating backup from $source ..." | tee $logfile
docker exec minecraft-mc-1 rcon-cli say Backing up world...
docker exec minecraft-mc-1 rcon-cli list | tee $logfile
docker exec minecraft-mc-1 rcon-cli save-off
docker exec minecraft-mc-1 rcon-cli save-all
cp -r "$source" "$destination"
docker exec minecraft-mc-1 rcon-cli save-on
docker exec minecraft-mc-1 rcon-cli say Backup complete! Enjoy your day
echo "$current_datetime Created backup at: $destination" | tee $logfile

# Compressing
echo "$current_datetime Compressing backup..." | tee $logfile
tar -cpzf "$destination.tar.gz" "$destination"
rm -rf "$destination"
echo "$current_datetime Compressed backup to $destination.tar.gz and removed the uncompressed backup." | tee $logfile

# Final log: add to log file
echo "$current_datetime Finished backing up!" | tee $logfile
# List individual file sizes
du -sh ./*
# Print total size of the current folder in GB
total_size=$(du -sb . | awk '{printf "%.2f", $1/1024/1024/1024}')
echo "Total backup folder size: $total_size GB"