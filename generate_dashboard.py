#!/usr/bin/env python3

#!/usr/bin/env python3
"""! @brief Example Python program with Doxygen style comments."""


##
# @mainpage Raspberry Pi Dashboard mit Inky Display
#
# @section description_main Description
# Dieses Python-Programm erstellt ein Dashboard für den Raspberry Pi mit einem Inky Impression 7Zoll Display.
# Es werden Wetterdaten, Kalenderereignisse, Aufgaben und Nachrichten angezeigt.
# @section notes_main Notes
# - Das Progrann wurde für den Raspberry Pi 4 mit einem Inky Impression 7Zoll Display entwickelt.
# - Das Programm wurde im Rahmen einer Projektarbeit im Bildungsgang Infromatiker Systemtechnik HF der TEKO Schweizerische Fachschule erstellt.
# 


##
# @file generate_dashboard.py
#
# @brief Ruft die Daten für das Dashboard ab und erstellt ein HTML-Dokument, das als Screenshot auf dem Inky Display angezeigt wird.
#
# @section description_doxygen_example Description
# Ruft die Daten für das Dashboard ab und erstellt ein HTML-Dokument, das als Screenshot auf dem Inky Display angezeigt wird.
#
# @section libraries_main Libraries/Modules
# - re
#  - Anwendung: Reguläre Ausdrücke
# - json
#  - Anwendung: JSON
# - datetime
#  - Anwendung: Datum und Zeit
# - requests
#  - Anwendung: HTTP-Anfragen
# - Account, FileSystemTokenBackend
#  - Anwendung: O365 API für Microsoft Graph
# - ConfidentialClientApplication
#  - Anwendung: MSAL für Microsoft Graph
# - feedparser
#  - Anwendung: RSS-Feeds
# - qrcode
#  - Anwendung: QR-Codes
# - webdriver, Service, Options
#  - Anwendung: Selenium für Screenshots
# - os
#  - Anwendung: Pfade
# - Image, auto
#  - Anwendung: Inky Display
# - locale
#  - Anwendung: Datums- und Zeitformatierung
#
# @section notes_doxygen_example Notes
# - Comments are Doxygen compatible.
#
# @section todo_doxygen_example TODO
# - None.
#
# @section author_doxygen_example Author(s)
# - Created by David Stöckli on 04.09.2023.
# 
#

# Erforderliche Module importieren
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

# Konfigurationsdatei importieren
import config

# Pfade zu den Ressourcen und Dateien festlegen
templatepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ressources/dashboard_template.html')
htmlpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dashboard.html')
imgpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dashboard.png')
no_internetpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ressources/no_internet.png')
tokenfilename = 'o365_token.txt'
tokenfilepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), tokenfilename)
tokenpath = os.path.dirname(os.path.abspath(__file__))


# Erforderliche Funktionen

def check_internet():
    """
    Prüft die Internetverbindung durch einen HTTP-Anfrageversuch an google.com.
    
    Returns:
        bool: True, wenn die Verbindung erfolgreich ist, False sonst.
    """
    url='http://www.google.com/'
    timeout=5
    # Versuchen eine HTTP-Anfrage an google.com zu senden
    try:
        _ = requests.get(url, timeout=timeout)
        return True
    # Wenn die Anfrage fehlschlägt, ist die Verbindung nicht erfolgreich, False zurückgeben
    except requests.ConnectionError:
        return False

def get_weather(City):
    """
    Ruft Wetterdaten von OpenWeatherMap API ab.

    Args:
        City (str): Der Name der Stadt, für die die Wetterdaten abgerufen werden sollen.

    Returns:
        str: Die zurückgegebenen Wetterdaten als Text im JSON Format.
    """
    base_url = "https://api.openweathermap.org/data/2.5/forecast?"
    # Zusammenstellen der URL für den API-Aufruf
    api_call = base_url + "lang=de" + "&q=" + City + "&appid=" + config.api_key + "&units=metric"
    # API-Aufruf und Rückgabe der Wetterdaten als Text im JSON Format
    return requests.get(api_call).text

