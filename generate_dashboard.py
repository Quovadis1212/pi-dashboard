#!/usr/bin/env python3

#Required modules
from bs4 import BeautifulSoup as bs
import re
import json
import datetime
import requests
import locale
from O365 import Account, FileSystemTokenBackend
from msal import ConfidentialClientApplication
import feedparser
import qrcode

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import os

from PIL import Image
from inky.auto import auto

#import config with variables
import config

#Required variables
templatepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ressources/dashboard_template.html')
htmlpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dashboard.html')
imgpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dashboard.png')
tokenfilename = 'o365_token.txt'
tokenfilepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), tokenfilename)
tokenpath = os.path.dirname(os.path.abspath(__file__))



#Required Functions

#function to check internet connection
def check_internet():
    url='http://www.google.com/'
    timeout=5
    try:
        _ = requests.get(url, timeout=timeout)
        return True
    except requests.ConnectionError:
        return False

# Function to get the weather data from openweathermap.org
def get_weather(City):
    base_url = "https://api.openweathermap.org/data/2.5/forecast?"
    api_call = base_url + "lang=de" + "&q=" + City + "&appid=" + config.api_key + "&units=metric"
    return requests.get(api_call).text

# Function to Check if token is expired
def is_token_expired(access_token):
    match = re.search(r'"expires_at":\s*(\d+\.\d+)', access_token)
    expires_at = float(match.group(1)) if match else 0
    if expires_at < datetime.datetime.utcnow().timestamp():
        return True
    else:
        return False

# Function to Refresh the access token
def refresh_access_token(client_id, client_secret, token_path, token_filename, access_token):
    # Read the refresh token from the file if it exists
    try:
        with open(token_filename, 'r') as f:
            access_token = f.read().strip()
            print("Token found.")
    except FileNotFoundError:
        access_token = None
        print("No token found. Please run get_token.py first.")

    match = re.search(r'"refresh_token": "([^"]+)"', access_token)
    if match:
        refresh_token = match.group(1)
        refresh_token = str(refresh_token)
    else:
        refresh_token = None
        print("No refresh token found in the access_token string.")
    

    # Create an instance of the Account class
    credentials = (client_id, client_secret)
    account = Account(credentials, token_backend=FileSystemTokenBackend(token_path=token_path, token_filename=token_filename))

    # Manually load the refresh token
    account.connection.token_backend.token = {'refresh_token': refresh_token}

    # Refresh the access token using MSAL
    
    authority = 'https://login.microsoftonline.com/common'
    scopes = ['User.Read', 'Calendars.Read', 'Tasks.Read']
    app = ConfidentialClientApplication(client_id, authority=authority, client_credential=client_secret)
    result = app.acquire_token_silent(scopes, account=account.connection)
    if "access_token" in result:
        access_token = result['access_token']
        expires_at = result['expires_on']
        return (access_token, expires_at)
    else:
        print(result['error'])
        print(result['error_description'])
        return None
        
