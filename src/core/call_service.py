"""Call service for making automated calls via Retell.ai API with knowledge base enhancement."""

import json
import os
import requests
import time
from typing import Dict, Any, Optional
from src.utils.logger import get_logger

logger = get_logger()


def make_knowledge_enhanced_call(patient_obj, protocol_obj) -> Optional[str]:
    """Make a knowledge-enhanced Retell AI call with patient and protocol objects."""
    try:
        from src.core.retell_integration import enhance_retell_call_config
        
        # Convert patient object to dictionary for compatibility
        patient_dict = {
            "id": patient_obj.id,
            "first_name": patient_obj.first_name,
            "last_name": patient_obj.last_name,
            "phone_number": patient_obj.phone_number,
            "email_address": patient_obj.email,
            "primary_diagnosis": patient_obj.primary_diagnosis,
            "protocol_type": patient_obj.protocol_type.value
        }
        
        # Get enhanced configuration
        enhanced_config = enhance_retell_call_config(patient_obj, protocol_obj)
        
        # Make the call with enhanced configuration
        logger.info(f"Making knowledge-enhanced call for {patient_obj.full_name}")
        
        # Use enhanced dynamic variables in the call
        return _make_enhanced_retell_call(patient_dict, enhanced_config)
        
    except Exception as e:
        logger.error(f"Error making knowledge-enhanced call: {e}")
        # Fallback to standard call
        return make_retell_call({
            "id": patient_obj.id,
            "first_name": patient_obj.first_name,
            "last_name": patient_obj.last_name,
            "phone_number": patient_obj.phone_number,
            "email_address": patient_obj.email or "",
        })


def _make_enhanced_retell_call(patient: Dict[str, Any], enhanced_config: Dict[str, Any]) -> Optional[str]:
    """Make Retell AI call with enhanced configuration."""
    logger.info("=== make_enhanced_retell_call called ===")
    
    # Check if we should make real calls
    make_real_call = os.environ.get("MAKE_REAL_CALL", "false").lower() in (
        "true", "t", "1", "yes",
    )
    
    if make_real_call:
        return _make_real_enhanced_call(patient, enhanced_config)
    else:
        logger.info(f"SIMULATION MODE: Enhanced call for {patient.get('first_name')} {patient.get('last_name')}")
        return _make_simulated_call(patient)


def _make_real_enhanced_call(patient: Dict[str, Any], enhanced_config: Dict[str, Any]) -> Optional[str]:
    """Make actual enhanced Retell AI call."""
    
    # Get basic configuration
    runtime_env = os.environ.get("RUNTIME_ENV", "")
    dev_state = os.environ.get("DEV_STATE", "TEST")
    
    if runtime_env == "local" or dev_state == "TEST":
        agent_id = os.environ.get("RETELLAI_LOCAL_AGENT_ID")
        webhook_url = os.environ.get("RETELLAI_LOCAL_WEBHOOK")
        mode = "LOCAL"
    else:
        agent_id = os.environ.get("RETELLAI_REMOTE_AGENT_ID")
        cloud_app_name = os.environ.get("CLOUD_APP_NAME", "")
        if cloud_app_name:
            base_url = cloud_app_name.rstrip("/")
            webhook_url = f"{base_url}/webhook"
        else:
            webhook_url = None
        mode = "REMOTE"
    
    api_key = os.environ.get("RETELLAI_API_KEY")
    from_number = os.environ.get("RETELLAI_PHONE_NUMBER")
    
    # Validate configuration
    if not all([api_key, agent_id, from_number, webhook_url]):
        raise ValueError("Missing required Retell AI configuration")
    
    # Extract patient information
    phone_number = patient.get("phone_number")
    first_name = patient.get("first_name", "Patient")
    last_name = patient.get("last_name", "")
    patient_id = patient.get("id")
    
    normalized_phone = _normalize_phone_number(phone_number)
    
    # Build enhanced call request
    call_request = {
        "agent_id": agent_id,
        "from_number": from_number,
        "to_number": normalized_phone,
        "webhook_url": webhook_url,
        "metadata": {
            "patient_name": f"{first_name} {last_name}".strip(),
            "patient_phone": normalized_phone,
            "patient_id": str(patient_id),
            "knowledge_enhanced": "true",
            "primary_diagnosis": patient.get("primary_diagnosis", ""),
            "protocol_type": patient.get("protocol_type", "")
        }
    }
    
    # Add enhanced dynamic variables from knowledge service
    if "retell_llm_dynamic_variables" in enhanced_config:
        call_request["retell_llm_dynamic_variables"] = enhanced_config["retell_llm_dynamic_variables"]
        logger.info("Added knowledge-enhanced dynamic variables to call")
    else:
        # Fallback to basic variables
        call_request["retell_llm_dynamic_variables"] = {
            "patient_name": first_name,
            "phone_number": normalized_phone,
            "primary_diagnosis": patient.get("primary_diagnosis", ""),
        }
    
    logger.info(f"Making enhanced Retell.ai call: {json.dumps(call_request, indent=2)}")
    
    try:
        response = requests.post(
            "https://api.retellai.com/v2/create-phone-call",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=call_request,
            timeout=30,
        )
        
        if response.status_code in [200, 201]:
            response_data = response.json()
            call_id = response_data.get("call_id")
            logger.info(f"Enhanced Retell.ai call created successfully. Call ID: {call_id}")
            return call_id
        else:
            error_msg = f"Enhanced Retell.ai API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to connect to Retell.ai API: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)


