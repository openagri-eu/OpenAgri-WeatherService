import os
import dotenv


dotenv.load_dotenv()

LOGGING_LEVEL = os.environ.get('LOGGING_LEVEL', 'DEBUG')

DATABASE_URI = os.environ.get('DATABASE_URI', 'mongodb://root:root@localhost:27017/')
DATABASE_NAME = os.environ.get('DATABASE_NAME', '')
OPENWEATHERMAP_API_KEY = os.environ.get('OPENWEATHERMAP_API_KEY', '')