# Function to get the calendar events
def get_calendar():
    calendar_events = ""
    # Read Microsoft 365 access token from file 
    with open(tokenfilepath, 'r') as f:
        access_token = f.read().strip()

    if access_token == "":
        print("No token found. Please run get_token.py first.")
        exit()

    #if token is expired refresh it
    if is_token_expired(access_token):
        refreshed_token = refresh_access_token(config.CLIENT_ID, config.SECRET_ID, tokenpath, tokenfilename, access_token)
        if refreshed_token:
            access_token, expires_at = refreshed_token
            print('Refreshed Access Token:', access_token)
            print('Expires At:', expires_at)

    # Create Microsoft Graph API account object
    credentials = (config.CLIENT_ID, config.SECRET_ID)
    account = Account(credentials, token_backend=FileSystemTokenBackend(token_path=tokenpath, token_filename=tokenfilename))

    if not account.is_authenticated:
        account.authenticate(scopes=['basic', 'calendar_all'])

    # Set the start and end times to include events for today
    today = datetime.datetime.utcnow().date()
    start = datetime.datetime.combine(today, datetime.time.min).isoformat() + 'Z'
    end = datetime.datetime.combine(today, datetime.time.max).isoformat() + 'Z'

    # Authenticate with Microsoft Graph API and get default calendar events for today
    if account.is_authenticated:
        schedule = account.schedule()
        calendar = schedule.get_default_calendar()
        q = calendar.new_query('start').greater_equal(start)
        q.chain('and').on_attribute('end').less_equal(end)
        events = calendar.get_events(query=q, include_recurring=True) 
        for event in events:
            event = str(event)
            # Extract subject
            subject_match = re.search(r'Subject: (.+?) \(on:', event)
            subject = subject_match.group(1) if subject_match else None

            # Extract start time
            start_time_match = re.search(r'from:(.+?) ', event)
            start_time = start_time_match.group(1) if start_time_match else None

            # Extract end time
            end_time_match = re.search(r'to: (.+?)\)', event)
            end_time = end_time_match.group(1) if end_time_match else None

            # Add appropriate amount of spaces to subject to align events
            space_amount = 20 - len(subject)
            subject += space_amount * "&nbsp;"

            # Combine event details and add to calendar_events string
            event_details = subject + ' um ' + start_time + ' - ' + end_time
            calendar_events += event_details + "\n"

        return(calendar_events)
    else:
        return('Authentication failed.')    

# Function to get the tasks
def get_tasks():
    # Read Microsoft 365 access token from file
    with open(tokenfilepath, 'r') as f:
        access_token = f.read().strip()

    if access_token == "":
        print("No token found. Please run get_token.py first.")
        exit()

    # If token is expired, refresh it
    if is_token_expired(access_token):
        refreshed_token = refresh_access_token(config.CLIENT_ID, config.SECRET_ID, tokenpath, tokenfilename, access_token)
        if refreshed_token:
            access_token, expires_at = refreshed_token
            print('Refreshed Access Token:', access_token)
            print('Expires At:', expires_at)

    # Create Microsoft Graph API account object
    credentials = (config.CLIENT_ID, config.SECRET_ID)
    account = Account(credentials, token_backend=FileSystemTokenBackend(token_path=tokenfilepath, token_filename=tokenfilename))

    if not account.is_authenticated:
        account.authenticate(scopes=['basic', 'tasks_all'])

    if account.is_authenticated:
        planner = account.planner()
        tasks = planner.get_my_tasks()
        task_list = ""
        for task in tasks:
            subject = task.title
            due_date = task.due_date_time
            # Combine task details and add to task_list
            task_details = subject 
            # If due_date is not None, add it to task_details
            if due_date:
                task_details += ' bis ' + due_date.strftime("%d.%m")
            task_list += task_details + "\n"
            
        return(task_list)
    else:
        return('Authentication failed.')

# Function to read rss feeds
def read_rss_feed(rss_url):
    feed = feedparser.parse(rss_url)
    rss_items = feed['items']
    news = []
    for item in rss_items:
        news.append(item['title'])
        news.append(item['link'])  
    return news

# Function to get news
def get_news():
    rss_url = "https://partner-feeds.beta.20min.ch/rss/20minuten"

    news = read_rss_feed(rss_url)

    qr = qrcode.QRCode(version=1, box_size=2, border=1)
    qr.add_data(news[1])
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    qr_code_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ressources/newsqr.png')
    img.save(qr_code_file)

    return(news[0])

# Function to replace data in html file
def replace_data(replace_data_list, filedata):
    for i in replace_data_list:
        filedata = re.sub(i[0], i[1], filedata)
    return filedata

def capture_screenshot_from_file(file_path, image_path):
    """Capture a screenshot of a webpage and save it as a PNG image"""
    # Set parameters for Chrome driver
    service = Service('/usr/bin/chromedriver')
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=800x480")

    # Initialize Chrome driver
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # get absolute path of html file
    url = 'file://' + os.path.abspath(file_path)

    # Navigate to the URL
    driver.get(url)

    # Take a screenshot and save it
    driver.save_screenshot(image_path)

    # Close the browser
    driver.quit()

