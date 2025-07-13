"""API routes"""
import requests

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
    code = request.args.get('code')
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
            url=token_url,
            data=token_data,
            timeout=100,
            verify=config.SSL_ENABLE
        )
        response.raise_for_status()  # Raises an HTTPError for bad responses
        token_response = response.json()
    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "error": f"Failed to exchange token: {str(e)}"}), 500

    # TODO: Store token_response in the database
    return jsonify({
        "success": True,
        "message": "Token exchanged successfully",
        "token_response": token_response
    }), 200
