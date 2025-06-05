#!/bin/bash

# Get the current date in DD-MM-YYYY format
current_date=$(date +"%d-%m-%Y")

# Define source and destination directories
source="minecraft-data"
destination="minecraft-data-$current_date"

# Copy the directory recursively
echo "Creating backup from $source ..."
cp -r "$source" "$destination"
echo "Created backup at: $destination"