# Funcrion to write image to inky
def image_to_inky(image_path):
    inky = auto(ask_user=True, verbose=True)
    saturation = 1
    image = Image.open(image_path)
    resizedimage = image.resize(inky.resolution)
    inky.set_image(resizedimage, saturation=saturation)
    inky.show()

#set locale to german
locale.setlocale(locale.LC_TIME, 'de_CH.ISO-8859-1')

#set headers for api call
headers = {"accept": "application/json"}

#check for internet connection and if not available, exit
if not check_internet():
    #replace content of dashboard.html with error message no_internet.png
    with open(htmlpath, 'w') as file:
        file.write("<img src=\"ressources/no_internet.png\" alt=\"No Internet Connection\" style=\"width:100%;height:100%;\">")
    #print error message
    print("No internet connection available. Exiting...")
    exit()

#api call to get O365 information
CALENDAR_EVENTS = get_calendar()
print(CALENDAR_EVENTS)
TASKS = get_tasks()
print(TASKS)

#api call to get news
NEWS = get_news()
print(NEWS)

#Api call to get weather data
json_data =  json.loads(get_weather(config.Location))
print(json_data)
#if json_data["weather"][0]["description"] and/or json_data["weather"][2]["description"] is greater than lenght 15, replace space with <br/>
if len(json_data["list"][0]["weather"][0]["description"]) > 15:
    json_data["list"][0]["weather"][0]["description"] = json_data["list"][0]["weather"][0]["description"].replace(" ", "<br/>")
if len(json_data["list"][2]["weather"][0]["description"]) > 15:
    json_data["list"][2]["weather"][0]["description"] = json_data["list"][2]["weather"][0]["description"].replace(" ", "<br/>")
#convert winds from m/s to km/h
json_data["list"][0]["wind"]["speed"] = round(json_data["list"][0]["wind"]["speed"] * 3.6, 1)
json_data["list"][2]["wind"]["speed"] = round(json_data["list"][2]["wind"]["speed"] * 3.6, 1)

#set json_data_now and json_data_forecast
json_data_now = json_data["list"][0]
json_data_forecast = json_data["list"][2]

replace_data_list = [
    ['WEEKDAY', datetime.datetime.now().strftime('%A')],
    ['DAYTODAY', datetime.datetime.now().strftime("%d")],
    ['MONTHTODAY', datetime.datetime.now().strftime("%b")],
    ['NOW_NOWTEMP', str(json_data_now["main"]["temp"])],
    ['NOW_DESC', json_data_now["weather"][0]["description"]],
    ['NOW_WIND', str(json_data_now["wind"]["speed"])],
    ['NOW_ICON', json_data_now["weather"][0]["icon"]],
    ['FORECAST_NOWTEMP', str(json_data_forecast["main"]["temp"])],
    ['FORECAST_DESC', json_data_forecast["weather"][0]["description"]],
    ['FORECAST_WIND', str(json_data_forecast["wind"]["speed"])],
    ['FORECAST_ICON', json_data_forecast["weather"][0]["icon"]],
    ['NEWS', NEWS.replace('\n', "<br/>")],
    ['CALENDAR_EVENTS', CALENDAR_EVENTS.replace('\n', "<br/>")],
    ['TASKS', TASKS.replace('\n', "<br/>")],
    ['TIMESTAMP', datetime.datetime.now().strftime('%H:%M')]
]

#replace text in html file and save it as dashboard.html
with open(templatepath, 'r') as file :
    filedata = file.read()
    filedata = replace_data(replace_data_list, filedata)

with open(htmlpath, 'w') as file:
    file.write(filedata)

capture_screenshot_from_file(htmlpath, imgpath)
image_to_inky(imgpath)