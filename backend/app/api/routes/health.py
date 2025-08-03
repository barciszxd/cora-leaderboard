import logging

from app.api.routes import api_bp
from app.database import get_db_session
from flask import jsonify
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "Flask API is running successfully"
    })


@api_bp.route('/health/db', methods=['GET'])
def database_health_check():
    """Database connectivity health check"""
    try:
        session = get_db_session()
        # Simple query to test database connectivity
        session.execute(text("SELECT 1"))
        session.close()

        return jsonify({
            "status": "healthy",
            "message": "Database connection is working",
            "database": "connected"
        }), 200

    except OperationalError as e:
        logger.error("Database health check failed: %s", e)
        return jsonify({
            "status": "unhealthy",
            "message": "Database connection failed",
            "database": "disconnected",
            "error": str(e)
        }), 503

    except Exception as e:
        logger.error("Unexpected error in database health check: %s", e)
        return jsonify({
            "status": "error",
            "message": "Health check error",
            "error": str(e)
        }), 500
