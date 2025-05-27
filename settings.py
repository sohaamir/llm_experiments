# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------- SETTINGS FOR MULTI-APP OTREE PROJECT ----------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

import os
from os import environ
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# SECURITY SETTINGS
# ----------------------------------------------------------------
SECRET_KEY = os.environ.get('OTREE_SECRET_KEY')
DEBUG = True if os.environ.get('OTREE_PRODUCTION') != '1' else False
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Admin credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

# OTREE-SPECIFIC SETTINGS
# ----------------------------------------------------------------
OTREE_PRODUCTION = True
PARTICIPANT_FIELDS = ['finished']
SESSION_FIELDS = []
USE_POINTS = False

# DATABASE CONFIGURATION
# ----------------------------------------------------------------
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# SESSION CONFIGURATION
# ----------------------------------------------------------------
SESSION_CONFIGS = [
    dict(
        name='rps_oneshot',
        app_sequence=['rps_oneshot'],
        num_demo_participants=1,
        display_name='Rock Paper Scissors (Single Player)',
        doc="Single-player one-shot Rock Paper Scissors game"
    ),
    dict(
        name='rps_repeat',
        app_sequence=['rps_repeat'],
        num_demo_participants=2,
        display_name='Rock Paper Scissors (Multi-Round)',
        doc="Multi-round Rock Paper Scissors between two players"
    ),
]

# Default configuration for all sessions
SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=0.00,
    participation_fee=0.00,
    payoff=10.00,
    doc=""
)

# ROOM CONFIGURATION
# ----------------------------------------------------------------
ROOMS = [
    dict(
        name='multi_app_experiments',
        display_name='Multi-App Experiments (LLM Bots)',
    ),
]

# LOCALIZATION SETTINGS
# ----------------------------------------------------------------
LANGUAGE_CODE = 'en'
REAL_WORLD_CURRENCY_CODE = 'GBP'

# STATIC FILES CONFIGURATION
# ----------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, '_static'),
]

# PROFILER SETTINGS
# ----------------------------------------------------------------
USE_PROFILER = True