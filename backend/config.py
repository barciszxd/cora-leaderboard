"""Configuration module for Flask application"""

import os


class Config:
    """Base configuration"""
    CLIENT_ID = os.environ.get('CLIENT_ID')
    CLIENT_SECRET = os.environ.get('CLIENT_SECRET')


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SSL_ENABLE = False  # Disable SSL verification for development
    # DATABASE_URL = 'sqlite:///dev.db'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SSL_ENABLE = True  # Enable SSL verification for production
    # DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///prod.db'


# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

config_name = os.environ.get('FLASK_ENV', 'default')
config = config_map.get(config_name, DevelopmentConfig)
