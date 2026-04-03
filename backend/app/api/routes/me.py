"""Protected /me endpoint — returns or deletes the currently authenticated athlete's data."""
import logging

import requests as http_requests

import app.services.athlete as athlete_service
import app.services.effort as effort_service

from app.api.routes import api_bp
from app.auth import clear_auth_cookie, requires_auth
from app.services.utilities import decrypt_token
from config import config
from flask import jsonify, request

logger = logging.getLogger(__name__)


def _deauthorize_with_strava(access_token: str) -> None:
    """Call Strava's deauthorize endpoint to revoke the athlete's app access.

    Sends ``POST https://www.strava.com/oauth/deauthorize`` with the given
    bearer token.  Raises ``requests.HTTPError`` when Strava responds with a
    non-2xx status so that the caller can abort before touching the database.

    Args:
        access_token: The athlete's plaintext Strava access token.

    Raises:
        requests.HTTPError: When Strava returns a non-2xx response.
        requests.RequestException: On any network-level failure.
    """
    response = http_requests.post(
        url     = "https://www.strava.com/oauth/deauthorize",
        headers = {"Authorization": f"Bearer {access_token}"},
        timeout = 10,
        verify  = config.SSL_ENABLE,
    )
    response.raise_for_status()


@api_bp.get('/me')
@requires_auth
def get_me(athlete):
    """Return basic profile data for the authenticated athlete.

    Requires a valid ``auth_session`` cookie (set by ``/exchange_token``).

    Returns:
        JSON with ``id``, ``firstname``, ``lastname``, and ``sex`` fields.
    """
    return jsonify({
        "id":        athlete.id,
        "firstname": athlete.firstname,
        "lastname":  athlete.lastname,
        "sex":       athlete.sex,
    }), 200


@api_bp.delete('/me')
@requires_auth
def delete_me(athlete):
    """Permanently sign an athlete out of the leaderboard.

    Requires a valid ``auth_session`` cookie.

    Query parameters:
        hard (str, optional): When ``"true"``, the athlete's record and all
            their efforts are also deleted from the database (hard sign-out).
            Omitting the parameter or any other value performs a soft sign-out,
            which only revokes the stored credentials while preserving the
            athlete record and historical efforts.

    Behaviour:
        1. Retrieve the athlete's plaintext access token.
        2. Call Strava's ``POST /oauth/deauthorize`` endpoint. Abort and return
           503 if the call fails — this keeps our database consistent with
           Strava's authorisation state.
        3. **Soft** (default): Nullify ``access_token``, ``refresh_token``, and
           ``expires_at`` on the athlete record so they cannot authenticate again.
        4. **Hard** (``?hard=true``): Delete the athlete record and all their
           efforts from the database.
        5. Clear the ``auth_session`` cookie so the browser session ends.

    Returns:
        200 JSON on success, 503 JSON if the Strava API call fails.
    """
    athlete_id = athlete.id
    hard = request.args.get('hard', 'false').lower() == 'true'

    athlete_repo = athlete_service.AthleteRepository()

    # Retrieve the plaintext access token before we potentially delete the record
    access_token = decrypt_token(athlete.access_token)

    # Deauthorize with Strava first — abort if Strava rejects the request
    try:
        _deauthorize_with_strava(access_token)
    except http_requests.exceptions.RequestException as exc:
        logger.error("Failed to deauthorize athlete %d with Strava: %s", athlete_id, exc)
        return jsonify({
            "success": False,
            "error":   "Strava deauthorization failed. Please try again later.",
        }), 503

    logger.info("Athlete %d deauthorized with Strava (hard=%s)", athlete_id, hard)

    if hard:
        # Hard sign-out: delete the athlete record and all their efforts
        effort_repo   = effort_service.EffortRepository()

        deleted_efforts = effort_repo.delete_efforts_by_athlete_id(athlete_id)
        athlete_deleted = athlete_repo.delete_by_id(athlete_id)

        msg = "Hard sign-out completed. "
        msg += "Athlete record deleted. " if athlete_deleted else "No athlete record found. "
        msg += f"{deleted_efforts} effort(s) deleted." if deleted_efforts else "No efforts to delete."

    else:
        # Soft sign-out: wipe credentials, keep athlete record and efforts
        athlete_repo.revoke_tokens(athlete_id)
        msg = "Soft sign-out completed. Athlete credentials revoked; historical data retained."

    response = clear_auth_cookie(jsonify({"success": True, "message": msg}))
    return response, 200
