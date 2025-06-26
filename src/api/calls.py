from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime, timedelta
import os

from src import db
from src.models.user import User, UserRole
from src.models.patient import Patient
from src.models.call import Call, CallStatus
from src.schemas.call import (
    CallSchema,
    CallListSchema,
    CallUpdateSchema,
    CallTranscriptSchema,
)
from src.utils.decorators import roles_required, audit_action
from src.models.audit_log import AuditLog
from src.core.rag_service import generate_call_script
from src.core.call_service import make_retell_call

calls_bp = Blueprint("calls", __name__)


@calls_bp.route("/", methods=["GET"])
@jwt_required()
def get_all_calls():
    """Get all calls with optional filtering"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # Get query parameters
    patient_id = request.args.get("patient_id", type=int)
    status = request.args.get("status")
    call_type = request.args.get("call_type")
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")

    # Start with base query
    query = Call.query

    # Apply filters
    if patient_id:
        query = query.filter(Call.patient_id == patient_id)

        # Check access to patient for nurses
        if current_user.role == UserRole.NURSE:
            patient = Patient.query.get(patient_id)
            if not patient or patient.primary_nurse_id != current_user_id:
                return (
                    jsonify({"error": "Unauthorized to view this patient's calls"}),
                    403,
                )
    elif current_user.role == UserRole.NURSE:
        # Nurses can only see calls for their patients
        query = query.join(Patient).filter(Patient.primary_nurse_id == current_user_id)

    if status:
        try:
            status_enum = CallStatus(status)
            query = query.filter(Call.status == status_enum)
        except ValueError:
            return jsonify({"error": f"Invalid call status: {status}"}), 400

    if call_type:
        query = query.filter(Call.call_type == call_type)

    if from_date:
        try:
            from_date_obj = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
            query = query.filter(Call.scheduled_time >= from_date_obj)
        except ValueError:
            return jsonify({"error": f"Invalid from_date format: {from_date}"}), 400

    if to_date:
        try:
            to_date_obj = datetime.fromisoformat(to_date.replace("Z", "+00:00"))
            query = query.filter(Call.scheduled_time <= to_date_obj)
        except ValueError:
            return jsonify({"error": f"Invalid to_date format: {to_date}"}), 400

    # Order by scheduled_time
    calls = query.order_by(Call.scheduled_time.desc()).all()

    return jsonify(CallListSchema(many=True).dump(calls)), 200


@calls_bp.route("/<int:id>", methods=["GET"])
@jwt_required()
def get_call(id):
    """Get a call by ID"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    call = Call.query.get(id)
    if not call:
        return jsonify({"error": "Call not found"}), 404

    # Regular nurses can only view calls for their patients
    if current_user.role == UserRole.NURSE:
        patient = Patient.query.get(call.patient_id)
        if not patient or patient.primary_nurse_id != current_user_id:
            return jsonify({"error": "Unauthorized to view this call"}), 403

    # Log the access
    AuditLog.log(
        user_id=current_user_id,
        action="view",
        resource_type="call",
        resource_id=id,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
    )

    return jsonify(CallSchema().dump(call)), 200


@calls_bp.route("/", methods=["POST"])
@jwt_required()
@roles_required(UserRole.NURSE, UserRole.PHYSICIAN)
@audit_action("create", "call")
def schedule_call():
    """Schedule a new call"""
    data = request.get_json()
    current_user_id = get_jwt_identity()

    try:
        # Add conducted_by_id if not provided
        if "conducted_by_id" not in data:
            data["conducted_by_id"] = current_user_id

        # Validate input
        call_data = CallSchema().load(data)
    except ValidationError as err:
        return jsonify({"error": "Validation error", "messages": err.messages}), 400

    # Get patient and check access for nurses
    patient = Patient.query.get(call_data["patient_id"])
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    current_user = User.query.get(current_user_id)
    if (
        current_user.role == UserRole.NURSE
        and patient.primary_nurse_id != current_user_id
    ):
        return jsonify({"error": "Unauthorized to schedule call for this patient"}), 403

    # Create new call
    call = Call(
        patient_id=call_data["patient_id"],
        conducted_by_id=call_data["conducted_by_id"],
        scheduled_time=call_data["scheduled_time"],
        status=CallStatus.SCHEDULED,
        call_type=call_data["call_type"],
        notes=call_data.get("notes"),
    )

    db.session.add(call)
    db.session.commit()

    return jsonify(CallSchema().dump(call)), 201