def is_token_expired(access_token):
    """
    Überprüft, ob ein Zugriffstoken abgelaufen ist.

    Args:
        access_token (str): Das Zugriffstoken.

    Returns:
        bool: True, wenn das Token abgelaufen ist, sonst False.
    """
    # Den Ablaufzeitpunkt des Tokens auslesen
    match = re.search(r'"expires_at":\s*(\d+\.\d+)', access_token)
    expires_at = float(match.group(1)) if match else 0
    # Den aktuellen Zeitpunkt auslesen und mit dem Ablaufzeitpunkt vergleichen
    if expires_at < datetime.datetime.utcnow().timestamp():
        return True
    else:
        return False

def refresh_access_token(client_id, client_secret, token_path, token_filename, access_token):
    """
    Aktualisiert ein Zugriffstoken mithilfe eines Refresh-Tokens.

    Args:
        client_id (str): Die Client-ID für die Authentifizierung.
        client_secret (str): Das Client-Geheimnis für die Authentifizierung.
        token_path (str): Der Pfad zum Verzeichnis, in dem Tokens gespeichert werden.
        token_filename (str): Der Dateiname für das Token.
        access_token (str): Das aktuelle Zugriffstoken.

    Returns:
        tuple: Ein Tupel mit dem aktualisierten Zugriffstoken und dem Ablaufzeitpunkt.
    """
    # Die Datei mit dem Refresh-Token öffnen
    try:
        with open(token_filename, 'r') as f:
            refresh_token = f.read().strip()
            print("Refresh token found.")
    except FileNotFoundError:
        print("No refresh token found. Please run get_token.py first.")
        return None

    # Eine Instanz der Account-Klasse erstellen
    credentials = (client_id, client_secret)
    account = Account(credentials, token_backend=FileSystemTokenBackend(token_path=token_path, token_filename=token_filename))

    # Den Refresh-Token in die Account-Instanz schreiben
    account.connection.token_backend.token = {'refresh_token': refresh_token}

    # Den Zugriffstoken mit MSAL aktualisieren
    authority = 'https://login.microsoftonline.com/common'
    scopes = ['User.Read', 'Calendars.Read', 'Tasks.Read']
    app = ConfidentialClientApplication(client_id, authority=authority, client_credential=client_secret)
    result = app.acquire_token_silent(scopes, account=account.connection)

    # Wenn der Zugriffstoken erfolgreich aktualisiert wurde, wird er zurückgegeben, ansonsten wird ein Fehler ausgegeben
    if "access_token" in result:
        access_token = result['access_token']
        expires_at = result['expires_on']
        print("Access token refreshed.")
        return access_token, expires_at
    else:
        print(result['error'])
        print(result['error_description'])
        return None
        
