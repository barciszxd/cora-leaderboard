import os

class Config:
    """Base configuration"""
    # SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    
class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    # DATABASE_URL = 'sqlite:///dev.db'
    
class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    # DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///prod.db'

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}