@calls_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
@roles_required(UserRole.NURSE, UserRole.PHYSICIAN)
@audit_action("update", "call")
def update_call(id):
    """Update a call"""
    data = request.get_json()
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    call = Call.query.get(id)
    if not call:
        return jsonify({"error": "Call not found"}), 404

    # Regular nurses can only update calls for their patients
    if current_user.role == UserRole.NURSE:
        patient = Patient.query.get(call.patient_id)
        if not patient or patient.primary_nurse_id != current_user_id:
            return jsonify({"error": "Unauthorized to update this call"}), 403

    try:
        # Validate input
        call_data = CallUpdateSchema().load(data)
    except ValidationError as err:
        return jsonify({"error": "Validation error", "messages": err.messages}), 400

    # Update call fields
    if "conducted_by_id" in call_data:
        call.conducted_by_id = call_data["conducted_by_id"]
    if "scheduled_time" in call_data:
        call.scheduled_time = call_data["scheduled_time"]
    if "status" in call_data:
        previous_status = call.status
        new_status = CallStatus(call_data["status"])
        call.status = new_status

        # Update timestamps based on status change
        if previous_status != new_status:
            if new_status == CallStatus.IN_PROGRESS and not call.start_time:
                call.start_time = datetime.utcnow()
            elif new_status == CallStatus.COMPLETED and not call.end_time:
                call.end_time = datetime.utcnow()
                if call.start_time:
                    call.duration = (call.end_time - call.start_time).total_seconds()
    if "notes" in call_data:
        call.notes = call_data["notes"]

    db.session.commit()

    return jsonify(CallSchema().dump(call)), 200


