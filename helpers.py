"""This module contains shortcut functions"""
import datetime
import logging

logging.basicConfig(filename='acuity_calendar.log',
                    level=logging.DEBUG)


def calculate_effective_times(appointments, appointment_types):
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