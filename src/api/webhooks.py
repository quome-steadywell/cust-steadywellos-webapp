"""Webhook endpoints for the palliative care application."""

import json
import logging
from flask import Blueprint, request, jsonify

from src.utils.logger import get_logger

# Create blueprint
webhook_bp = Blueprint("webhooks", __name__)
logger = logging.getLogger(__name__)
webhook_logger = logging.getLogger("webhook")


def log_webhook_payload(
    logger: logging.Logger,
    message: str,
    payload: dict,
    level: int = logging.INFO,
) -> None:
    """Log webhook payload data at the specified level.

    Args:
        logger: Logger to use
        message: Log message
        payload: Webhook payload to include in the log record
        level: Log level (default: INFO)
    """
    if logger.isEnabledFor(level):
        logger.log(level, f"{message}: {json.dumps(payload, indent=2)}")


def log_json_data(
    logger: logging.Logger,
    message: str,
    data: dict,
    level: int = logging.INFO,
) -> None:
    """Log message with associated JSON data at the specified level.

    Args:
        logger: Logger to use
        message: Log message
        data: JSON data to include in the log record
        level: Log level (default: INFO)
    """
    if logger.isEnabledFor(level):
        logger.log(level, f"{message}: {json.dumps(data, indent=2)}")


@webhook_bp.route("/webhook", methods=["POST"])
def handle_webhook():
    """Handle incoming webhooks from Retell.ai."""
    from src.core.patient_monitor import update_patient_status

    try:
        # Log request details
        logger.info("=" * 60)
        logger.info("WEBHOOK RECEIVED FROM RETELL.AI")
        logger.info(f"Request URL: {request.url}")
        logger.info(f"Request Method: {request.method}")
        logger.info(f"Request Headers: {dict(request.headers)}")
        logger.info("=" * 60)

        # Get the webhook data
        webhook_data = request.json

        # Log the complete webhook payload
        if webhook_data:
            logger.info("WEBHOOK PAYLOAD (Full JSON):")
            logger.info(json.dumps(webhook_data, indent=2))

            # Log key fields for quick debugging
            logger.info("KEY WEBHOOK FIELDS:")
            logger.info(f"  - call_id: {webhook_data.get('call_id', 'NOT FOUND')}")
            logger.info(f"  - call_status: {webhook_data.get('call_status', 'NOT FOUND')}")
            logger.info(f"  - to_number: {webhook_data.get('to_number', 'NOT FOUND')}")
            logger.info(f"  - from_number: {webhook_data.get('from_number', 'NOT FOUND')}")
            logger.info(f"  - metadata: {webhook_data.get('metadata', {})}")
            logger.info(f"  - recording_url: {webhook_data.get('recording_url', 'NOT FOUND')}")
            logger.info(f"  - public_log_url: {webhook_data.get('public_log_url', 'NOT FOUND')}")

            # Log call analysis if present
            if "call_analysis" in webhook_data:
                call_analysis = webhook_data.get("call_analysis", {})
                logger.info("CALL ANALYSIS DATA:")
                logger.info(f"  - call_successful: {call_analysis.get('call_successful', 'NOT FOUND')}")
                logger.info(f"  - user_sentiment: {call_analysis.get('user_sentiment', 'NOT FOUND')}")
                logger.info(f"  - in_voicemail: {call_analysis.get('in_voicemail', 'NOT FOUND')}")
                logger.info(f"  - custom_analysis_data: {call_analysis.get('custom_analysis_data', {})}")

            # Enhanced webhook logging
            log_webhook_payload(webhook_logger, "Received Retell.ai webhook payload", webhook_data)

            # For backward compatibility, also log as plain text at lower level
            webhook_logger.debug(json.dumps(webhook_data))
        else:
            logger.warning("WEBHOOK DATA IS EMPTY OR NULL")

        # Update patient status based on webhook data
        logger.info("Calling update_patient_status function...")
        result = update_patient_status(webhook_data)

        # Log the result
        logger.info("WEBHOOK PROCESSING RESULT:")
        logger.info(json.dumps(result, indent=2))
        log_json_data(logger, "Webhook processing result", result)

        logger.info("Webhook processing completed successfully")
        logger.info("=" * 60)

        return jsonify(
            {
                "status": "success",
                "message": "Webhook processed successfully",
                "result": result,
            }
        )

    except Exception as e:
        logger.error("=" * 60)
        logger.error("WEBHOOK PROCESSING ERROR")
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        logger.error("=" * 60)
        return (
            jsonify({"status": "error", "message": f"Failed to process webhook: {str(e)}"}),
            500,
        )


@webhook_bp.route("/palliative-care-callback", methods=["POST"])
def palliative_care_callback():
    """Alternative endpoint for Retell.ai callbacks."""
    return handle_webhook()
