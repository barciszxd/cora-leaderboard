"""Module for handling Strava OAuth token exchange"""
import logging

import requests

from app.api.routes import api_bp
from app.services import athlete as athlete_service
from config import config
from flask import jsonify, request

logger = logging.getLogger(__name__)


@api_bp.get('/exchange_token')
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

    response = requests.post(
        url     = token_url,
        data    = token_data,
        timeout = 100,
        verify  = config.SSL_ENABLE
    )
    if not response.ok:
        return jsonify({"success": False, "error": "Could not exchange token: STRAVA didn't respond"}), 500

    token_data = response.json()

    athlete_data = token_data.get('athlete', {})
    athlete_repo = athlete_service.AthleteRepository()

    msg = f"Exchanged token for athlete {athlete_data.get('id', 'unknown')}"

    if existing_athlete := athlete_repo.get_by_id(athlete_data.get('id')):
        # Update existing athlete
        athlete_repo.update(
            athlete      = existing_athlete,
            athlete_data = athlete_data,
            token_data   = token_data
        )
        msg += " (athlete exists, updated)"
        created = False

    else:
        # Create new athlete
        athlete_repo.create(
            athlete_data = athlete_data,
            token_data   = token_data
        )
        msg += " (new athlete created)"
        created = True

    return jsonify({
        "success": True,
        "message": msg,
        "athlete_created": created,  # True if a new athlete was created, False if updated
        "athlete": athlete_data
    }), 200
