#!/bin/bash

# Get the current date and time in DD-MM-YYYY_HH-MM-SS format
current_datetime=$(date +"%Y.%m.%d %H.%M.%S")

# Define source and destination directories
source="minecraft-data"
destination="./minecraft-backups/minecraft-data $current_datetime"

# Copy the directory recursively
echo "Creating backup from $source ..."
cp -r "$source" "$destination"
echo "Created backup at: $destination"