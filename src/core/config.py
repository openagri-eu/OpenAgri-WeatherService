import os
from typing import Optional

DATABASE_URI = str(os.environ.get('DATABASE_URI', 'mongodb://root:root@localhost:27017/'))
DATABASE_NAME = str(os.environ.get('DATABASE_NAME', ''))
OPENWEATHERMAP_API_KEY=str(os.environ.get('OPENWEATHERMAP_API_KEY', ''))
