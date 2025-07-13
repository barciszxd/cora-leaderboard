"""Flask application factory"""
import os

from config import config
from flask import Flask


def create_app():
    """Create and configure Flask application"""
    flask_app = Flask(__name__)

    # Load configuration
    flask_app.config.from_object(config)

    # Register blueprints
    from app.api.routes import api_bp  # pylint: disable=import-outside-toplevel
    flask_app.register_blueprint(api_bp, url_prefix='/api')

    # from app.main.routes import main_bp
    # app.register_blueprint(main_bp)

    return flask_app


app = create_app()

if __name__ == '__main__':
    app.run()
