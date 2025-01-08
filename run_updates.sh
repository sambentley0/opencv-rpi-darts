#!/bin/bash

# Full Dartboard Score Calculation Runner Script
# Runs checks for updates on required packages
# Ensure this script has executable permissions: chmod +x run_dartboard.sh

# Update and upgrade the Raspberry Pi
echo "Updating Raspberry Pi packages..."
sudo apt-get update && sudo apt-get upgrade -y

# Install required dependencies
echo "Installing required dependencies..."
sudo apt-get install -y python3 python3-pip python3-opencv sqlite3 libopencv-dev
pip3 install flask opencv-python opencv-contrib-python --break-system-packages

# Check for camera availability
echo "Testing camera availability..."
vcgencmd get_camera || { echo "Camera not detected. Ensure it's connected and enabled."; exit 1; }

# Run the Python script
#!/bin/bash
git pull origin main
python3 dartboard_server.py
echo "Starting the Dartboard Score Calculation script..."