@calls_bp.route("/<int:id>/cancel", methods=["PUT"])
@jwt_required()
@roles_required(UserRole.NURSE, UserRole.PHYSICIAN)
@audit_action("cancel", "call")
def cancel_call(id):
    """Cancel a scheduled call"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    call = Call.query.get(id)
    if not call:
        return jsonify({"error": "Call not found"}), 404

    # Regular nurses can only cancel calls for their patients
    if current_user.role == UserRole.NURSE:
        patient = Patient.query.get(call.patient_id)
        if not patient or patient.primary_nurse_id != current_user_id:
            return jsonify({"error": "Unauthorized to cancel this call"}), 403

    # Can only cancel scheduled calls
    if call.status != CallStatus.SCHEDULED:
        return (
            jsonify({"error": f"Cannot cancel call with status {call.status.value}"}),
            400,
        )

    call.status = CallStatus.CANCELLED
    db.session.commit()

    return jsonify({"message": f"Call for {call.patient.full_name} cancelled"}), 200


@calls_bp.route("/<int:id>/initiate", methods=["POST"])
@jwt_required()
@roles_required(UserRole.NURSE, UserRole.PHYSICIAN)
def initiate_outbound_call(id):
    """Initiate an outbound call using Twilio"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    call = Call.query.get(id)
    if not call:
        return jsonify({"error": "Call not found"}), 404

    # Regular nurses can only initiate calls for their patients
    if current_user.role == UserRole.NURSE:
        patient = Patient.query.get(call.patient_id)
        if not patient or patient.primary_nurse_id != current_user_id:
            return (
                jsonify({"error": "Unauthorized to initiate call for this patient"}),
                403,
            )

    # Can only initiate scheduled calls
    if call.status != CallStatus.SCHEDULED:
        return (
            jsonify({"error": f"Cannot initiate call with status {call.status.value}"}),
            400,
        )

    # Get patient phone number
    patient = Patient.query.get(call.patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    try:
        # Generate call script if needed
        if call.call_type == "assessment":
            # Get the appropriate protocol for this patient
            from src.models.protocol import Protocol

            protocol = Protocol.get_latest_active_protocol(patient.protocol_type)
            if not protocol:
                return (
                    jsonify(
                        {
                            "error": f"No active protocol found for {patient.protocol_type.value}"
                        }
                    ),
                    400,
                )

            # Generate script using RAG service
            call_script = generate_call_script(patient, protocol, call.call_type)
        else:
            call_script = None

        # Initiate call through Twilio service
        result = initiate_call(
            to_number=patient.phone_number,
            from_number=current_app.config["TWILIO_PHONE_NUMBER"],
            call_id=call.id,
            call_type=call.call_type,
            call_script=call_script,
        )

        # Update call status and SID
        call.status = CallStatus.IN_PROGRESS
        call.start_time = datetime.utcnow()
        call.twilio_call_sid = result["call_sid"]
        db.session.commit()

        # Log the call initiation
        AuditLog.log(
            user_id=current_user_id,
            action="initiate_call",
            resource_type="call",
            resource_id=id,
            details={"call_sid": result["call_sid"]},
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string,
        )

        return (
            jsonify(
                {
                    "message": f"Call to {patient.full_name} initiated",
                    "call_sid": result["call_sid"],
                    "status": call.status.value,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error initiating call: {str(e)}")
        return jsonify({"error": f"Failed to initiate call: {str(e)}"}), 500


@calls_bp.route("/webhook/status", methods=["POST"])
def call_status_webhook():
    """Webhook for Twilio call status updates"""
    # Verify the request is from Twilio
    # In production, you should validate the request signature

    call_sid = request.form.get("CallSid")
    call_status = request.form.get("CallStatus")

    if not call_sid:
        return jsonify({"error": "Missing CallSid parameter"}), 400

    # Find the call by Twilio SID
    call = Call.query.filter_by(twilio_call_sid=call_sid).first()
    if not call:
        return jsonify({"error": "Call not found"}), 404

    # Update call status based on Twilio status
    if call_status == "in-progress":
        call.status = CallStatus.IN_PROGRESS
        if not call.start_time:
            call.start_time = datetime.utcnow()
    elif call_status == "completed":
        call.status = CallStatus.COMPLETED
        call.end_time = datetime.utcnow()
        if call.start_time:
            call.duration = (call.end_time - call.start_time).total_seconds()
    elif call_status == "busy" or call_status == "no-answer" or call_status == "failed":
        call.status = CallStatus.MISSED

    db.session.commit()

    # Log the status change
    AuditLog.log(
        user_id=None,  # System event
        action="call_status_update",
        resource_type="call",
        resource_id=call.id,
        details={"twilio_status": call_status, "call_sid": call_sid},
    )

    return "", 204


@calls_bp.route("/webhook/voice", methods=["POST"])
def voice_webhook():
    """Webhook for Twilio voice interactions"""
    # Get call parameters
    call_sid = request.form.get("CallSid")
    call_status = request.form.get("CallStatus")

    # Create TwiML response
    response = VoiceResponse()

    # Find call by SID if available
    call = None
    if call_sid:
        call = Call.query.filter_by(twilio_call_sid=call_sid).first()

    if call:
        # Generate TwiML for this specific call
        twiml = generate_call_twiml(call)
        return twiml, 200
    else:
        # Generic response for unknown calls
        response.say(
            "Hello, this is the palliative care coordination system. No active call was found for this number."
        )
        response.hangup()

    return str(response), 200


@calls_bp.route("/webhook/recording", methods=["POST"])
def recording_webhook():
    """Webhook for processing call recordings"""
    # Get recording parameters
    recording_sid = request.form.get("RecordingSid")
    recording_url = request.form.get("RecordingUrl")
    call_sid = request.form.get("CallSid")

    if not recording_sid or not recording_url or not call_sid:
        return jsonify({"error": "Missing required parameters"}), 400

    # Find the call by Twilio SID
    call = Call.query.filter_by(twilio_call_sid=call_sid).first()
    if not call:
        return jsonify({"error": "Call not found"}), 404

    try:
        # Process the recording (download, transcribe, etc.)
        result = process_call_recording(recording_sid, recording_url, call)

        # Update call with recording info
        call.recording_url = result.get("recording_url")
        call.transcript = result.get("transcript")
        db.session.commit()

        # Log the recording processing
        AuditLog.log(
            user_id=None,  # System event
            action="process_recording",
            resource_type="call",
            resource_id=call.id,
            details={"recording_sid": recording_sid},
        )

        return "", 204

    except Exception as e:
        current_app.logger.error(f"Error processing recording: {str(e)}")
        return jsonify({"error": f"Failed to process recording: {str(e)}"}), 500


@calls_bp.route("/<int:id>/transcript", methods=["POST"])
@jwt_required()
@roles_required(UserRole.NURSE, UserRole.PHYSICIAN)
@audit_action("update_transcript", "call")
def update_transcript(id):
    """Update call transcript manually"""
    data = request.get_json()
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    call = Call.query.get(id)
    if not call:
        return jsonify({"error": "Call not found"}), 404

    # Regular nurses can only update calls for their patients
    if current_user.role == UserRole.NURSE:
        patient = Patient.query.get(call.patient_id)
        if not patient or patient.primary_nurse_id != current_user_id:
            return jsonify({"error": "Unauthorized to update this call"}), 403

    try:
        # Validate input
        transcript_data = CallTranscriptSchema().load(data)
    except ValidationError as err:
        return jsonify({"error": "Validation error", "messages": err.messages}), 400

    # Update transcript
    call.transcript = transcript_data["transcript"]
    if "recording_url" in transcript_data:
        call.recording_url = transcript_data["recording_url"]

    db.session.commit()

    return jsonify({"message": "Transcript updated successfully"}), 200


@calls_bp.route("/today", methods=["GET"])
@jwt_required()
def get_today_calls():
    """Get calls scheduled for today"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # Get today's date range
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1) - timedelta(microseconds=1)

    # Build query for today's calls
    query = Call.query.filter(
        Call.scheduled_time >= today_start, Call.scheduled_time <= today_end
    )

    # Regular nurses can only see calls for their patients
    if current_user.role == UserRole.NURSE:
        query = query.join(Patient).filter(Patient.primary_nurse_id == current_user_id)

    # Order by scheduled time
    calls = query.order_by(Call.scheduled_time).all()

    return jsonify(CallListSchema(many=True).dump(calls)), 200


@calls_bp.route("/ring-now", methods=["POST"])
@jwt_required()
@roles_required(UserRole.ADMIN, UserRole.NURSE, UserRole.PHYSICIAN)
@audit_action("ring_now", "call")
def ring_now():
    """Initiate immediate call using Retell.ai"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    data = request.get_json()

    # Validate required fields
    if not data or not data.get("patient_id"):
        return jsonify({"error": "patient_id is required"}), 400

    patient_id = data.get("patient_id")
    patient = Patient.query.get(patient_id)

    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    # Check authorization - nurses can only call their own patients
    if (
        current_user.role == UserRole.NURSE
        and patient.primary_nurse_id != current_user_id
    ):
        return jsonify({"error": "Unauthorized to call this patient"}), 403

    # Validate phone number
    if not patient.phone_number:
        return (
            jsonify({"error": "Patient has no phone number on file", "success": False}),
            400,
        )

    try:
        # Prepare patient data for Retell.ai call
        patient_data = {
            "id": patient.id,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "phone_number": patient.phone_number,
            "email_address": patient.email,
        }

        # Initiate the call using Retell.ai
        call_id = make_retell_call(patient_data)

        if call_id:
            # Create a call record in the database
            call = Call(
                patient_id=patient_id,
                conducted_by_id=current_user_id,
                call_type="ring_now",
                status=CallStatus.IN_PROGRESS,
                scheduled_time=datetime.utcnow(),
                start_time=datetime.utcnow(),
                twilio_call_sid=call_id,
                notes=f"Ring Now call initiated by {current_user.full_name}",
            )

            db.session.add(call)
            db.session.commit()

            # Log the action
            current_app.logger.info(
                f"Ring Now call initiated for patient {patient.full_name} (ID: {patient_id}) by user {current_user.full_name} (ID: {current_user_id})"
            )

            return (
                jsonify(
                    {
                        "success": True,
                        "message": f"Call initiated successfully to {patient.full_name}",
                        "call_id": call.id,
                        "external_call_id": call_id,
                    }
                ),
                200,
            )
        else:
            return (
                jsonify({"success": False, "message": "Failed to initiate call"}),
                500,
            )

    except ValueError as e:
        current_app.logger.error(f"Ring Now call validation error: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 400

    except Exception as e:
        current_app.logger.error(f"Ring Now call error: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "message": "An error occurred while initiating the call",
                }
            ),
            500,
        )


@calls_bp.route("/call-setting", methods=["GET", "POST"])
@jwt_required()
@roles_required(UserRole.ADMIN, UserRole.NURSE, UserRole.PHYSICIAN)
def call_setting():
    """Get or update call mode setting (simulation vs real calls)"""

    if request.method == "GET":
        # Get current MAKE_REAL_CALL setting
        make_real_call_str = os.environ.get("MAKE_REAL_CALL", "false").lower()
        make_real_call = make_real_call_str in ("true", "t", "1", "yes")

        current_app.logger.info(
            f"Call setting GET request - current value: {make_real_call}"
        )

        return jsonify({"make_real_call": make_real_call}), 200

    elif request.method == "POST":
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        data = request.get_json()

        if not data or "make_real_call" not in data:
            return jsonify({"error": "make_real_call field is required"}), 400

        make_real_call = data.get("make_real_call", False)

        # Update environment variable
        env_value = "true" if make_real_call else "false"
        os.environ["MAKE_REAL_CALL"] = env_value

        # Log the action
        mode = "Real Call Mode" if make_real_call else "Simulation Mode"
        current_app.logger.info(
            f"Call mode updated to {mode} by user {current_user.full_name} (ID: {current_user_id})"
        )

        return (
            jsonify(
                {
                    "success": True,
                    "make_real_call": make_real_call,
                    "message": f"Call mode updated to {mode}",
                }
            ),
            200,
        )
