#!/usr/bin/env python3
# Importiere die Klasse Account aus dem Modul O365
from O365 import Account, MSOffice365Protocol
# Importiere die Konfiguration aus der Datei config.py
import config
# Erstelle ein Account-Objekt mit den Anmeldedaten aus config.py
credentials = (config.CLIENT_ID, config.SECRET_ID)
protocol = MSOffice365Protocol(default_resource='common')
scopes = ['User.Read', 'Calendars.Read', 'Tasks.Read', 'offline_access']
account = Account(credentials, protocol=protocol)
# Führe die Authentifizierung durch
if account.authenticate(scopes=scopes):
    print('Token can now be used to access Office 365 APIs')

else:
    print('Authentication failed.')