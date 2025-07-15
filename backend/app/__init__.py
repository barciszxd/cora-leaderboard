"""Flask application factory"""
import os

from app.database import init_db
from config import config
from flask import Flask


def create_app():
    """Create and configure Flask application"""
    flask_app = Flask(__name__)

    # Initialize database tables
    init_db()

    # Load configuration
    flask_app.config.from_object(config)

    # Register blueprints
    from app.api.routes import api_bp  # pylint: disable=import-outside-toplevel
    flask_app.register_blueprint(api_bp, url_prefix='/api')

    return flask_app


app = create_app()

if __name__ == '__main__':
    app.run()
