"""Run this file to create a json file containing all appointments for the Acuity user listed in local.py"""
import logging, json

import acuity
import helpers
import local

logging.basicConfig(filename='acuity_calendar.log',
                    level=local.LOG_LEVEL)

appointments = helpers.calculate_effective_times(
    helpers.get_all_acuity_appts(),
    acuity.get_appointment_types()
)
logging.info("{} appointments found in acuity".format(len(appointments)))

try:
    json_file = open('appointments.json', 'w')
except IOError:
    logging.critical('Error opening `appointments.json`')
else:
    json.dump(helpers.format_appointments_for_json(appointments), json_file)
    json_file.close()


