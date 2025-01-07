#!/bin/bash

#  Dartboard Score Calculation Runner Script
# Ensure this script has executable permissions: chmod +x run_dartboard.sh

# Enable the Raspberry Pi Camera
echo "Enabling Raspberry Pi Camera..."
sudo raspi-config nonint do_camera 0

# Check for camera availability
echo "Testing camera availability..."
vcgencmd get_camera || { echo "Camera not detected. Ensure it's connected and enabled."; exit 1; }

# Run the Python script
#!/bin/bash
git pull origin main
python3 dartboard_server.py
echo "Starting the Dartboard Score Calculation script..."
