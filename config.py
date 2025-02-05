# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    postgresql: dict = {
        'database': 'postgres',
        'user': 'postgres',
        'password': 'zhang202902',
        'host': 'localhost',
        'port': 5432
    }

def get_settings():
    return Settings()