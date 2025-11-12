import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database configuration
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # API configuration
    API_PREFIX = '/api/v1'
    
    # Forecasting configuration
    DEFAULT_FORECAST_PERIODS = 12
    MOVING_AVERAGE_WINDOW = 3
    EXPONENTIAL_SMOOTHING_ALPHA = 0.3