def make_retell_call(patient: Dict[str, Any]) -> Optional[str]:
    """Initiate a call to a patient using Retell.ai API.

    Args:
        patient: Dictionary containing patient information with keys:
            first_name: Patient's first name
            last_name: Patient's last name
            phone_number: Phone number to call
            email_address: (Optional) Patient email address
            id: Patient ID

    Returns:
        String containing the call ID if successful, None otherwise

    Raises:
        ValueError: If required configuration or patient data is missing
        RuntimeError: If call initiation fails
    """
    logger.info("=== make_retell_call called ===")
    logger.info(f"Patient data received: {json.dumps(patient, indent=2)}")

    # Check if we should make real calls
    make_real_call = os.environ.get("MAKE_REAL_CALL", "false").lower() in (
        "true",
        "t",
        "1",
        "yes",
    )
    logger.info(f"MAKE_REAL_CALL setting: {make_real_call}")

    # Extract patient information
    phone_number = patient.get("phone_number")
    first_name = patient.get("first_name", "Patient")
    last_name = patient.get("last_name", "")
    email = patient.get("email_address", "")
    patient_id = patient.get("id", "unknown")

    if not phone_number:
        raise ValueError("Patient phone number is missing")

    if make_real_call:
        logger.info(f"REAL CALL MODE: Initiating actual call to {first_name} {last_name} at {phone_number}")
        return _make_real_retell_call(patient)
    else:
        logger.info(f"SIMULATION MODE: Would initiate call to {first_name} {last_name} at {phone_number}")
        return _make_simulated_call(patient)


