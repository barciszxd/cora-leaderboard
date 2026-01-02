"""This route handles individual challenges and their results."""
from datetime import datetime, timezone

import app.services.challenge as challenge_service
import app.services.segment as segment_service

from app.api.routes import api_bp
from app.helpers import Gender, TimeSpan
from app.services.results import ResultService
from flask import jsonify, request


@api_bp.post('/challenges')
def create_challenge():
    """Create a new challenge"""
    data = request.json

    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    challenge_repo = challenge_service.ChallengeRepository()

    if challenge_repo.add(data) is None:
        return jsonify({"success": False, "error": "Failed to create challenge"}), 400

    return jsonify({"success": True, "message": "Challenge created successfully."}), 201


@api_bp.get('/challenges')
def get_challenges():
    """Get all challenges"""
    challenge_repo = challenge_service.ChallengeRepository()

    challenges = challenge_repo.get_all()

    if not challenges:
        return jsonify({"success": False, "error": "No challenges found"}), 404
    # Convert challenges to a list of dictionaries

    segment_repo = segment_service.SegmentRepository()

    response = []

    for challenge in challenges:
        now = datetime.now(timezone.utc)
        time_span = TimeSpan(challenge.start_date, challenge.end_date)  # type: ignore

        segments = segment_repo.get_for_challenge(challenge)

        segment_dicts = []

        for segment, segment_type in zip(segments, ['sprint', 'climb']):
            segment_dict = segment_service.SegmentRepository.to_dict(segment) if segment else {}
            segment_dict["type"] = segment_type
            segment_dicts.append(segment_dict)

        challenge_dict = {
            "id"            : challenge.id,
            "name"          : challenge.name,
            "start_date"    : challenge.start_date.isoformat(),
            "end_date"      : challenge.end_date.isoformat(),
            "sprint_segment": segment_dicts[0],
            "climb_segment" : segment_dicts[1],
            "status"        : "upcoming" if now < time_span else "completed" if now > time_span else "active"
        }

        response.append(challenge_dict)

    return jsonify(response), 200


@api_bp.get('/challenges/<int:challenge_id>')
def get_challenge_by_id(challenge_id):
    """Get a challenge by ID"""
    challenge_repo = challenge_service.ChallengeRepository()
    challenge = challenge_repo.get_by_id(challenge_id)

    if not challenge:
        return jsonify({"success": False, "error": "Challenge not found"}), 404

    segments = segment_service.SegmentRepository().get_for_challenge(challenge)

    segment_dicts = []

    for segment, segment_type in zip(segments, ['sprint', 'climb']):
        segment_dict = segment_service.SegmentRepository.to_dict(segment) if segment else {}
        segment_dict["type"] = segment_type
        segment_dicts.append(segment_dict)

    now = datetime.now(timezone.utc)
    time_span = TimeSpan(challenge.start_date, challenge.end_date)  # type: ignore

    response = {
        "id"            : challenge.id,
        "name"          : challenge.name,
        "start_date"    : challenge.start_date.isoformat(),
        "end_date"      : challenge.end_date.isoformat(),
        "sprint_segment": segment_dicts[0],
        "climb_segment" : segment_dicts[1],
        "status"        : "upcoming" if now < time_span else "completed" if now > time_span else "active"
    }

    return jsonify(response), 200


@api_bp.get('/challenges/<int:challenge_id>/results')
def get_challenge_results(challenge_id):
    """Get results for a specific challenge"""

    segment_type = request.args.get('segment_type')
    gender = request.args.get('gender')

    if segment_type and segment_type not in ['climb', 'sprint']:
        return jsonify({"success": False, "error": "Invalid or no segment type"}), 400

    if gender and gender not in Gender.values():
        return jsonify({"success": False, "error": "Invalid or no gender"}), 400

    try:
        result_service = ResultService(challenge_id)
        result_service.query_from_db()
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404

    segment_types = [segment_type] if segment_type else ['climb', 'sprint']
    genders = [gender] if gender else Gender.values()

    results = []
    for segment_type in segment_types:
        for gender in genders:
            results.extend(result_service.yield_results(segment_type, Gender(gender)))

    return jsonify(results), 200
