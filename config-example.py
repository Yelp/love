# -*- coding: utf-8 -*-
# Copy this file to config.py and change the settings. Don't forget to specify your own SECRET_KEY.

# The app name will be used in several places.
APP_NAME = 'Yelp Love'

APP_BASE_URL = 'https://PROJECT_ID.appspot.com/'

LOVE_SENDER_EMAIL = 'Yelp Love <love@PROJECT_ID.appspotmail.com>'

# We can use the 'appengine' email API or the 'sendgrid' API. Pick one here.
EMAIL_BACKEND = 'appengine'
# If you have EMAIL_BACKEND = 'sendgrid', you'll need to set the SENDGRID_API_KEY
# secret using the Secret Model. This is documented in the README in the discussion
# on "JSON via Amazon S3". You'll also need to add the sendgrid module to your
# requirements.txt. Note that you don't need it in your requirements if you don't
# have it chosen!

# Flask's secret key, used to encrypt the session cookie.
# Set this to any random string and make sure not to share this!
SECRET_KEY = 'YOUR_SECRET_HERE'

# Use default theme
THEME = 'default'

# Every employee needs a reference to a Google Account. This reference is based on the users
# Google Account email address and created when employee data is imported: we take the *username*
# and this DOMAIN
DOMAIN = 'example.com'

# Name of the S3 bucket used to import employee data from a file named employees.json
# Check out /import/employees.json to see how this file should look like.
S3_BUCKET = 'employees'

# When do we use Gravatar? Options are:
# * 'always' - prefers Gravatar over the Employee.photo_url
# * 'backup' - use Gravatar when photo_url is empty
# * anything else - disabled
GRAVATAR = 'backup'

ORG_TITLE = 'All Company'
