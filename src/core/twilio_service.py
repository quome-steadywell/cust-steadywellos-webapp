"""Twilio service for telephony integration"""

import os
from typing import Dict, Any, Optional
from flask import current_app, url_for
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather

from src.models.call import Call, CallStatus
from src.models.patient import Patient
from src.models.protocol import Protocol
from src.core.rag_service import analyze_call_transcript


def get_twilio_client() -> Client:
    """Get initialized Twilio client"""
    account_sid = current_app.config.get("TWILIO_ACCOUNT_SID")
    auth_token = current_app.config.get("TWILIO_AUTH_TOKEN")

    if not account_sid or not auth_token:
        raise ValueError("Twilio credentials not configured")

    return Client(account_sid, auth_token)


def initiate_call(
    to_number: str,
    from_number: str,
    call_id: int,
    call_type: str,
    call_script: Optional[str] = None,
) -> Dict[str, Any]:
    """Initiate an outbound call using Twilio"""
    try:
        # Initialize Twilio client
        client = get_twilio_client()

        # Prepare webhook URLs
        status_callback = url_for("calls.call_status_webhook", _external=True)
        voice_url = url_for("calls.voice_webhook", _external=True, call_id=call_id, call_type=call_type)

        # Make the call
        call = client.calls.create(
            to=to_number,
            from_=from_number,
            url=voice_url,
            status_callback=status_callback,
            status_callback_event=["initiated", "ringing", "answered", "completed"],
            status_callback_method="POST",
            record=True,
        )

        return {"call_sid": call.sid, "status": call.status}

    except Exception as e:
        current_app.logger.error(f"Error initiating Twilio call: {str(e)}")
        raise


def generate_call_twiml(call: Call) -> str:
    """Generate TwiML for a specific call"""
    response = VoiceResponse()

    # Get patient info
    patient = Patient.query.get(call.patient_id)
    if not patient:
        response.say("Error: Patient information not found.")
        response.hangup()
        return str(response)

    # Different TwiML based on call type
    if call.call_type == "assessment":
        # Introduction
        response.say(
            f"Hello, this is the palliative care coordination service calling for {patient.first_name} {patient.last_name}. "
        )
        response.pause(length=1)

        # Verify identity
        try:
            action_url = url_for("calls.voice_webhook", _external=True, call_id=call.id, action="verify")
        except Exception as e:
            current_app.logger.warning(f"Could not build URL for voice webhook: {str(e)}")
            action_url = f"/api/v1/calls/voice?call_id={call.id}&action=verify"

        gather = Gather(num_digits=1, action=action_url, method="POST")
        gather.say(f"If you are {patient.first_name} {patient.last_name}, please press 1.")
        response.append(gather)

        # Timeout handling
        response.say("We didn't receive your response. We'll try again later.")
        response.hangup()

    elif call.call_type == "follow_up":
        # Follow-up call TwiML
        response.say(
            f"Hello, this is the palliative care coordination service calling to follow up with {patient.first_name} {patient.last_name}. "
        )
        response.pause(length=1)

        # Similar verification and questions...

    else:
        # Generic call
        response.say(
            f"Hello, this is the palliative care coordination service calling for {patient.first_name} {patient.last_name}. "
        )
        response.pause(length=1)
        response.say("A care coordinator will be with you shortly.")

    return str(response)


def process_call_recording(recording_sid: str, recording_url: str, call: Call) -> Dict[str, Any]:
    """Process a call recording - download, transcribe, and analyze"""
    try:
        client = get_twilio_client()

        # Get recording details
        recording = client.recordings(recording_sid).fetch()

        # Get transcription if available through Twilio
        transcriptions = client.recordings(recording_sid).transcriptions.list()
        transcript = None

        if transcriptions:
            # Use Twilio's transcription
            transcription = transcriptions[0]
            transcript = transcription.transcription_text
        else:
            # We could implement our own transcription service here
            # For now, just note that transcription is not available
            transcript = "[Transcription not available]"

        # If we have a transcript and a patient, analyze it
        result = {
            "recording_url": recording_url,
            "transcript": transcript,
            "duration": recording.duration,
            "analysis": None,
        }

        if transcript and transcript != "[Transcription not available]" and call.patient_id:
            # Get patient and protocol for analysis
            patient = Patient.query.get(call.patient_id)
            if patient and patient.protocol_type:
                protocol = Protocol.get_latest_active_protocol(patient.protocol_type)
                if protocol:
                    # Analyze the transcript
                    analysis = analyze_call_transcript(transcript, patient, protocol)
                    result["analysis"] = analysis

        return result

    except Exception as e:
        current_app.logger.error(f"Error processing call recording: {str(e)}")
        return {
            "recording_url": recording_url,
            "transcript": "[Error processing recording]",
            "error": str(e),
        }
