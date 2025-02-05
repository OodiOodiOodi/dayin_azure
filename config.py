# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    postgresql: dict = {
        'database': 'dayinsystem-database',
        'user': 'dojattpgyo',
        'password': '8yQw02WwXFrPrM$C',
        'host': 'dayinsystem-cygnaybvb8f9e4d5.westus-01.azurewebsites.net',
        'port': 5432
    }

def get_settings():
    return Settings()