def get_calendar():
    """
    Ruft Kalenderereignisse von Microsoft Graph API ab.

    Returns:
        str: Eine formatierte Zeichenfolge mit den abgerufenen Kalenderereignissen.
    """
    calendar_events = ""
    # Die Datei mit dem Zugriffstoken öffnen
    try:
        with open(tokenfilepath, 'r') as f:
            access_token = f.read().strip()
    # Wenn die Datei nicht gefunden wird, wird ein Fehler ausgegeben
    except FileNotFoundError:
        access_token = None
        print("No token found. Please run get_token.py first.")
        return("No token found. Please run get_token.py first.")
        

    # Aktualisieren des Zugriffstokens, wenn er abgelaufen ist
    if is_token_expired(access_token):
        refreshed_token = refresh_access_token(config.CLIENT_ID, config.SECRET_ID, tokenpath, tokenfilename, access_token)
        # Wenn der Zugriffstoken erfolgreich aktualisiert wurde, wird er ausgegeben, ansonsten wird ein Fehler ausgegeben
        if refreshed_token:
            access_token, expires_at = refreshed_token
            print('Refreshed Access Token:', access_token)
            print('Expires At:', expires_at)
        else:
            return("Token refresh failed.")

    # Ein Account-Objekt für die Microsoft Graph API erstellen
    credentials = (config.CLIENT_ID, config.SECRET_ID)
    account = Account(credentials, token_backend=FileSystemTokenBackend(token_path=tokenpath, token_filename=tokenfilename))
    # Wenn der Account nicht authentifiziert ist, wird er authentifiziert
    if not account.is_authenticated:
        account.authenticate(scopes=['basic', 'calendar_all'])

    # Die Start- und Endzeit für die Abfrage festlegen, um nur Ereignisse für den aktuellen Tag abzurufen
    today = datetime.datetime.utcnow().date()
    start = datetime.datetime.combine(today, datetime.time.min).isoformat() + 'Z'
    end = datetime.datetime.combine(today, datetime.time.max).isoformat() + 'Z'

    # Mit der Microsoft Graph API die Kalenderereignisse abrufen
    if account.is_authenticated:
        schedule = account.schedule()
        calendar = schedule.get_default_calendar()
        q = calendar.new_query('start').greater_equal(start)
        q.chain('and').on_attribute('end').less_equal(end)
        events = calendar.get_events(query=q, include_recurring=True) 
        # Für jedes Ereignis werden die Details extrahiert und in die calendar_events Zeichenfolge geschrieben
        for event in events:
            event = str(event)
            # Titel des Ereignisses extrahieren
            subject_match = re.search(r'Subject: (.+?) \(on:', event)
            subject = subject_match.group(1) if subject_match else None
            # Wenn der Titel zu lang ist, wird er abgeschnitten
            if len(subject) > 20:
                subject = subject[:20]
            
            # Startzeit des Ereignisses extrahieren und von HH:MM:SS auf HH:MM formatieren
            start_time_match = re.search(r'from:(.+?) ', event)
            start_time = start_time_match.group(1) if start_time_match else None
            start_time = start_time[:-3]

            # Endzeit des Ereignisses extrahieren und von HH:MM:SS auf HH:MM formatieren
            end_time_match = re.search(r'to: (.+?)\)', event)
            end_time = end_time_match.group(1) if end_time_match else None
            end_time = end_time[:-3]

            # Abstand zwischen Titel und Startzeit berechnen und mit Leerzeichen auffüllen
            space_amount = 20 - len(subject)
            subject += space_amount * "&nbsp;"

            # Komplette Zeichenfolge mit Ereignisdetails erstellen und an calendar_events anhängen
            event_details = subject + ' um ' + start_time + ' - ' + end_time
            calendar_events += event_details + "\n"
        # Die Zeichenfolge mit den Ereignissen zurückgeben
        return(calendar_events)
    # Wenn der Account nicht authentifiziert ist, wird ein Fehler ausgegeben
    else:
        return('Authentication failed.')    

