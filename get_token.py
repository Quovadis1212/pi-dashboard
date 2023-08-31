#!/usr/bin/env python3

from O365 import Account, MSOffice365Protocol
import config

credentials = (config.CLIENT_ID, config.SECRET_ID)
protocol = MSOffice365Protocol(default_resource='common')

scopes = ['User.Read', 'Calendars.Read', 'Tasks.Read', 'offline_access']
account = Account(credentials, protocol=protocol)

if account.authenticate(scopes=scopes):
    print('Token can now be used to access Office 365 APIs')

else:
    print('Authentication failed.')