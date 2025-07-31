from datetime import datetime, timezone

from app.api.routes import api_bp
from app.database import db_session
from app.helpers import Gender, TimeSpan
from app.services.classification import ClassificationService
from flask import jsonify, request


@api_bp.route('/classification', methods=['GET'])
def get_classification():
    """Get classification data"""
    gender = request.args.get('gender')

    if gender and gender not in Gender.values():
        return jsonify({"success": False, "error": "Invalid or no gender"}), 400

    genders = [Gender(gender)] if gender else Gender

    current_year = datetime.now(timezone.utc).year
    season_time_span = TimeSpan(
        start=datetime(current_year, 1, 1, tzinfo=timezone.utc),
        end=datetime(current_year, 12, 31, tzinfo=timezone.utc)
    )

    classification_service = ClassificationService(season_time_span)
    classification_service.query_from_db(db_session)
    classification_data = []

    for gender in genders:
        classification_data.extend(classification_service.yield_classification(gender))

    return jsonify(classification_data), 200
