import app.services.athlete as athlete_service
import app.services.effort as effort_service

from app.api.routes import api_bp
from app.database import db_session
from config import config
from flask import jsonify, request


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
