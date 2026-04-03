"""Authentication module for cookie-based session management.

This module provides:

  - ``requires_auth`` – a route decorator that enforces authentication.
  - ``set_auth_cookie`` / ``clear_auth_cookie`` – helpers used by the login
    endpoint to attach or remove the session cookie from a response.

Session design
--------------
After a successful Strava OAuth exchange the backend writes an HTTP-only
``auth_session`` cookie that contains the *encrypted* athlete ID.  On every
protected request the decorator:

1. Reads the cookie and decrypts the athlete ID.
2. Loads the ``Athlete`` record from the database.
3. Calls ``AthleteRepository.get_access_token()``, which transparently
   refreshes the Strava access token when it has expired.
4. Passes the ``Athlete`` model instance as the **first positional argument**
   to the wrapped route function.

Usage example::

    from app.auth import requires_auth

    @api_bp.get('/me')
    @requires_auth
    def get_me(athlete):
        return jsonify({'id': athlete.id, 'firstname': athlete.firstname})
"""

import logging
from functools import wraps

import requests as http_requests
from cryptography.exceptions import InvalidTag
from flask import jsonify, request

from app.services.athlete import AthleteRepository
from app.services.utilities import decrypt_token, encrypt_token
from config import config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Cookie value helpers
# ---------------------------------------------------------------------------

def encrypt_athlete_id(athlete_id: int) -> str:
    """Encrypt an athlete ID for storage in the session cookie.

    Args:
        athlete_id: The integer Strava athlete ID to encrypt.

    Returns:
        Versioned base64 ciphertext produced by ``encrypt_token``.
    """
    return encrypt_token(str(athlete_id))


def decrypt_athlete_id(blob: str) -> int | None:
    """Decrypt the athlete ID from a session cookie value.

    Args:
        blob: The encrypted cookie value.

    Returns:
        The integer athlete ID, or ``None`` if decryption fails for any reason
        (tampered value, wrong key, malformed input, etc.).
    """
    try:
        return int(decrypt_token(blob))
    except (ValueError, KeyError, TypeError, InvalidTag):
        return None


# ---------------------------------------------------------------------------
# Cookie management helpers
# ---------------------------------------------------------------------------

def set_auth_cookie(response, athlete_id: int):
    """Attach the ``auth_session`` HTTP-only cookie to a Flask response.

    The cookie value is the AES-GCM–encrypted athlete ID so it cannot be
    forged or read by JavaScript.  Expiry and security flags are read from
    the active ``config`` object, which applies different values in
    development vs. production.

    Args:
        response: A Flask ``Response`` object to attach the cookie to.
        athlete_id: The athlete's Strava ID to store in the cookie.

    Returns:
        The same response object with the cookie set.
    """
    response.set_cookie(
        config.COOKIE_NAME,
        value    = encrypt_athlete_id(athlete_id),
        max_age  = config.COOKIE_MAX_AGE,
        httponly = config.COOKIE_HTTPONLY,
        secure   = config.COOKIE_SECURE,
        samesite = config.COOKIE_SAMESITE,
    )
    logger.debug("Auth cookie set for athlete %d", athlete_id)
    return response


def clear_auth_cookie(response):
    """Remove the ``auth_session`` cookie from the browser by zeroing its age.

    Args:
        response: A Flask ``Response`` object.

    Returns:
        The same response object with the cookie cleared.
    """
    response.set_cookie(
        config.COOKIE_NAME,
        value    = '',
        max_age  = 0,
        httponly = config.COOKIE_HTTPONLY,
        secure   = config.COOKIE_SECURE,
        samesite = config.COOKIE_SAMESITE,
    )
    return response


# ---------------------------------------------------------------------------
# Authentication decorator
# ---------------------------------------------------------------------------

def requires_auth(f):
    """Route decorator that enforces a valid ``auth_session`` cookie.

    The wrapped function receives the authenticated ``Athlete`` model instance
    as its **first positional argument**.  All other route arguments (e.g.
    URL path parameters) are forwarded unchanged.

    Returns HTTP 401 when:
    - The cookie is absent.
    - The cookie value cannot be decrypted (tampered / invalid).
    - No athlete with the decrypted ID exists in the database.
    - The Strava access token is expired *and* the silent refresh fails.

    Returns HTTP 503 when:
    - The Strava token-refresh API call raises a connection error.

    Usage::

        @api_bp.get('/me')
        @requires_auth
        def get_me(athlete):
            return jsonify({'id': athlete.id})
    """
    @wraps(f)
    def decorated(*args, **kwargs):

        # 1. Read cookie -------------------------------------------------
        encrypted = request.cookies.get(config.COOKIE_NAME)
        if not encrypted:
            logger.debug("Auth rejected: no cookie")
            return jsonify({"error": "Authentication required"}), 401

        # 2. Decrypt athlete ID -----------------------------------------
        athlete_id = decrypt_athlete_id(encrypted)
        if athlete_id is None:
            logger.warning("Auth rejected: invalid cookie value")
            return jsonify({"error": "Invalid session"}), 401

        # 3. Load athlete from database ----------------------------------
        repo    = AthleteRepository()
        athlete = repo.get_by_id(athlete_id)
        if athlete is None:
            logger.warning("Auth rejected: athlete %d not found in DB", athlete_id)
            return jsonify({"error": "Invalid session"}), 401

        # 4. Ensure we have a valid (possibly refreshed) access token ----
        try:
            access_token = repo.get_access_token(athlete_id)
        except http_requests.exceptions.RequestException as exc:
            logger.error("Auth: token refresh network error for athlete %d: %s", athlete_id, exc)
            return jsonify({"error": "Authentication service unavailable"}), 503

        if access_token is None:
            logger.warning("Auth rejected: could not obtain access token for athlete %d", athlete_id)
            return jsonify({"error": "Session expired, please log in again"}), 401

        # Re-load athlete so any token updates made by get_access_token are reflected
        athlete = repo.get_by_id(athlete_id)

        if athlete:
            logger.debug("Auth accepted for athlete %d (%s %s)", athlete_id, athlete.firstname, athlete.lastname)

        # 5. Inject athlete as first positional argument ----------------
        return f(athlete, *args, **kwargs)

    return decorated
