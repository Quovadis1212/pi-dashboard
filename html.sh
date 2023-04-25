#!/bin/bash
python /home/pi/pi-dashboard/generate_html.py

path="/home/pi/pi-dashboard/dashboard.html"
chromium-browser --headless --screenshot="/home/pi/pi-dashboard/screenshot.png" file:///$path --window-size=800,480
#python /home/pi/pi-dashboard/image.py /home/pi/pi-dashboard/screenshot.png


ip=$(hostname -I)
python /home/pi/pi-dashboard/name-badge.py --name $ip