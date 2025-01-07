#!/bin/bash

# Full Dartboard Score Calculation Runner Script
# Ensure this script has executable permissions: chmod +x run_dartboard.sh

# Update and upgrade the Raspberry Pi
echo "Updating Raspberry Pi packages..."
sudo apt-get update && sudo apt-get upgrade -y

# Install required dependencies
echo "Installing required dependencies..."
sudo apt-get install -y python3 python3-pip python3-opencv sqlite3 libopencv-dev
pip3 install flask opencv-python opencv-contrib-python

# Enable the Raspberry Pi Camera
echo "Enabling Raspberry Pi Camera..."
sudo raspi-config nonint do_camera 0

# Check for camera availability
echo "Testing camera availability..."
vcgencmd get_camera || { echo "Camera not detected. Ensure it's connected and enabled."; exit 1; }

# Path to the Python script
SCRIPT="full_dartboard_score.py"

# Run the Python script
echo "Starting the Dartboard Score Calculation script..."
python3 "$SCRIPT"
