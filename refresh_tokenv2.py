from O365 import Account, FileSystemTokenBackend
from msal import ConfidentialClientApplication
import re
import time
import config

def refresh_access_token(client_id, client_secret, token_path, token_filename):
    # Read the refresh token from the file
    with open(token_filename, 'r') as f:
        access_token = f.read().strip()

    if access_token == "":
        print("No token found. Please run get_token.py first.")
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
        print('Failed to refresh access token.')
        return None

# Refresh the access token
refreshed_token = refresh_access_token(config.CLIENT_ID, config.SECRET_ID, config.token_path, config.token_filename)

if refreshed_token:
    # Print the refreshed access token and its expiration time
    access_token, expires_at = refreshed_token
    print('Refreshed Access Token:', access_token)
    print('Expires At:', expires_at)

