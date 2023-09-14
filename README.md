# Raspberry Pi Projekt README

## Allgemeine Informationen
### Benötigte Produkte
- 1x Raspberry Pi Zero WH Kit
- 1x Inky Impression 7.3" (7-Farb-ePaper/E Ink HAT)
- Micro SD Karte (mindestens 8GB)

### Sicherheitsinformationen
- Die 5V-Speisung des Pi Zero W nur am vom Hersteller angegebenen Anschluss anschließen.
- Die Geräte gemäß den Herstellerangaben behandeln.
- Die aktuelle Software befindet sich auf der [Github-Seite](https://github.com/Quovadis1212/pi-dashboard/tree/dev).

## Vorbereitung
### Voraussetzungen
- Das Raspberry Pi Zero WH Kit bereits mit den GPIO-Headern gelötet verwenden.
- Der Raspberry Pi Zero W wurde bereits mit Raspberry Pi OS legacy, Debian Version: 10/"Buster" vorbereitet.
- Der Raspberry Pi Zero W hat eine Verbindung mit dem gleichen WLAN wie das Gerät, von dem man die Befehle an den RPI sendet.

## Verkabelung / Aufbau
- Die folgenden Anweisungen basieren auf der Verbindung zum Raspberry Pi Zero W über SSH.

## Zugriff auf den Raspberry Pi
- Verwenden Sie SSH, um sich mit dem Raspberry Pi Zero W zu verbinden: `ssh pi@<IP-Adresse-von-PI>`

## Installation der Software
1. Erstellen Sie ein Setup-Skript und fügen Sie den Code von der Github-Seite `setup.sh` ein.
2. Führen Sie das Setup-Skript aus: `sh setup.sh`
3. Nach erfolgreicher Installation wechseln Sie zum Programmverzeichnis: `cd pi-dashboard`

## Konfiguration des Config-Files
- Passen Sie nach Bedarf die Standortdaten für das Wetter an: `nano config.py`
- Erstellen Sie eine Anwendung in [Azure](https://pietrowicz-eric.medium.com/how-to-read-microsoft-outlook-calendars-with-python-bdf257132318), um die O365 Funktionen mit Ihrem Tenant zu nutzen. Tragen sie die Informationen ins Config-File ein.


## Freigabe des M365 Tokens
- Fordern Sie den aktuellen API-Key für das Office 365 Konto an: `python3 get_token.py`

## Programmstart
- Um das Programm manuell auszuführen, stellen Sie sicher, dass Sie sich im Verzeichnis "pi@raspberrypi:~/pi-dashboard $" befinden, und führen Sie den Befehl aus: `python3 generate_dashboard.py`
- Das Programm wird durch einen Cronjob alle 10 Minuten ausgeführt und aktualisiert die Daten auf dem Display.
