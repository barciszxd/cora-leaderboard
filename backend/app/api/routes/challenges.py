from datetime import datetime, timezone

import app.services.challenge as challenge_service
import app.services.segment as segment_service

from app.api.routes import api_bp
from app.database import db_session
from app.helpers import Gender, TimeSpan
from app.services.results import ResultService
from flask import jsonify, request


@api_bp.route('/challenges', methods=['POST'])
def create_challenge():
    """Create a new challenge"""
    data = request.json

    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    challenge_repo = challenge_service.ChallengeRepository(db_session)
    challenge_repo.add(
        name              = data.get('name'),
        climb_segment_id  = data.get('climb_segment_id'),
        sprint_segment_id = data.get('sprint_segment_id'),
        start_date        = data.get('start_date'),
        end_date          = data.get('end_date'))

    db_session.commit()

    return jsonify({"success": True, "message": "Challenge created successfully."}), 201


@api_bp.route('/challenges', methods=['GET'])
def get_challenges():
    """Get all challenges"""
    challenge_repo = challenge_service.ChallengeRepository(db_session)

    challenges = challenge_repo.get_all()

    if not challenges:
        return jsonify({"success": False, "error": "No challenges found"}), 404
    # Convert challenges to a list of dictionaries

    segment_repo = segment_service.SegmentRepository(db_session)

    response = []

    for challenge in challenges:
        now = datetime.now(timezone.utc)
        time_span = TimeSpan(challenge.start_date, challenge.end_date)
        climb_segment_dict, sprint_segment_dict = get_segments_for_challenge(challenge, segment_repo)

        challenge_dict = {
            "id"            : challenge.id,
            "name"          : challenge.name,
            "start_date"    : challenge.start_date.isoformat(),
            "end_date"      : challenge.end_date.isoformat(),
            "climb_segment" : climb_segment_dict,
            "sprint_segment": sprint_segment_dict,
            "status"        : "upcoming" if now < time_span else "completed" if now > time_span else "active"
        }

        response.append(challenge_dict)

    return jsonify(response), 200


@api_bp.route('/challenges/<int:challenge_id>', methods=['GET'])
def get_challenge_by_id(challenge_id):
    """Get a challenge by ID"""
    challenge_repo = challenge_service.ChallengeRepository(db_session)
    challenge = challenge_repo.get_by_id(challenge_id)

    if not challenge:
        return jsonify({"success": False, "error": "Challenge not found"}), 404

    segment_repo = segment_service.SegmentRepository(db_session)

    climb_segment_dict, sprint_segment_dict = get_segments_for_challenge(challenge, segment_repo)

    now = datetime.now(timezone.utc)
    time_span = TimeSpan(challenge.start_date, challenge.end_date)

    response = {
        "id"            : challenge.id,
        "name"          : challenge.name,
        "start_date"    : challenge.start_date.isoformat(),
        "end_date"      : challenge.end_date.isoformat(),
        "climb_segment" : climb_segment_dict,
        "sprint_segment": sprint_segment_dict,
        "status"        : "upcoming" if now < time_span else "completed" if now > time_span else "active"
    }

    return jsonify(response), 200


@api_bp.route('/challenges/<int:challenge_id>/results', methods=['GET'])
def get_challenge_results(challenge_id):
    """Get results for a specific challenge"""

    segment_type = request.args.get('segment_type')
    gender = request.args.get('gender')

    if segment_type and segment_type not in ['climb', 'sprint']:
        return jsonify({"success": False, "error": "Invalid or no segment type"}), 400

    if gender and gender not in Gender.values():
        return jsonify({"success": False, "error": "Invalid or no gender"}), 400

    try:
        result_service = ResultService()
        result_service.query_from_db(challenge_id, db_session)
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404

    segment_types = [segment_type] if segment_type else ['climb', 'sprint']
    genders = [gender] if gender else Gender.values()

    results = []
    for segment_type in segment_types:
        for gender in genders:
            results.extend(result_service.yield_results(segment_type, Gender(gender)))

    return jsonify(results), 200


def get_segments_for_challenge(
        challenge: challenge_service.Challenge,
        segment_repo: segment_service.SegmentRepository) -> tuple[dict | None, dict | None]:
    """Get segment details for a challenge."""
    climb_segment = segment_repo.get_by_id(challenge.climb_segment_id)
    climb_segment_dict = {
        "id": climb_segment.id,
        "name": climb_segment.name,
        "type": "climb",
        "distance": climb_segment.distance,
        "elevation_gain": climb_segment.elevation_gain
    } if climb_segment else None

    sprint_segment = segment_repo.get_by_id(challenge.sprint_segment_id)
    sprint_segment_dict = {
        "id": sprint_segment.id,
        "name": sprint_segment.name,
        "type": "sprint",
        "distance": sprint_segment.distance,
        "elevation_gain": sprint_segment.elevation_gain
    } if sprint_segment else None

    return climb_segment_dict, sprint_segment_dict
