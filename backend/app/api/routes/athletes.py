import app.services.athlete as athlete_service

from app.api.routes import api_bp
from app.database import db_session
from flask import jsonify


@api_bp.route('/athletes', methods=['GET'])
def get_athletes():
    """Get all athletes"""
    athlete_repo = athlete_service.AthleteRepository(db_session)
    athletes = athlete_repo.get_all()

    if not athletes:
        return jsonify({"success": False, "error": "No athletes found"}), 404

    # Convert athletes to a list of dictionaries

    return jsonify([{
        "id": athlete.id,
        "name": f"{athlete.firstname} {athlete.lastname}",
        "gender": athlete.sex,
    } for athlete in athletes]), 200
