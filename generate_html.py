#Required modules
from bs4 import BeautifulSoup as bs
import re
import time
import json
import random
import datetime
import requests
import locale

#Required variables
Location="Sursee"
datetime = datetime.date.today()

#Required Functions
def get_weather(Location):
    #Required variables
    api_key = 'a9a70ee61cdf08ce9c1753776b1a2bad'
    base_url = "https://api.openweathermap.org/data/2.5/forecast?"
    api_call = base_url + "lang=de" + "&q=" + Location + "&appid=" + api_key + "&units=metric"
    return requests.get(api_call).text

#set locale to german
locale.setlocale(locale.LC_TIME, 'de_CH.ISO-8859-1')

#set headers for api call
headers = {"accept": "application/json"}

#set Daily seed
seed= datetime.day + datetime.month
random.seed(seed)

#Api call
json_data =  json.loads(get_weather(Location))
print(json_data)
json_data_now = json_data["list"][0]
json_data_forecast = json_data["list"][2]

#replace text in html file and save it as dashboard.html
with open('/home/pi/pi-dashboard/dashboard_template.html', 'r') as file :
    filedata = file.read()

    filedata = filedata.replace('WEEKDAY', str(datetime.strftime('%A')))
    filedata = filedata.replace('DAYTODAY', str(datetime.day))
    filedata = filedata.replace('MONTHTODAY', str(datetime.strftime("%b")))
    
    filedata = filedata.replace('NOW_CITY', Location)
    filedata = re.sub('NOW_NOWTEMP', str(json_data_now["main"]["temp"]), filedata)
    filedata = re.sub('NOW_MINTEMP', str(json_data_now["main"]["temp_min"]), filedata)
    filedata = re.sub('NOW_MAXTEMP', str(json_data_now["main"]["temp_max"]), filedata)
    filedata = filedata.replace('NOW_DESC', json_data_now["weather"][0]["description"])
    filedata = re.sub('NOW_ICON', json_data_now["weather"][0]["icon"], filedata)

    filedata = re.sub('FORECAST_CITY', Location, filedata)
    filedata = re.sub('FORECAST_NOWTEMP', str(json_data_forecast["main"]["temp"]), filedata)
    filedata = re.sub('FORECAST_MINTEMP', str(json_data_forecast["main"]["temp_min"]), filedata)
    filedata = re.sub('FORECAST_MAXTEMP', str(json_data_forecast["main"]["temp_max"]), filedata)
    filedata = filedata.replace('FORECAST_DESC', json_data_forecast["weather"][0]["description"])
    filedata = re.sub('FORECAST_ICON', json_data_forecast["weather"][0]["icon"], filedata)
    
    filedata = filedata.replace('QUOTE', random.choice(list(open('/home/pi/pi-dashboard/quotes.txt'))))

with open('/home/pi/pi-dashboard/dashboard.html', 'w') as file:
    file.write(filedata)
