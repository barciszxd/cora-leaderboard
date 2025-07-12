"""Flask application factory"""
import os

from flask import Flask
from config import config


def create_app():
    """Create and configure Flask application"""
    flask_app = Flask(__name__)

    # Load configuration
    config_name = os.environ.get('FLASK_ENV', 'default')
    flask_app.config.from_object(config[config_name])

    # Register blueprints
    from app.api.routes import api_bp   # pylint: disable=import-outside-toplevel
    flask_app.register_blueprint(api_bp, url_prefix='/api')

    # from app.main.routes import main_bp
    # app.register_blueprint(main_bp)

    return flask_app


app = create_app()

if __name__ == '__main__':
    app.run()
