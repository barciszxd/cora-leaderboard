"""Flask application factory"""
from flask import Flask
from config import config
import os

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)

    # Load configuration
    config_name = os.environ.get('FLASK_ENV', 'default')
    app.config.from_object(config[config_name])
    
    # Register blueprints
    from app.api.routes import api_bp   # pylint: disable=import-outside-toplevel
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # from app.main.routes import main_bp
    # app.register_blueprint(main_bp)
    
    return app