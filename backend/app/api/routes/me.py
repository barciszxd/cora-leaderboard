"""Protected /me endpoint — returns the currently authenticated athlete's data."""
import logging

from app.api.routes import api_bp
from app.auth import requires_auth
from flask import jsonify

logger = logging.getLogger(__name__)


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