def get_tasks():
    """
    Ruft Aufgaben von Microsoft Graph API ab.

    Returns:
        str: Eine formatierte Zeichenfolge mit den abgerufenen Aufgaben.
    """
    # Die Datei mit dem Zugriffstoken öffnen
    try:
        with open(tokenfilepath, 'r') as f:
            access_token = f.read().strip()
    # Wenn die Datei nicht gefunden wird, wird ein Fehler ausgegeben
    except FileNotFoundError:
        access_token = None
        return("No token found. Please run get_token.py first.")

    # Aktualisieren des Zugriffstokens, wenn er abgelaufen ist
    if is_token_expired(access_token):
        refreshed_token = refresh_access_token(config.CLIENT_ID, config.SECRET_ID, tokenpath, tokenfilename, access_token)
        # Wenn der Zugriffstoken erfolgreich aktualisiert wurde, wird er ausgegeben, ansonsten wird ein Fehler ausgegeben
        if refreshed_token:
            access_token, expires_at = refreshed_token
            print('Refreshed Access Token:', access_token)
            print('Expires At:', expires_at)
        else:
            return("Token refresh failed.")

    # Ein Account-Objekt für die Microsoft Graph API erstellen
    credentials = (config.CLIENT_ID, config.SECRET_ID)
    account = Account(credentials, token_backend=FileSystemTokenBackend(token_path=tokenpath, token_filename=tokenfilename))
    # Wenn der Account nicht authentifiziert ist, wird er authentifiziert
    if not account.is_authenticated:
        account.authenticate(scopes=['basic', 'tasks_all'])
    # Mit der Microsoft Graph API die Aufgaben abrufen
    if account.is_authenticated:
        planner = account.planner()
        tasks = planner.get_my_tasks()
        task_list = ""
        # Für jede Aufgabe werden die Details extrahiert und in die task_list Zeichenfolge geschrieben
        for task in tasks:
            # Überprüfen, ob die Aufgabe abgeschlossen ist
            if not task.completed_date:
                # Titel der Aufgabe extrahieren
                subject = task.title
                # Fälligkeitsdatum der Aufgabe extrahieren
                due_date = task.due_date_time
                # Komplette Zeichenfolge mit Aufgabendetails erstellen
                task_details = subject 
                # Wenn die Aufgabe ein Fälligkeitsdatum hat, wird dieses an die Zeichenfolge angehängt
                if due_date:
                    task_details += ' bis ' + due_date.strftime("%d.%m")
            else:
                break                
            # task_details an task_list anhängen
            task_list += task_details + '\n'
        # Die Zeichenfolge mit den Aufgaben zurückgeben
        return(task_list)
    # Wenn der Account nicht authentifiziert ist, wird ein Fehler ausgegeben
    else:
        return('Authentication failed.')

def read_rss_feed(rss_url):
    """
    Liest RSS-Feeds von einer angegebenen URL.

    Args:
        rss_url (str): Die URL des RSS-Feeds.

    Returns:
        list: Eine Liste mit Titeln und Links der gelesenen RSS-Nachrichten.
    """
    # Setzen der Parameter für den API-Aufruf
    feed = feedparser.parse(rss_url)
    rss_items = feed['items']
    news = []
    # Für jede Nachricht werden Titel und Link in die news Liste geschrieben
    for item in rss_items:
        news.append(item['title'])
        news.append(item['link'])  
    # Die Liste mit den Nachrichten zurückgeben
    return news

# Function to get news
def get_news():
    """
    Liest RSS-Feeds von einer angegebenen URL.

    Args:
        rss_url (str): Die URL des RSS-Feeds.

    Returns:
        list: Eine Liste mit Titeln und Links der gelesenen RSS-Nachrichten.
    """
    # Setzen der Parameter für den API-Aufruf
    rss_url = "https://partner-feeds.beta.20min.ch/rss/20minuten"
    # Aufrufen der Funktion read_rss_feed mit der URL als Parameter
    news = read_rss_feed(rss_url)
    # Erstellen eines QR-Codes mit dem Link zur Nachricht
    qr = qrcode.QRCode(version=1, box_size=2, border=1)
    qr.add_data(news[1])
    qr.make(fit=True)
    # Speichern des QR-Codes als PNG-Bild
    img = qr.make_image(fill_color="black", back_color="white")
    qr_code_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ressources/newsqr.png')
    img.save(qr_code_file)
    # Den ersten Titel der Nachricht zurückgeben
    return(news[0])

def replace_data(replace_data_list, filedata):
    """
    Ersetzt Daten in einer HTML-Datei anhand einer Liste von Ersetzungen.

    Args:
        replace_data_list (list): Eine Liste von Ersetzungen als Tupel.
        filedata (str): Der Inhalt der HTML-Datei.

    Returns:
        str: Der aktualisierte Inhalt der HTML-Datei.
    """
    # Für jede Ersetzung in der Liste wird der erste Wert durch den zweiten Wert ersetzt
    for i in replace_data_list:
        filedata = re.sub(i[0], i[1], filedata)
    # Der aktualisierte Inhalt der HTML-Datei wird zurückgegeben
    return filedata

