"""Configuration module for Flask application"""

import os


class Config:
    """Base configuration"""
    CLIENT_ID = os.environ.get('CLIENT_ID')
    CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
    DATABASE_URL = os.environ.get('DATABASE_URL')
    STRAVA_VERIFY_TOKEN = os.environ.get('STRAVA_VERIFY_TOKEN')
    STRAVA_API_URL = "https://www.strava.com/api/v3"
    POINTS = [15, 12, 10, 8, 6, 4, 2, 1]  # Points for top 8 positions


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SSL_ENABLE = False  # Disable SSL verification for development
    FRONTEND_URL = "http://localhost:8080"  # Development frontend URL


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SSL_ENABLE = True  # Enable SSL verification for production
    FRONTEND_URL = os.environ.get('FRONTEND_URL')


# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

config_name = os.environ.get('FLASK_ENV', 'default')
config = config_map.get(config_name, DevelopmentConfig)
