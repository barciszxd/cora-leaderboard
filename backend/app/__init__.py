"""Flask application factory"""
import importlib

from app.database import init_db
from config import config
from flask import Flask
from flask_cors import CORS


def create_app():
    """Create and configure Flask application"""
    flask_app = Flask(__name__)

    # Initialize database tables
    init_db()

    # Load configuration
    flask_app.config.from_object(config)

    # Register blueprints
    from app.api.routes import api_bp  # pylint: disable=import-outside-toplevel

    if config.DEBUG:
        CORS(flask_app, origins=['http://localhost:8080'])
    else:
        CORS(flask_app,
             origins              = [config.FRONTEND_URL],
             methods              = ['GET', 'POST', 'PUT', 'DELETE'],
             allow_headers        = ['Content-Type'])

    flask_app.register_blueprint(api_bp, url_prefix='/api')

    return flask_app


app = create_app()

if __name__ == '__main__':
    app.run()
