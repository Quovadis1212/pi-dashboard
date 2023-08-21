#Required modules
from bs4 import BeautifulSoup as bs
import re
import time
import json
import datetime
import requests
import locale
from O365 import Account, MSGraphProtocol, FileSystemTokenBackend
from msal import ConfidentialClientApplication
import feedparser
import qrcode
#import subprocess

#import config.py with variables
import config

#test calendar
#import subprocess
#script_path = '/home/pi/pi-dashboard/get_calendar.py'
#output = subprocess.check_output(['python', script_path], universal_newlines=True)
#CALENDAR_EVENTS = output
#print(CALENDAR_EVENTS)

#test tasks
#script_path = '/home/pi/pi-dashboard/get_tasks.py'
#output = subprocess.check_output(['python', script_path], universal_newlines=True)
#TASKS = output
#print(TASKS)

#test news
#script_path = '/home/pi/pi-dashboard/get_news.py'
#output = subprocess.check_output(['python', script_path], universal_newlines=True)
#NEWS = output
#print(NEWS)

#Required variables


#Required Functions

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
    '''
    # Read the refresh token from the file if it exists
    try:
        with open(token_filename, 'r') as f:
            access_token = f.read().strip()
            print("Token found.")
    except FileNotFoundError:
        access_token = None
        print("No token found. Please run get_token.py first.")
    '''
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

    '''
    result = app.acquire_token_by_refresh_token(account.connection.token_backend.token['refresh_token'], scopes=scopes)

    # Check if the access token was successfully refreshed
    if 'access_token' in result:
        access_token = result['access_token']
        expires_in = result['expires_in']

        # Update the access token and its expiration time in the token backend
        account.connection.token_backend.token['access_token'] = access_token
        account.connection.token_backend.token['expires_in'] = expires_in

        # Calculate the expiration timestamp (current time + expires_in)
        expires_at = int(time.time()) + expires_in
        account.connection.token_backend.token['expires_at'] = expires_at

        # Save the updated token information
        account.connection.token_backend.save_token()

        # Return the refreshed access token and its expiration time
        return access_token, expires_at
    else:
        # Failed to refresh access token
        #print('Failed to refresh access token.')
        return None
    '''

# Function to get the calendar events
def get_calendar():
    calendar_events = ""

    '''
    #set scopes to read shared calendars and refresh token
    #scopes = ['Calendars.Read.Shared', 'offline_access']
    scopes = 'Calendars.Read.Shared offline_access'
    '''

    # Read Microsoft 365 access token from file 
    with open(config.token_pf, 'r') as f:
        access_token = f.read().strip()

    if access_token == "":
        print("No token found. Please run get_token.py first.")
        exit()

    #if token is expired refresh it
    if is_token_expired(access_token):
        refreshed_token = refresh_access_token(config.CLIENT_ID, config.SECRET_ID, config.token_path, config.token_filename, access_token)
        if refreshed_token:
            access_token, expires_at = refreshed_token
            print('Refreshed Access Token:', access_token)
            print('Expires At:', expires_at)

    # Create Microsoft Graph API account object
    credentials = (config.CLIENT_ID, config.SECRET_ID)
    account = Account(credentials, token_backend=FileSystemTokenBackend(token_path=config.token_path, token_filename=config.token_filename))

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
    with open(config.token_pf, 'r') as f:
        access_token = f.read().strip()

    if access_token == "":
        print("No token found. Please run get_token.py first.")
        exit()

    # If token is expired, refresh it
    if is_token_expired(access_token):
        refreshed_token = refresh_access_token(config.CLIENT_ID, config.SECRET_ID, config.token_path, config.token_filename, access_token)
        if refreshed_token:
            access_token, expires_at = refreshed_token

    # Create Microsoft Graph API account object
    credentials = (config.CLIENT_ID, config.SECRET_ID)
    account = Account(credentials, token_backend=FileSystemTokenBackend(token_path=config.token_path, token_filename=config.token_filename))

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
    qr_code_file = "newsqr.png"
    img.save(qr_code_file)

    return(news[0])

#set locale to german
locale.setlocale(locale.LC_TIME, 'de_CH.ISO-8859-1')

#set headers for api call
headers = {"accept": "application/json"}

#api call to get O365 information
CALENDAR_EVENTS = get_calendar()
TASKS = get_tasks()
print(CALENDAR_EVENTS)
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

#replace text in html file and save it as dashboard.html
with open('/home/pi/pi-dashboard/dashboard_template.html', 'r') as file :
    filedata = file.read()

    filedata = filedata.replace('WEEKDAY', datetime.datetime.now().strftime('%A'))
    filedata = filedata.replace('DAYTODAY', datetime.datetime.now().strftime("%d"))
    filedata = filedata.replace('MONTHTODAY', datetime.datetime.now().strftime("%b"))

    #filedata = filedata.replace('NOW_CITY', config.Location)
    filedata = re.sub('NOW_NOWTEMP', str(json_data_now["main"]["temp"]), filedata)
    #filedata = re.sub('NOW_MINTEMP', str(json_data_now["main"]["temp_min"]), filedata)
    #filedata = re.sub('NOW_MAXTEMP', str(json_data_now["main"]["temp_max"]), filedata)
    filedata = filedata.replace('NOW_DESC', json_data_now["weather"][0]["description"])
    filedata = re.sub('NOW_WIND', str(json_data_now["wind"]["speed"]), filedata)
    filedata = re.sub('NOW_ICON', json_data_now["weather"][0]["icon"], filedata)

    #filedata = re.sub('FORECAST_CITY', config.Location, filedata)
    filedata = re.sub('FORECAST_NOWTEMP', str(json_data_forecast["main"]["temp"]), filedata)
    #filedata = re.sub('FORECAST_MINTEMP', str(json_data_forecast["main"]["temp_min"]), filedata)
    #filedata = re.sub('FORECAST_MAXTEMP', str(json_data_forecast["main"]["temp_max"]), filedata)
    filedata = filedata.replace('FORECAST_DESC', json_data_forecast["weather"][0]["description"])
    filedata = re.sub('FORECAST_WIND', str(json_data_forecast["wind"]["speed"]), filedata)
    filedata = re.sub('FORECAST_ICON', json_data_forecast["weather"][0]["icon"], filedata)
    
    filedata = re.sub('NEWS', NEWS.replace('\n', "<br/>"), filedata)
    filedata = re.sub('CALENDAR_EVENTS', CALENDAR_EVENTS.replace('\n', "<br/>"), filedata)
    filedata = re.sub('TASKS', TASKS.replace('\n', "<br/>"), filedata)

with open('/home/pi/pi-dashboard/dashboard.html', 'w') as file:
    file.write(filedata)
    