#!/bin/bash

# Update Package repository
sudo apt update

# Enable i2c and spi
sudo raspi-config nonint do_i2c 0  # Enable I2C
sudo raspi-config nonint do_spi 0  # Enable SPI

# Install de_CH.ISO-8859-1 Locale
sudo apt install -y locales
sudo dpkg-reconfigure locales

# Install python3 and pip3
sudo apt install -y python3 python3-pip

# Install libopenjp2-7
sudo apt-get install -y libopenjp2-7

# Install numpy via apt-get to improve runtime of installation
sudo apt-get install -y python3-numpy

# Install git
sudo apt-get install -y git

# Install inky library and dependencies
pip3 install inky[rpi]

# Install library dependencies via pip3
pip3 install bs4 datetime requests O365 msal feedparser qrcode Pillow selenium

# Install selenium dependencies
sudo apt-get install -y chromium-browser chromium-chromedriver

# Change directory to /home/pi
cd $HOME

# Download files from git repository
git clone -b dev https://github.com/Quovadis1212/pi-dashboard.git

# Make log directory
mkdir -p log

# Install cronjob
script_path="$HOME/pi-dashboard/generate_dashboard.py"
log_file="$HOME/pi-dashboard/log/py.log"
(crontab -l ; echo "*/10 * * * * /usr/bin/python3 $script_path > $log_file 2>&1") | crontab -
