"""API routes"""
import app.services.athlete as athlete_service
import app.services.challenge as challenge_service
import app.services.effort as effort_service
import requests

from app.database import db_session
from config import config
from flask import Blueprint, jsonify, request

api_bp = Blueprint('api', __name__)


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "Flask API is running successfully"
    })


@api_bp.route('/hello', methods=['GET'])
def hello_world():
    """Simple GET endpoint that returns a JSON response"""
    return jsonify({
        "response": "Hello world"
    })


@api_bp.route('/exchange_token', methods=['GET'])
def exchange_token():
    """Handle Strava OAuth authorization callback"""

    # Get query parameters
    code  = request.args.get('code')
    scope = request.args.get('scope')
    error = request.args.get('error')

    if error:
        return jsonify({"success": False, "error": error}), 400

    scopes = scope.split(',') if scope else []

    if "activity:read" not in scopes:
        return jsonify({"success": False, "error": "Missing read access for activities"}), 403

    token_url = "https://www.strava.com/oauth/token"
    token_data = {
        'client_id': config.CLIENT_ID,
        'client_secret': config.CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code'
    }

    try:
        response = requests.post(
            url     = token_url,
            data    = token_data,
            timeout = 100,
            verify  = config.SSL_ENABLE
        )
        response.raise_for_status()  # Raises an HTTPError for bad responses
        token_data = response.json()

    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "error": f"Failed to exchange token: {str(e)}"}), 500

    athlete_data = token_data.get('athlete', {})

    athlete_repo = athlete_service.AthleteRepository(db_session)

    msg = f"Exchanged token for athlete {athlete_data.get('id', 'unknown')}"

    if existing_athlete := athlete_repo.get_by_id(athlete_data.get('id')):
        # Update existing athlete
        athlete_repo.update(
            athlete      = existing_athlete,
            athlete_data = athlete_data,
            token_data   = token_data
        )
        msg += " (athlete exists, updated)"

    else:
        # Create new athlete
        athlete_repo.create(
            athlete_data = athlete_data,
            token_data   = token_data
        )
        msg += " (new athlete created)"

    db_session.commit()

    return jsonify({
        "success": True,
        "message": msg,
    }), 200


@api_bp.route('/webhook', methods=['GET'])
def subscription_callback():
    """Handle Strava subscription callback"""

    # Get query parameters
    challenge = request.args.get('hub.challenge')
    verify_token = request.args.get('hub.verify_token')

    if verify_token == config.STRAVA_VERIFY_TOKEN:
        return jsonify({"success": True, "hub.challenge": challenge}), 200

    return jsonify({"success": False, "error": "Bad request"}), 403


@api_bp.route('/webhook', methods=['POST'])
def webhook():
    """Handle Strava webhook events"""
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "error": "No data received"}), 400

    print(f"Received webhook data: {data}")

    object_type = data.get('object_type')
    aspect_type = data.get('aspect_type')
    athlete_id = data.get('owner_id')

    # handle activity-related events
    if object_type == 'activity':
        activity_id = data.get('object_id')
        effort_repo = effort_service.EffortRepository(db_session)

        if aspect_type == 'create':
            effort_added = effort_repo.add(activity_id, athlete_id)
            db_session.commit()

            msg = f"New activity {activity_id} of athlete {athlete_id} registered. "

            if effort_added:
                msg += "Segment effort added to the database."
                status_code = 201
            else:
                msg += "No segment effort was added."
                status_code = 200

            return jsonify({"success": True, "message": msg}), status_code

        if aspect_type == 'update':
            updates = data.get('updates', {})
            private = updates.get('private', False)

            if private and private == "true":
                efforts_deleted = effort_repo.delete_efforts_by_activity_id(activity_id)
                db_session.commit()

                msg = f"Setting activity {activity_id} to private registered. "

                if efforts_deleted:
                    msg += "All related efforts were deleted."
                    status_code = 200
                else:
                    msg += "No efforts to delete from leaderboard."
                    status_code = 200

                return jsonify({"success": True, "message": msg}), status_code

            if private and private == "false":
                effort_added = effort_repo.add(activity_id, athlete_id)
                db_session.commit()

                msg = f"Setting activity {activity_id} to public registered. "

                if effort_added:
                    msg += "Segment effort added to the database."
                    status_code = 201
                else:
                    msg += "No segment effort was added."
                    status_code = 200

                return jsonify({"success": True, "message": msg}), status_code

        if aspect_type == 'delete':
            efforts_deleted = effort_repo.delete_efforts_by_activity_id(activity_id)
            db_session.commit()

            msg = f"Deleted activity {activity_id}. "

            if efforts_deleted:
                msg += "All related efforts were deleted."
                status_code = 200
            else:
                msg += "No efforts to delete from leaderboard."
                status_code = 200

            return jsonify({"success": True, "message": msg}), status_code

        return jsonify({"success": False, "error": "Unsupported aspect type for activity"}), 400

    # handle athlete-related events
    if object_type == 'athlete':
        if aspect_type == 'update':
            effort_repo = effort_service.EffortRepository(db_session)
            athlete_repo = athlete_service.AthleteRepository(db_session)
            updates = data.get('updates', {})

            if (authorized := updates.get('authorized', False)) and authorized == "false":
                athlete_deleted = athlete_repo.delete_by_id(athlete_id)
                efforts_deleted = effort_repo.delete_efforts_by_athlete_id(athlete_id)
                db_session.commit()
                msg = f"Athlete {athlete_id} deauthorized the application. "

                if athlete_deleted:
                    msg += "Athlete record deleted. "
                else:
                    msg += "No athlete record to delete. "

                if efforts_deleted:
                    msg += "All related efforts deleted."
                else:
                    msg += "No efforts to delete from leaderboard."

                return jsonify({"success": True, "message": msg}), 200

        return jsonify({"success": False, "error": "Unsupported aspect type for athlete"}), 400

    return jsonify({"success": False, "error": "Unsupported object type"}), 400


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