def capture_screenshot_from_file(file_path, image_path):
    """
    Erstellt einen Screenshot einer Webseite aus einer HTML-Datei und speichert ihn als PNG-Bild.

    Args:
        file_path (str): Der Pfad zur HTML-Datei.
        image_path (str): Der Pfad, unter dem das Bild gespeichert werden soll.
    """
    # Parameter für den Chrome Driver setzen
    service = Service('/usr/bin/chromedriver')
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=800x480")

    # Chrome Driver starten
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Absolute URL aus dem Pfad zur HTML-Datei erstellen
    url = 'file://' + os.path.abspath(file_path)

    # Zur URL navigieren
    driver.get(url)

    # Einen screenshot erstellen und speichern
    driver.save_screenshot(image_path)

    # Den Browser schliessen
    driver.quit()

def image_to_inky(image_path):
    """
    Lädt ein Bild, skaliert es und zeigt es auf einem Inky-Display an.

    Args:
        image_path (str): Der Pfad zum Bild.
    """
    # Inky Display initialisieren
    inky = auto(ask_user=True, verbose=True)
    # Helligkeit und Sättigung des Displays festlegen
    saturation = 1
    # Bild laden
    image = Image.open(image_path)
    # Bild skalieren
    resizedimage = image.resize(inky.resolution)
    # Bild auf Inky-Display anzeigen
    inky.set_image(resizedimage, saturation=saturation)
    inky.show()

# Locale für die Datums- und Zeitformatierung festlegen
locale.setlocale(locale.LC_TIME, 'de_CH.utf8')

# Headers für die API-Aufrufe festlegen
headers = {"accept": "application/json"}

# Prüfen, ob eine Internetverbindung besteht
if not check_internet():
    # Wenn keine Internetverbindung besteht, wird no_internet.html angezeigt
    image_to_inky(no_internetpath)
    # Error message anzeigen
    print("No internet connection available. Exiting...")
    exit()

# API-Aufruf für den Kalender
CALENDAR_EVENTS = get_calendar()
print(CALENDAR_EVENTS)
# API-Aufruf für die Aufgaben
TASKS = get_tasks()
print(TASKS)
# API-Aufruf für die News
NEWS = get_news()
print(NEWS)
# API-Aufruf für das Wetter
json_data =  json.loads(get_weather(config.Location))
print(json_data)
# Wenn die Beschreibung zu lang ist, wird sie mit einem Zeilenumbruch getrennt
if len(json_data["list"][0]["weather"][0]["description"]) > 15:
    json_data["list"][0]["weather"][0]["description"] = json_data["list"][0]["weather"][0]["description"].replace(" ", "<br/>")
if len(json_data["list"][2]["weather"][0]["description"]) > 15:
    json_data["list"][2]["weather"][0]["description"] = json_data["list"][2]["weather"][0]["description"].replace(" ", "<br/>")
# Konvertieren der Windgeschwindigkeit von m/s in km/h
json_data["list"][0]["wind"]["speed"] = round(json_data["list"][0]["wind"]["speed"] * 3.6, 1)
json_data["list"][2]["wind"]["speed"] = round(json_data["list"][2]["wind"]["speed"] * 3.6, 1)

# Die aktuellen Wetterdaten und die Wettervorhersage in Variablen speichern
json_data_now = json_data["list"][0]
json_data_forecast = json_data["list"][2]

# Zu ersetzende Daten für die HTML-Datei in einer Liste speichern
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

# HTML-Template Variablen mit den API Daten ersetzen
with open(templatepath, 'r') as file :
    filedata = file.read()
    filedata = replace_data(replace_data_list, filedata)
# HTML-Datei speichern
with open(htmlpath, 'w') as file:
    file.write(filedata)
# Screenshot der HTML-Datei erstellen
capture_screenshot_from_file(htmlpath, imgpath)
# Bild auf Inky-Display anzeigen
image_to_inky(imgpath)