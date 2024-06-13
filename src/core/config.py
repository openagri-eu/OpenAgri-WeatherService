import os
from typing import Optional

DATABASE_URI = str(os.environ.get('DATABASE_URL', 'mongodb://root:root@localhost:27017/'))
DATABASE_NAME = str(os.environ.get('DATABASE_NAME', 'openagridb'))