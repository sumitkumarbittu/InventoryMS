import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'inventory_management')
    DB_PORT = int(os.getenv('DB_PORT', 5432))
    
    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # API configuration
    API_PREFIX = '/api/v1'
    
    # Forecasting configuration
    DEFAULT_FORECAST_PERIODS = 12
    MOVING_AVERAGE_WINDOW = 3
    EXPONENTIAL_SMOOTHING_ALPHA = 0.3
