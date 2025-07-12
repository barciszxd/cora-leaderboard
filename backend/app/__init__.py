"""Flask application factory"""
from flask import Flask
from config import config

def create_app(config_name='default'):
    """Create and configure Flask application"""
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config[config_name])
    
    # Register blueprints
    from app.api.routes import api_bp   # pylint: disable=import-outside-toplevel
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # from app.main.routes import main_bp
    # app.register_blueprint(main_bp)
    
    return app