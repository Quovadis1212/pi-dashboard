#Required modules
from bs4 import BeautifulSoup as bs
import re
import time
import json
import random
import datetime
import requests


#Required Functions
def get_weather(Location):
    #Required variables
    api_key = 'a9a70ee61cdf08ce9c1753776b1a2bad'
    base_url = "https://api.openweathermap.org/data/2.5/weather?"
    api_call = base_url + "q=" + Location + "&appid=" + api_key + "&units=metric"
    return requests.get(api_call).text

def suffix(day):
  suffix = ""
  if 4 <= day <= 20 or 24 <= day <= 30:
    suffix = "th"
  else:
    suffix = ["st", "nd", "rd"][day % 10 - 1]
  return suffix

#Required variables
Location="Sursee"

datetime = datetime.date.today()
daytoday = str(datetime.day) + suffix(datetime.day)
monthtoday = str(datetime.strftime("%b"))
weekday = str(datetime.strftime('%A'))

headers = {"accept": "application/json"}

#Daily seed
seed= datetime.day + datetime.month
random.seed(seed)

#Weather Get name, temperature, description, icon   
json_data =  json.loads(get_weather(Location))
print(json_data)

#replace text in html file and save it as dashboard.html
with open('/home/pi/pi-dashboard/dashboard_template.html', 'r') as file :
    filedata = file.read()


    filedata = filedata.replace('WEEKDAY', weekday)
    filedata = filedata.replace('DAYTODAY', daytoday)
    filedata = filedata.replace('MONTHTODAY', monthtoday)
    
    filedata = filedata.replace('CITY', json_data["name"])
    filedata = re.sub('NOWTEMP', str(json_data["main"]["temp"]), filedata)
    filedata = re.sub('MINTEMP', str(json_data["main"]["temp_min"]), filedata)
    filedata = re.sub('MAXTEMP', str(json_data["main"]["temp_max"]), filedata)
    filedata = filedata.replace('DESC', json_data["weather"][0]["description"])
    filedata = re.sub('ICON', json_data["weather"][0]["icon"], filedata)

    filedata = filedata.replace('QUOTE', random.choice(list(open('/home/pi/pi-dashboard/quotes.txt'))))
with open('/home/pi/pi-dashboard/dashboard.html', 'w') as file:
    file.write(filedata)
