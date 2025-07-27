import app.services.challenge as challenge_service

from app.api.routes import api_bp
from app.database import db_session
from flask import jsonify, request


@api_bp.route('/challenges', methods=['POST'])
def create_challenge():
    """Create a new challenge"""
    data = request.json
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400
    segment_id = data.get('segment_id')
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    challenge_repo = challenge_service.ChallengeRepository(db_session)
    challenge_repo.add(segment_id, start_date, end_date)
    db_session.commit()

    return jsonify({"success": True, "message": "Challenge created successfully."}), 201


@api_bp.route('/challenges', methods=['GET'])
def get_challenge():
    """Get challenge by ID or current challenge"""
    challenge_repo = challenge_service.ChallengeRepository(db_session)
    challenge_id = request.args.get('id')
    get_all = request.args.get('all')

    if challenge_id and challenge_id.isdigit():
        challenge = challenge_repo.get_by_id(int(challenge_id))
    elif get_all and get_all.lower() == 'true':
        challenges = challenge_repo.get_all()
        if not challenges:
            return jsonify({"success": False, "error": "No challenges found"}), 404
        # Convert challenges to a list of dictionaries

        return jsonify([{
            "id": challenge.id,
            "segment_id": challenge.segment_id,
            "start_date": challenge.start_date,
            "end_date": challenge.end_date,
        } for challenge in challenges]), 200
    else:
        challenge = challenge_repo.get_current()

    if not challenge:
        return jsonify({"success": False, "error": "Challenge not found"}), 404

    return jsonify({
        "id": challenge.id,
        "segment_id": challenge.segment_id,
        "start_date": challenge.start_date,
        "end_date": challenge.end_date,
    }), 200
