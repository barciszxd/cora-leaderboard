"""Flask application factory"""
import logging

from app.database import close_db_session, init_db
from config import config
from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


def create_app():
    """Create and configure Flask application"""
    flask_app = Flask(__name__)

    @flask_app.errorhandler(SQLAlchemyError)
    def handle_database_error(error):
        """Global database exception handler"""
        logger.error("Database error: %s", error)
        return jsonify({
            "success": False,
            "error": "Database connection issue. Please try again.",
            "details": str(error)
        }), 503

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
app.teardown_appcontext(close_db_session)

if __name__ == '__main__':
    app.run()
