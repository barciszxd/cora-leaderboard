"""Configuration module for Flask application"""

import os


class Config:
    """Base configuration"""
    CLIENT_ID = os.environ.get('CLIENT_ID')
    CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
    DATABASE_URL = os.environ.get('DATABASE_URL')
    STRAVA_VERIFY_TOKEN = os.environ.get('STRAVA_VERIFY_TOKEN')
    STRAVA_API_URL = "https://www.strava.com/api/v3"
    POINTS = [15, 12, 10, 8, 6, 4, 2, 1]  # Points for top 8 positions in a challenge
    MAX_COUNTED_RESULTS = 8  # Max number of results counted towards total classification
    TOKEN_ENC_KEY = os.environ.get('TOKEN_ENC_KEY')  # Base64-encoded 32-byte key

    # Auth cookie configuration
    COOKIE_NAME     = 'auth_session'  # HTTP-only cookie that holds the encrypted athlete_id
    COOKIE_MAX_AGE  = 86400           # 1 day in seconds
    COOKIE_HTTPONLY = True            # Never expose cookie to JavaScript


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SSL_ENABLE = False  # Disable SSL verification for development
    FRONTEND_URL = "http://localhost:8080"  # Development frontend URL

    # In development the frontend runs on the same machine but a different port,
    # so SameSite=Lax is sufficient and Secure is not required.
    COOKIE_SECURE   = False
    COOKIE_SAMESITE = 'Lax'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SSL_ENABLE = True  # Enable SSL verification for production
    FRONTEND_URL = os.environ.get('FRONTEND_URL')

    # Production frontend and backend are on different domains, so we need
    # SameSite=None (cross-site cookie) which mandates the Secure flag.
    COOKIE_SECURE   = True
    COOKIE_SAMESITE = 'None'


# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

config_name = os.environ.get('FLASK_ENV', 'default')
config = config_map.get(config_name, DevelopmentConfig)
