import os
from dotenv import load_dotenv

load_dotenv()  # Carrega variáveis do .env

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:semensol@db.bxmxwmdokaptetkxpdbi.supabase.co:5432/postgres'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')

    # Configurações da balança TC420
    SERIAL_PORT = os.getenv('SERIAL_PORT', '/dev/ttyUSB0')  # ou 'COM3' no Windows
    SERIAL_BAUDRATE = int(os.getenv('SERIAL_BAUDRATE', 9600))
    SERIAL_TIMEOUT = float(os.getenv('SERIAL_TIMEOUT', 1))
    SERIAL_RETRIES = int(os.getenv('SERIAL_RETRIES', 3))
    READ_SLEEP = float(os.getenv('READ_SLEEP', 0.2))
    READ_BYTES = int(os.getenv('READ_BYTES', 100))


def get_config():
    return Config
