"""Run this file to get appointments for the Acuity user and dates listed in local.py"""
import logging

import acuity
import helpers
import local

logging.basicConfig(filename='acuity_calendar.log',
                    level=logging.DEBUG)

appointments = helpers.calculate_effective_times(
    acuity.get_appointments(
        start_date=local.START_DATE,
        end_date=local.END_DATE,
    ),
    acuity.get_appointment_types()
)

if local.OUTPUT_FILE is not None:
    try:
        output_file = open(local.OUTPUT_FILE, 'wt')
    except(IOError):
        logging.error('Unable to open output file. Please check permissions.')
    print(helpers.print_busy_times(appointments), file=output_file)
    output_file.close()
else:
    print(helpers.print_busy_times(appointments))