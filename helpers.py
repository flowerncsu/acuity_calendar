"""This module contains shortcut and utility functions"""
import datetime
import logging
import time

import local
import google_api
import constants
import acuity

logging.basicConfig(filename='acuity_calendar.log',
                    level=local.LOG_LEVEL)


def remove_cancelled_appointments(acuity_list, google_list):
    deleted = 0
    for google_appt in google_list:
        for acuity_appt in acuity_list:
            if events_match(google_appt, acuity_appt):
                break
        else:
            google_api.delete_event(google_appt)
            google_list.pop(google_appt)
            deleted += 1
    logging.info("Deleted {} cancelled appts from google calendar".format(deleted))
    return google_list


def events_match(acuity_event, google_event):
    return (str(acuity_event['appt_id']) == google_event['description'] and
            acuity_event['start_time'] == datetime_from_google_time(google_event['start']['dateTime']) and
            acuity_event['end_time'] == datetime_from_google_time(google_event['end']['dateTime']))


def find_bookend_dates(appointments):
    earliest = appointments[0]['date']
    latest = earliest
    for appointment in appointments:
        if appointment['date'] < earliest:
            earliest = appointment['date']
        elif appointment['date'] > latest:
            latest = appointment['date']
    logging.info("Dates range from {} to {}".format(earliest, latest))
    return datetime.datetime.combine(
        earliest, datetime.datetime.min.time()
    ), datetime.datetime.combine(
        latest, datetime.datetime.min.time())


def get_all_acuity_appts():
    time_span = constants.DEFAULT_TIME_SPAN
    start_date = datetime.datetime.now().date()
    end_date = start_date + datetime.timedelta(days=time_span)
    results = []
    new_results = acuity.get_appointments(start_date, end_date)
    while new_results:
        results += new_results
        if len(new_results) * 2 < constants.MAX_RESULTS_PER_REQUEST:
            time_span *= 2
        start_date = end_date + datetime.timedelta(days=1)
        end_date = start_date + datetime.timedelta(days=time_span)
        new_results = acuity.get_appointments(start_date, end_date)
    return results


def calculate_effective_times(appointments, appointment_types):
    """
    Input appointment information and appointment type information
    Adjust appointment times to include padding, and return adjusted appointment information
    """
    appointments_with_types = []
    for appointment in appointments:
        for item in appointment_types:
            if item['type_id'] == appointment['type_id']:
                appointment.update(item)
                # Type information is present; parse and calculate the times and durations
                appointment['date'] = datetime.datetime.strptime(appointment['date'], '%B %d, %Y').date()
                appointment['appt_time'] = datetime.datetime.strptime(appointment['appt_time'], '%I:%M%p').time()
                appointment['start_time'] = datetime.datetime.combine(
                    appointment['date'], appointment['appt_time']
                ) - datetime.timedelta(minutes=int(appointment['paddingBefore']))
                appointment['effective_duration'] = int(appointment['duration']) + int(appointment['paddingAfter'])
                appointment['end_time'] = appointment['start_time'] + datetime.timedelta(
                    minutes=appointment['effective_duration'])
                appointments_with_types.append(appointment)
                break
        else:
            logging.warning(
                'No appointment type found for appointment ID {}, type ID {}'.format(
                    appointment['appt_id'],
                    appointment['type_id']
                )
            )
    return appointments_with_types


def print_busy_times(appointments):
    output_str = ''
    if len(appointments) > 0:
        busy_times = {}
        earliest_date = None
        for appointment in appointments:
            if appointment['date'] in busy_times:
                # There's already a recorded appointment for this date
                busy_times[appointment['date']].append(
                    {
                    'start': appointment['start_time'],
                    'end': appointment['start_time'] + datetime.timedelta(minutes = appointment['effective_duration'])
                    }
                )
                pass
            else:
                # This is the first appointment for this date
                busy_times[appointment['date']] = [{
                    'start': appointment['start_time'].time(),
                    'end': (appointment['start_time'] + datetime.timedelta(minutes = appointment['effective_duration'])).time()
                }]
                # See if it's the earliest date
                if earliest_date is None or earliest_date > appointment['date']:
                    earliest_date = appointment['date']
        while len(busy_times) > 1:
            output_str += pretty_print(earliest_date, busy_times.pop(earliest_date))
            # Find next earliest
            sorted_keys = list(busy_times.keys())
            sorted_keys.sort()
            earliest_date = sorted_keys[0]
        # Only one time remaining
        output_str += pretty_print(list(busy_times.keys())[0], list(busy_times.values())[0])
    else:
        output_str += "No appointments found in this range"
    return output_str


def pretty_print(date, times,):
    output_str = 'Busy times for ' + date.strftime('%B %d, %Y') + ' are:\n'
    for time in times:
        output_str += '   ' + time['start'].strftime('%I:%M %p') + ' to ' + time['end'].strftime('%I:%M %p') + '\n'
    return output_str


def datetime_from_google_time(google_timestamp):
    # Remove the colon that python doesn't know what to do with
    parsed_timestamp = google_timestamp[:-3] + google_timestamp[-2:]

    return datetime.datetime.strptime(parsed_timestamp, '%Y-%m-%dT%H:%M:%S%z')


def google_time_from_datetime(input_datetime):
    return input_datetime.isoformat()


def check_for_and_create_event(appointment, calendar_service, calendar_id='primary', timezone=local.DEFAULT_TIMEZONE, event_list=None):
    """
    Check the appointment to see if it already exists (appt_id is in the description of an appt with the correct
    start and end times) in the google event list provided.
    Create it if it does not exist.

    If calendar_id is not provided, the primary calendar for the account will be used.
    If timezone is not provided, the default (from local settings) will be used.
    If event_list is not provided, function will call google API to get the event list for the appt's date.
    """
    if not event_list:
        event_list = google_api.get_event_list(
            calendar_service,
            calendar_id=calendar_id,
            start_date=appointment['date'],
            end_date=appointment['date'] + datetime.timedelta(days=1)
        )
    for event in event_list:
        if 'description' in event and str(appointment['appt_id']) in event['description']:
            # Appointment exists; see if time is correct or if appt moved
            logging.debug("Google calendar event with appointment ID {} has been found".format(appointment['appt_id']))
            if not (appointment['start_time'] == datetime_from_google_time(event['start']['dateTime'])
                    and appointment['end_time'] == datetime_from_google_time(event['end']['dateTime'])):
                # Wrong time; delete incorrect appt
                logging.debug("Existing event has wrong time; deleting")
                google_api.delete_event(event, calendar_service, calendar_id)
            else:
                # Event matches appt, nothing to do here
                break
    else:  # if no break
        logging.debug("Creating event with appointment ID " + str(appointment['appt_id']))
        google_api.post_event_to_google(
            appointment['start_time'],
            appointment['end_time'],
            timezone,
            appointment['type_name'],
            appointment['appt_id'],
            calendar_service,
            calendar_id
        )


def delete_all_google_appts(calendar_service, start_date, end_date, calendar_id='primary'):
    # Intended for cleanup during testing/debugging
    event_list = google_api.get_event_list(calendar_service, start_date=start_date, end_date=end_date, calendar_id=calendar_id)
    for event in event_list:
        google_api.delete_event(event, calendar_service, calendar_id=calendar_id)
        # Avoid google's rate limit
        time.sleep(0.004)
