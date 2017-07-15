"""This module handles all interactions with the Google API"""
import datetime
import os
import logging

import httplib2
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from googleapiclient.errors import HttpError

import constants
import helpers
import local

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

logging.basicConfig(filename='acuity_calendar.log',
                    level=local.LOG_LEVEL)

GOOGLE_TIMESTAMP_FORMAT = '%Y-%m-%dT%H:%M:%S%z'

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/acuity-integration-with-google.json'
SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Acuity Calendar'


def post_event_to_google(start_time, end_time, timezone, summary, description, calendar_service, calendar_id='primary'):
    event = {
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': timezone
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': timezone
        },
        'summary': summary,
        'description': description
    }
    calendar_service.events().insert(calendarId=calendar_id, body=event).execute()


def delete_event(event, calendar_service, calendar_id='primary'):
    try:
        calendar_service.events().delete(eventId=event['id'], calendarId=calendar_id).execute()
    except HttpError as error:
        logging.warning(str(error) + ' while attempting to delete event with id ' + event['id'])


def update_time_of_event(event, new_start_time, new_end_time, calendar_service, calendar_id='primary'):
    # TODO: figure out why this function erases any summary or description that already exist on the event
    if 'summary' not in event['summary']:
        event['summary'] = ''
    if 'description' not in event['description']:
        # I don't even know why you're calling this function if there's no description,
        # but this will keep it from crashing
        event['description'] = ''
    calendar_service.events().update(
        eventId=event['id'],
        calendarId=calendar_id,
        body={
            'start': {
                'dateTime': helpers.google_time_from_datetime(new_start_time),
                'timeZone': event['start']['timeZone']
            },
            'end': {
                'dateTime': helpers.google_time_from_datetime(new_end_time),
                'timeZone': event['end']['timeZone']
            },
            'summary': event['summary'],
            'description': event['description']
        }
    ).execute()


def get_event_list(calendar_service, calendar_id='primary', start_date=None, end_date=None):
    if start_date is None:
        # Set start date to current date if not provided
        start_date = datetime.datetime.now()
    if end_date is None:
        # Use default duration if no end date provided
        end_date = start_date + datetime.timedelta(days=constants.DEFAULT_TIME_SPAN)
    try:
        eventsResult = calendar_service.events().list(
            calendarId=calendar_id,
            timeMin=start_date.isoformat() + 'Z',
            timeMax=end_date.isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute()

    except HttpError as error:
        # Google has this crazy idea that if there are no events in the time range you request, you should
        # get a 400 error. Similarly unhelpfully, it will give you no more detail than the fact that it is a
        # 400 error. So catch any 400 error and just return an empty list.
        if error.args[0]['status'] == '400':
            logging.error("Response from google was 400 when requesting event list; likely due to empty calendar.")
            return []
        else:
            raise error
    else:
        results = eventsResult.get('items', [])
        logging.info("Found {} events from google".format(len(results)))
        return results


def get_calendar_list(calendar_service):
    return calendar_service.calendarList().list().execute()


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'acuity-integration-with-google.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def get_calendar_service():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    return discovery.build('calendar', 'v3', http=http)

def main():
    """Shows basic usage of the Google Calendar API.

    Creates a Google Calendar API service object and outputs a list of the next
    10 events on the user's calendar.
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    print('Getting the upcoming 10 events')
    eventsResult = service.events().list(
        calendarId='primary', timeMin=now, maxResults=10, singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event['summary'])


if __name__ == '__main__':
    main()