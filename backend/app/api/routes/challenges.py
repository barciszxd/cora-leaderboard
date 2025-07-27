import app.services.athlete as athlete_service
import app.services.challenge as challenge_service
import app.services.effort as effort_service
import app.services.segment as segment_service

from app.api.routes import api_bp
from app.database import db_session
from config import config
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
        climb_segment_dict, sprint_segment_dict = get_segments_for_challenge(challenge, segment_repo)

        challenge_dict = {
            "id"            : challenge.id,
            "name"          : challenge.name,
            "start_date"    : challenge.start_date.isoformat(),
            "end_date"      : challenge.end_date.isoformat(),
            "climb_segment" : climb_segment_dict,
            "sprint_segment": sprint_segment_dict
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

    response = {
        "id"            : challenge.id,
        "name"          : challenge.name,
        "start_date"    : challenge.start_date.isoformat(),
        "end_date"      : challenge.end_date.isoformat(),
        "climb_segment" : climb_segment_dict,
        "sprint_segment": sprint_segment_dict
    }

    return jsonify(response), 200


@api_bp.route('/challenges/<int:challenge_id>/results', methods=['GET'])
def get_challenge_results(challenge_id):
    """Get results for a specific challenge"""
    # TODO: refactor this spaghetti code
    challenge_repo = challenge_service.ChallengeRepository(db_session)

    if not (challenge := challenge_repo.get_by_id(challenge_id)):
        return jsonify({"success": False, "error": "Challenge not found"}), 404

    segment_type = request.args.get('segment_type')
    gender = request.args.get('gender')

    if segment_type not in ['climb', 'sprint', None]:
        return jsonify({"success": False, "error": "Invalid segment type"}), 400

    segment_ids = {
        "climb": challenge.climb_segment_id,
        "sprint": challenge.sprint_segment_id
    }

    efforts_repo = effort_service.EffortRepository(db_session)

    if segment_type is not None:
        efforts = efforts_repo.get_efforts_by_segment_id_and_date(
            segment_id = segment_ids[segment_type],
            start_date = challenge.start_date,
            end_date   = challenge.end_date
        )
    else:
        efforts: list[effort_service.Effort] = []
        for segment_id in segment_ids.values():
            efforts += efforts_repo.get_efforts_by_segment_id_and_date(
                segment_id = segment_id,
                start_date = challenge.start_date,
                end_date   = challenge.end_date
            )

    if not efforts:
        return jsonify([]), 204

    results = []
    positions = {
        "M" : {"climb": 0, "sprint": 0},
        "F" : {"climb": 0, "sprint": 0}
    }
    athlete_repo = athlete_service.AthleteRepository(db_session)

    for effort in efforts:
        athlete = athlete_repo.get_by_id(effort.athlete_id)
        if not athlete:
            continue
        if gender and athlete.sex != gender:
            continue

        # Check if the athlete already has a better time for this segment
        # If so, skip this effort
        existing_result = next((result for result in results if result["athlete_id"] == effort.athlete_id and result["segment_id"] == effort.segment_id), None)

        if existing_result and existing_result["time"] < effort.elapsed_time:
            continue

        is_climb_effort = effort.segment_id == challenge.climb_segment_id

        result = {
            "id"            : effort.id,
            "athlete_id"    : effort.athlete_id,
            "athlete_name"  : f"{athlete.firstname} {athlete.lastname}",
            "challenge_id"  : challenge.id,
            "segment_id"    : effort.segment_id,
            "segment_type"  : "climb" if is_climb_effort else "sprint",
            "time"          : effort.elapsed_time,
            "recorded_at"   : effort.start_date.isoformat()
        }
        if is_climb_effort:
            positions[athlete.sex]["climb"] += 1
            p = positions[athlete.sex]["climb"]
            result["points"] = config.POINTS[p - 1] if p - 1 < len(config.POINTS) else 0
            result["position"] = p
        else:
            positions[athlete.sex]["sprint"] += 1
            p = positions[athlete.sex]["sprint"]
            result["points"] = config.POINTS[p - 1] if p - 1 < len(config.POINTS) else 0
            result["position"] = p

        results.append(result)

    # Fetch results for the challenge

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
