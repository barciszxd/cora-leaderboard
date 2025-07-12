"""Configuration module for Flask application"""
class Config:
    """Base configuration"""
    # SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    
class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    # DATABASE_URL = 'sqlite:///dev.db'
    
class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    # DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///prod.db'

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}