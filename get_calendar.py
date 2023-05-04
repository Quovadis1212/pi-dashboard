import datetime
from O365 import Account, MSGraphProtocol
import re
#import config.py with api keys
import config

calendar_events = ""


credentials = (config.CLIENT_ID, config.SECRET_ID)

protocol = MSGraphProtocol() 
scopes = ['Calendars.Read.Shared']
account = Account(credentials, protocol=protocol)

# Set the start and end times to include events for today
today = datetime.datetime.utcnow().date()
start = datetime.datetime.combine(today, datetime.time.min).isoformat() + 'Z'
end = datetime.datetime.combine(today, datetime.time.max).isoformat() + 'Z'

if account.authenticate(scopes=scopes):
   print('Authenticated!')

# Get Calendar Events for Today 
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
    space_amount = 20 - len(subject)
    subject += space_amount * "&nbsp;"
    event_details = subject + ' um ' + start_time + ' - ' + end_time
    calendar_events += event_details + "\n"

print(calendar_events)

