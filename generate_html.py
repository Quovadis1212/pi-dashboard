#Required modules
from bs4 import BeautifulSoup as bs
import re
import time
import json
import random
import datetime
import requests
import locale

#import config.py with api keys
import config

#test calendar
import subprocess
script_path = '/home/pi/pi-dashboard/get_calendar.py'
output = subprocess.check_output(['python', script_path], universal_newlines=True)
CALENDAR_EVENTS = output
print(CALENDAR_EVENTS)

#test tasks
script_path = '/home/pi/pi-dashboard/get_tasks.py'
output = subprocess.check_output(['python', script_path], universal_newlines=True)
TASKS = output
print(TASKS)

#test news
script_path = '/home/pi/pi-dashboard/get_news.py'
output = subprocess.check_output(['python', script_path], universal_newlines=True)
NEWS = output
print(NEWS)

#Required variables
datetime = datetime.date.today()

#Required Functions
def get_weather(City):
    base_url = "https://api.openweathermap.org/data/2.5/forecast?"
    api_call = base_url + "lang=de" + "&q=" + City + "&appid=" + config.api_key + "&units=metric"
    return requests.get(api_call).text

#set locale to german
locale.setlocale(locale.LC_TIME, 'de_CH.ISO-8859-1')

#set headers for api call
headers = {"accept": "application/json"}

#Api call
json_data =  json.loads(get_weather(config.Location))
print(json_data)
#if json_data["weather"][0]["description"] and/or json_data["weather"][2]["description"] is greater than lenght 15, replace space with <br/>
if len(json_data["list"][0]["weather"][0]["description"]) > 15:
    json_data["list"][0]["weather"][0]["description"] = json_data["list"][0]["weather"][0]["description"].replace(" ", "<br/>")
if len(json_data["list"][2]["weather"][0]["description"]) > 15:
    json_data["list"][2]["weather"][0]["description"] = json_data["list"][2]["weather"][0]["description"].replace(" ", "<br/>")
json_data_now = json_data["list"][0]
json_data_forecast = json_data["list"][2]

#replace text in html file and save it as dashboard.html
with open('/home/pi/pi-dashboard/dashboard_template.html', 'r') as file :
    filedata = file.read()

    filedata = filedata.replace('WEEKDAY', str(datetime.strftime('%A')))
    filedata = filedata.replace('DAYTODAY', str(datetime.day))
    filedata = filedata.replace('MONTHTODAY', str(datetime.strftime("%b")))
    
    filedata = filedata.replace('NOW_CITY', config.Location)
    filedata = re.sub('NOW_NOWTEMP', str(json_data_now["main"]["temp"]), filedata)
    filedata = re.sub('NOW_MINTEMP', str(json_data_now["main"]["temp_min"]), filedata)
    filedata = re.sub('NOW_MAXTEMP', str(json_data_now["main"]["temp_max"]), filedata)
    filedata = filedata.replace('NOW_DESC', json_data_now["weather"][0]["description"])
    filedata = re.sub('NOW_ICON', json_data_now["weather"][0]["icon"], filedata)

    filedata = re.sub('FORECAST_CITY', config.Location, filedata)
    filedata = re.sub('FORECAST_NOWTEMP', str(json_data_forecast["main"]["temp"]), filedata)
    filedata = re.sub('FORECAST_MINTEMP', str(json_data_forecast["main"]["temp_min"]), filedata)
    filedata = re.sub('FORECAST_MAXTEMP', str(json_data_forecast["main"]["temp_max"]), filedata)
    filedata = filedata.replace('FORECAST_DESC', json_data_forecast["weather"][0]["description"])
    filedata = re.sub('FORECAST_ICON', json_data_forecast["weather"][0]["icon"], filedata)
    
    filedata = re.sub('NEWS', NEWS.replace('\n', "<br/>"), filedata)
    filedata = re.sub('CALENDAR_EVENTS', CALENDAR_EVENTS.replace('\n', "<br/>"), filedata)
    filedata = re.sub('TASKS', TASKS.replace('\n', "<br/>"), filedata)

with open('/home/pi/pi-dashboard/dashboard.html', 'w') as file:
    file.write(filedata)
    