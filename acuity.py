"""This module handles all interactions with the Acuity API"""
import requests
import json
import datetime
import logging

import constants
import local

logging.basicConfig(filename='acuity_calendar.log',
                    level=logging.DEBUG)


def get_appointments(start_date=None, end_date=None):
    if start_date is None:
        # Set start date to current date if not provided
        start_date = datetime.datetime.now().date()
    if end_date is None:
        # Use default duration if no end date provided
        end_date = start_date + datetime.timedelta(days=constants.DEFAULT_TIME_SPAN)
    response = requests.get(
        "https://acuityscheduling.com/api/v1/appointments",
        auth=(local.USER_ID, local.API_KEY),
        params={
            'minDate': start_date.isoformat(),
            'maxDate': end_date.isoformat(),
            'max': constants.MAX_RESULTS_PER_REQUEST,
        }
    )
    response_data = json.loads(response.content.decode())
    if len(response_data) == constants.MAX_RESULTS_PER_REQUEST:
        # Too many results, break time in half and try again
        logging.debug('Reached max results, splitting time and trying again')
        new_time_span = datetime.timedelta(days=round((end_date - start_date).days/2))
        if new_time_span == end_date-start_date or new_time_span.days == 0:
            # This recursion will not work, bail and log
            logging.error('Too many results from one request; try increasing the maximum')
        else:
            return (
                get_appointments(start_date=start_date,
                                 end_date=start_date + new_time_span) +
                get_appointments(start_date=start_date + new_time_span + datetime.timedelta(days=1),
                                 end_date=end_date)
            )
    else:
        return[{
            'appt_time': item['time'],
            'date': item['date'],
            'appt_id': item['id'],
            'type_id': item['appointmentTypeID'],
            'duration': item['duration']
        } for item in response_data]


def get_appointment_types():
    response = requests.get("https://acuityscheduling.com/api/v1/appointment-types",
                            auth=(local.USER_ID, local.API_KEY))
    response_data = json.loads(response.content.decode())
    return [{'type_name': item['name'],
             'type_id': item['id'],
             'default_duration': item['duration'],
             'paddingBefore': item['paddingBefore'],
             'paddingAfter':item['paddingAfter']
             } for item in response_data]