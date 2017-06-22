"""Run this file to get appointments for the Acuity user and dates listed in local.py"""
import logging, datetime

import acuity
import helpers
import local
import google_api

logging.basicConfig(filename='acuity_calendar.log',
                    level=local.LOG_LEVEL)

appointments = helpers.calculate_effective_times(
    helpers.get_all_acuity_appts(),
    acuity.get_appointment_types()
)
logging.info("{} appointments found in acuity".format(len(appointments)))

earliest, latest = helpers.find_bookend_dates(appointments)

calendar_service = google_api.get_calendar_service()
calendar_id = local.CALENDAR_ID

event_list = google_api.get_event_list(calendar_service, start_date=earliest, end_date=latest)

event_list = helpers.remove_cancelled_appointments(appointments, event_list)

for appointment in appointments:
    helpers.check_for_and_create_event(appointment, calendar_service, calendar_id, event_list=event_list)
