"""This route handles Strava webhook events and subscription callbacks."""
import logging

import app.services.athlete as athlete_service
import app.services.effort as effort_service

from app.api.routes import api_bp
from config import config
from flask import jsonify, request

logger = logging.getLogger(__name__)


@api_bp.get('/webhook')
def subscription_callback():
    """Handle Strava subscription callback"""

    # Get query parameters
    challenge = request.args.get('hub.challenge')
    verify_token = request.args.get('hub.verify_token')

    if verify_token == config.STRAVA_VERIFY_TOKEN:
        return jsonify({"success": True, "hub.challenge": challenge}), 200

    return jsonify({"success": False, "error": "Bad request"}), 403


@api_bp.post('/webhook')
def webhook():
    """Handle Strava webhook events"""
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "error": "No data received"}), 400

    logger.info("Received webhook data: %s", data)

    object_type = data.get('object_type')
    aspect_type = data.get('aspect_type')
    athlete_id = data.get('owner_id')

    # handle activity-related events
    if object_type == 'activity':
        activity_id = data.get('object_id')
        effort_repo = effort_service.EffortRepository()

        if aspect_type == 'create':
            effort_added = effort_repo.add(activity_id, athlete_id)

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
                deleted_efforts = effort_repo.delete_efforts_by_activity_id(activity_id)

                msg = f"Setting activity {activity_id} to private registered. "

                msg += f"{deleted_efforts} related efforts were deleted." if deleted_efforts else "No efforts to delete from leaderboard."

                return jsonify({"success": True, "message": msg}), 200

            if private and private == "false":
                effort_added = effort_repo.add(activity_id, athlete_id)

                msg = f"Setting activity {activity_id} to public registered. "

                if effort_added:
                    msg += "Segment effort added to the database."
                    status_code = 201
                else:
                    msg += "No segment effort was added."
                    status_code = 200

                return jsonify({"success": True, "message": msg}), status_code

        if aspect_type == 'delete':
            deleted_efforts = effort_repo.delete_efforts_by_activity_id(activity_id)

            msg = f"Deletion of activity {activity_id} registered."
            msg += f"{deleted_efforts} efforts deleted." if deleted_efforts else "No efforts to delete."

            return jsonify({"success": True, "message": msg}), 200

        return jsonify({"success": False, "error": "Unsupported aspect type for activity"}), 400

    # handle athlete-related events
    if object_type == 'athlete':
        if aspect_type == 'update':
            effort_repo = effort_service.EffortRepository()
            athlete_repo = athlete_service.AthleteRepository()
            updates = data.get('updates', {})

            # handles the event of athlete deathorizating the application
            if (authorized := updates.get('authorized', False)) and authorized == "false":
                athlete_deleted = athlete_repo.delete_by_id(athlete_id)
                deleted_efforts = effort_repo.delete_efforts_by_athlete_id(athlete_id)

                msg = f"Athlete {athlete_id} deauthorized the application. "
                msg += "Athlete record deleted. " if athlete_deleted else "No athlete record to delete. "
                msg += f"{deleted_efforts} his/her efforts deleted." if deleted_efforts else "No efforts to delete."

                return jsonify({"success": True, "message": msg}), 200

        return jsonify({"success": False, "error": "Unsupported aspect type for athlete"}), 400

    return jsonify({"success": False, "error": "Unsupported object type"}), 400
