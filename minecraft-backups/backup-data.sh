#!/bin/bash
logfile="./backup-data.log"
current_datetime=$(date +"%Y.%m.%d %H.%M.%S")
source="../minecraft-data"
destination="./minecraft-data $current_datetime"

# Create backup: turn off saving, save all, copy the directory, turn on saving
echo "$current_datetime Creating backup from $source ..." >> $logfile
docker exec minecraft-mc-1 rcon-cli list >> $logfile
docker exec minecraft-mc-1 rcon-cli save-off
docker exec minecraft-mc-1 rcon-cli save-all
cp -r "$source" "$destination"
docker exec minecraft-mc-1 rcon-cli save-on
echo "$current_datetime Created backup at: $destination" >> $logfile

# Compressing
echo "$current_datetime Compressing backup..." >> $logfile
tar -cpzf "$destination.tar.gz" "$destination"
rm -rf "$destination"
echo "$current_datetime Compressed backup to $destination.tar.gz and removed the uncompressed backup." >> $logfile

# Final log: add to log file
echo "$current_datetime Finished backing up!" >> $logfile
du -sh ./*
