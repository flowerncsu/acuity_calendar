# Please fill in the values below and rename this file to local.py (remove '.example' from its name)
import datetime

# Use these lines to specify a start and end date.
start = {
    'month': 4,
    'day': 1,
    'year': 2017
}
end = {
    'month': 4,
    'day': 30,
    'year': 2017
}
# Do not change the next 2 lines, although you may comment them out if you
# use the definitions below these instead
START_DATE = datetime.datetime(start['year'], start['month'], start['day'])
END_DATE = datetime.datetime(end['year'], end['month'], end['day'])

# Use these lines to default to a time range starting
# on the current date and covering 7 days
# START_DATE = None
# END_DATE = None


# Optionally, specify a filename to output the information to
# OUTPUT_FILE = 'output.txt'
OUTPUT_FILE = None

# Find these values at https://secure.acuityscheduling.com/app.php?action=settings&key=api
USER_ID = 'Acuity User ID'
API_KEY = 'Acuity API Key'
