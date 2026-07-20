import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    EXTERNAL_API_BASE_URL = os.environ.get('EXTERNAL_API_BASE_URL', 'http://localhost:8000/')

    CANDIDATE_ID = os.environ.get('CANDIDATE_ID', '')

    DATABASE_PATH = os.environ.get('DATABASE_PATH', 'app_data.sqlite3')
    REQUEST_TIMEOUT = int(os.environ.get('REQUEST_TIMEOUT', '30'))

    DISPLAY_TIMEZONE = os.environ.get('DISPLAY_TIMEZONE', 'Asia/Novosibirsk')
