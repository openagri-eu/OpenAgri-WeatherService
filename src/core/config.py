import os
import dotenv

from src.core.jobs import caclulate_forecast_for_farm, calculate_spray_forecast_for_farm, calculate_thi_for_parcel


dotenv.load_dotenv()

# LOGGING
LOGGING_LEVEL = os.environ.get('LOGGING_LEVEL', 'INFO')

# SERVER
WEATHER_SRV_PORT = os.environ.get('WEATHER_SRV_PORT', '8000')
WEATHER_SRV_HOSTNAME = os.environ.get('WEATHER_SRV_HOSTNAME', 'weathersrv')

# DB
DATABASE_URI = os.environ.get('WEATHER_SRV_DATABASE_URI', 'mongodb://root:root@localhost:27017/')
DATABASE_NAME = os.environ.get('WEATHER_SRV_DATABASE_NAME', 'openagridb')
OPENWEATHERMAP_API_KEY = os.environ.get('WEATHER_SRV_OPENWEATHERMAP_API_KEY', '')

# ALLOWED_HOSTS
EXTRA_ALLOWED_HOSTS = os.environ.get('EXTRA_ALLOWED_HOSTS', "*").replace(' ', '').split(',')

# GATEKEEPER
GATEKEEPER_URL = os.environ.get('GATEKEEPER_URL', '')
WEATHER_SRV_GATEKEEPER_USER = os.environ.get('WEATHER_SRV_GATEKEEPER_USER', '')
WEATHER_SRV_GATEKEEPER_PASSWORD = os.environ.get('WEATHER_SRV_GATEKEEPER_PASSWORD', '')

# APP
CURRENT_WEATHER_DATA_CACHE_TIME = os.environ.get('CURRENT_WEATHER_DATA_CACHE_TIME', 1)

# FARM CALENDAR
PUSH_THI_TO_FARMCALENDAR=os.environ.get('PUSH_THI_TO_FARMCALENDAR', '')
PUSH_FLIGHT_FORECAST_TO_FARMCALENDAR=os.environ.get('PUSH_FLIGHT_FORECAST_TO_FARMCALENDAR', '')
PUSH_SPRAY_F_TO_FARMCALENDAR=os.environ.get('PUSH_SPRAY_F_TO_FARMCALENDAR', '')
FARM_CALENDAR_URL = os.environ.get('FARM_CALENDAR_URL', 'http://farmcalendar:8002')
INTERVAL_THI_TO_FARMCALENDAR = os.environ.get('INTERVAL_HOURS_THI_TO_FARMCALENDAR', 8)

# TASKS
JOBS = {
            'calculate_uav_forecast': {
                'name': caclulate_forecast_for_farm,
                'config': {
                    'trigger': 'interval',
                    'options': {
                        # 'days': 1
                        'minutes': 1
                    }
                }
            },
            'calculate_spray_indicator': {
                'name': calculate_spray_forecast_for_farm,
                'config': {
                    'trigger': 'interval',
                    'options': {
                        # 'days': 1
                        'minutes': 1
                    }
                }
            },
            'calculate_thi': {
                'name': calculate_thi_for_parcel,
                'config': {
                    'trigger': 'interval',
                    'options': {
                        # 'hours': INTERVAL_THI_TO_FARMCALENDAR
                        'minutes': 1
                    }
                }
            }
}

# JWT
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get('ACCESS_TOKEN_EXPIRE_MINUTES', '240'))
KEY = os.environ.get('JWT_KEY', 'some-key')
ALGORITHM = os.environ.get('ALGORITHM', 'HS256')
CRYPT_CONTEXT_SCHEME = os.environ.get('CRYPT_CONTEXT_SCHEME', 'bcrypt')