def _make_real_retell_call(patient: Dict[str, Any]) -> Optional[str]:
    """Make an actual call using Retell.ai API."""

    # Detect runtime environment
    runtime_env = os.environ.get("RUNTIME_ENV", "")
    dev_state = os.environ.get("DEV_STATE", "TEST")

    # Select appropriate configuration based on environment
    if runtime_env == "local" or dev_state == "TEST":
        # Local development mode
        agent_id = os.environ.get("RETELLAI_LOCAL_AGENT_ID")
        webhook_url = os.environ.get("RETELLAI_LOCAL_WEBHOOK")
        mode = "LOCAL"
    else:
        # Production mode (Quome cloud)
        agent_id = os.environ.get("RETELLAI_REMOTE_AGENT_ID")
        # Build webhook URL from CLOUD_APP_NAME for production
        cloud_app_name = os.environ.get("CLOUD_APP_NAME", "")
        if cloud_app_name:
            # Remove trailing slash if present to avoid double slashes
            base_url = cloud_app_name.rstrip("/")
            webhook_url = f"{base_url}/webhook"
        else:
            webhook_url = None
        mode = "REMOTE"

    # Common configuration
    api_key = os.environ.get("RETELLAI_API_KEY")
    from_number = os.environ.get("RETELLAI_PHONE_NUMBER")

    # Log configuration being used (without sensitive data)
    logger.info(f"=== Retell.ai Configuration ({mode} mode) ===")
    logger.info(f"RUNTIME_ENV: {runtime_env}")
    logger.info(f"DEV_STATE: {dev_state}")
    logger.info(f"Agent ID: {agent_id}")
    logger.info(f"From Number: {from_number}")
    logger.info(f"Webhook URL: {webhook_url}")
    logger.info(f"API Key configured: {'Yes' if api_key else 'No'}")

    # Validate configuration
    if not api_key:
        raise ValueError("RETELLAI_API_KEY is not configured")
    if not agent_id:
        agent_var = "RETELLAI_LOCAL_AGENT_ID" if mode == "LOCAL" else "RETELLAI_REMOTE_AGENT_ID"
        raise ValueError(f"{agent_var} is not configured")
    if not from_number:
        raise ValueError("RETELLAI_PHONE_NUMBER is not configured")
    if not webhook_url:
        webhook_var = "RETELLAI_LOCAL_WEBHOOK" if mode == "LOCAL" else "CLOUD_APP_NAME"
        raise ValueError(f"{webhook_var} is not configured")

    # Extract patient information
    phone_number = patient.get("phone_number")
    first_name = patient.get("first_name", "Patient")
    last_name = patient.get("last_name", "")
    email = patient.get("email_address", "")
    patient_id = patient.get("id")

    # Normalize phone number (basic normalization)
    normalized_phone = _normalize_phone_number(phone_number)

    # Prepare the API request
    call_request = {
        "agent_id": agent_id,
        "from_number": from_number,
        "to_number": normalized_phone,
        "webhook_url": webhook_url,
        "metadata": {
            "patient_name": f"{first_name} {last_name}".strip(),
            "patient_phone": normalized_phone,
            "patient_id": str(patient_id),
        },
        "retell_llm_dynamic_variables": {
            "patient_name": first_name,
            "phone_number": normalized_phone,
            "email_address": email,
        },
    }

    logger.info(f"Making Retell.ai API call with request: {json.dumps(call_request, indent=2)}")

    try:
        response = requests.post(
            "https://api.retellai.com/v2/create-phone-call",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=call_request,
            timeout=30,
        )

        if response.status_code in [
            200,
            201,
        ]:  # Both 200 and 201 are success for Retell.ai
            response_data = response.json()
            call_id = response_data.get("call_id")
            logger.info(f"Retell.ai call created successfully. Call ID: {call_id}")
            logger.info(f"Retell.ai API response: {response.text}")
            return call_id
        else:
            error_msg = f"Retell.ai API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to connect to Retell.ai API: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)


def _make_simulated_call(patient: Dict[str, Any]) -> str:
    """Simulate a call for testing purposes."""

    # Extract patient information
    first_name = patient.get("first_name", "Patient")
    last_name = patient.get("last_name", "")
    phone_number = patient.get("phone_number")
    patient_id = patient.get("id", "unknown")

    # Simulate realistic delay
    time.sleep(1)

    # Generate a mock call ID
    mock_call_id = f"sim_call_{patient_id}_{int(time.time())}"

    logger.info(f"SIMULATION: Call to {first_name} {last_name} at {phone_number}")
    logger.info(f"SIMULATION: Generated mock call ID: {mock_call_id}")

    return mock_call_id


def _normalize_phone_number(phone: str) -> str:
    """Normalize phone number to E.164 format."""
    if not phone:
        return phone

    # Remove all non-digit characters
    digits_only = "".join(filter(str.isdigit, phone))

    # If it starts with 1 and has 11 digits, it's already in US format
    if len(digits_only) == 11 and digits_only.startswith("1"):
        return f"+{digits_only}"

    # If it has 10 digits, assume US number and add country code
    elif len(digits_only) == 10:
        return f"+1{digits_only}"

    # Otherwise, return as-is with + prefix if not already present
    else:
        return f"+{digits_only}" if not phone.startswith("+") else phone


def check_retell_connection() -> bool:
    """Check if Retell.ai API connection is working.

    Returns:
        True if connection is successful, False otherwise
    """
    logger.info("check_retell_connection called - This is a placeholder implementation")

    # This is a placeholder implementation
    # In a full implementation, this would check API connectivity
    # For now, always return True to indicate the service is available

    return True
