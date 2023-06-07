import datetime
import time
from O365 import Account, MSGraphProtocol, FileSystemTokenBackend
from msal import ConfidentialClientApplication
import re
import config



calendar_events = ""
#set scopes to read shared calendars and refresh token
#scopes = ['Calendars.Read.Shared', 'offline_access']
scopes = 'Calendars.Read.Shared offline_access'

# Function to Check if token is expired
def is_token_expired(access_token):
    match = re.search(r'"expires_at":\s*(\d+\.\d+)', access_token)
    expires_at = float(match.group(1)) if match else 0
    return expires_at < datetime.datetime.utcnow().timestamp()

# Function to Refresh the access token
def refresh_access_token(client_id, client_secret, token_path, token_filename):
    # Read the refresh token from the file
    with open(token_filename, 'r') as f:
        access_token = f.read().strip()

    if access_token == "":
        #print("No token found. Please run get_token.py first.")
        return None

    refresh_token = re.search(r'"refresh_token":\s*"([^"]+)"', access_token).group(1)

    # Create an instance of the Account class
    credentials = (client_id, client_secret)
    account = Account(credentials, token_backend=FileSystemTokenBackend(token_path=token_path, token_filename=token_filename))

    # Manually load the refresh token
    account.connection.token_backend.token = {'refresh_token': refresh_token}

    # Refresh the access token using MSAL
    authority = 'https://login.microsoftonline.com/common'
    scopes = ['User.Read', 'Calendars.Read']
    app = ConfidentialClientApplication(client_id, authority=authority, client_credential=client_secret)
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

# Read Microsoft 365 access token from file 
with open('o365_token.txt', 'r') as f:
    access_token = f.read().strip()

if access_token == "":
    print("No token found. Please run get_token.py first.")
    exit()
#if token is expired refresh it
if is_token_expired(access_token):
    refreshed_token = refresh_access_token(config.CLIENT_ID, config.SECRET_ID, config.token_path, config.token_filename)
    if refreshed_token:
        access_token, expires_at = refreshed_token
        #print('Refreshed Access Token:', access_token)
        #print('Expires At:', expires_at)

# Create Microsoft Graph API account object
credentials = (config.CLIENT_ID, config.SECRET_ID)
protocol = MSGraphProtocol(api_version='beta')
account = Account(credentials, protocol=protocol)

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

    print(calendar_events)
else:
    print('Authentication failed.')    