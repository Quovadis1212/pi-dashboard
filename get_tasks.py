import datetime
import time
from O365 import Account, FileSystemTokenBackend
from msal import ConfidentialClientApplication
import re
import config

# Function to Check if token is expired
def is_token_expired(access_token):
    match = re.search(r'"expires_at":\s*(\d+\.\d+)', access_token)
    expires_at = float(match.group(1)) if match else 0
    return expires_at < datetime.datetime.utcnow().timestamp()

# Function to Refresh the access token
def refresh_access_token(client_id, client_secret, token_path, token_filename):
    # Read the refresh token from the file if it exists
    try:
        with open(token_filename, 'r') as f:
            access_token = f.read().strip()
    except FileNotFoundError:
        access_token = None
        print("No token found. Please run get_token.py first.")

    match = re.search(r'"refresh_token":\s*"([^"]+)"', access_token)

    if match:
        refresh_token = match.group(1)
        print("Refresh Token:", refresh_token)
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
        return None

# Read Microsoft 365 access token from file
with open('o365_token.txt', 'r') as f:
    access_token = f.read().strip()

if access_token == "":
    print("No token found. Please run get_token.py first.")
    exit()

# If token is expired, refresh it
if is_token_expired(access_token):
    refreshed_token = refresh_access_token(config.CLIENT_ID, config.SECRET_ID, config.token_path, config.token_filename)
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
    task_list = []

    for task in tasks:
        subject = task.title
        due_date = task.due_date_time
        # Combine task details and add to task_list
        task_details = subject + ' am ' + due_date.strftime("%d.%m")
        task_list.append(task_details)

    for task_details in task_list:
        print(task_details)

else:
    print('Authentication failed.')