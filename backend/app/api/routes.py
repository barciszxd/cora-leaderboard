"""API routes"""
import app.services.athlete as athlete_service
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

    message = "Webhook event received"
    object_type = data.get('object_type')
    aspect_type = data.get('aspect_type')
    athlete_id = data.get('owner_id')

    # handle activity-related events
    if object_type == 'activity':
        activity_id = data.get('object_id')

        if aspect_type == 'create':
            # TODO: Handle new activity creation
            message = f"New activity created with ID {activity_id} for athlete {athlete_id}"

        elif aspect_type == 'update':
            updates = data.get('updates', {})
            private = updates.get('private', False)

            if private and private == "true":
                # TODO: Handle activity set to private
                message = f"Activity {activity_id} of athlete {athlete_id} deleted from the leaderboard"

            elif private and private == "false":
                # TODO: Handle activity set to public
                message = f"Activity {activity_id} of athlete {athlete_id} added to the leaderboard"

        elif aspect_type == 'delete':
            message = f"Activity {activity_id} of athlete {athlete_id} deleted from the leaderboard"

    # handle athlete-related events
    elif object_type == 'athlete':
        if aspect_type == 'update':
            updates = data.get('updates', {})

            if (authorized := updates.get('authorized', False)) and authorized == "false":
                # TODO: Handle athlete deauthorization
                message = f"Athlete {athlete_id} deauthorized the application"

    return jsonify({"success": True, "message": message}), 200
