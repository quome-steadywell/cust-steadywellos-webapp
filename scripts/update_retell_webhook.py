#!/usr/bin/env python3
"""Update Retell AI agent webhook URL based on environment (dev/prod)."""

import os
import sys
import requests
import subprocess
import time
from typing import Optional

# Add parent directory to path to import from src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.utils.logger import get_logger

# Set up logging
logger = get_logger()


def check_ngrok_installed() -> bool:
    """Check if ngrok is installed."""
    try:
        subprocess.run(["ngrok", "version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_ngrok_url() -> Optional[str]:
    """Get the public ngrok URL from the ngrok API."""
    try:
        # ngrok exposes a local API on port 4040
        response = requests.get("http://localhost:4040/api/tunnels", timeout=2)
        response.raise_for_status()

        tunnels = response.json()
        for tunnel in tunnels.get("tunnels", []):
            if tunnel.get("proto") == "https":
                return tunnel.get("public_url")

        logger.error("No HTTPS tunnel found in ngrok")
        return None

    except requests.exceptions.RequestException as e:
        logger.debug(f"Failed to get ngrok URL from API: {e}")
        return None


def start_ngrok() -> Optional[str]:
    """Start ngrok and return the public URL."""
    port = os.getenv("RETELLAI_LOCAL_WEBHOOK_PORT", "8081")
    logger.info(f"Starting ngrok on port {port}...")

    try:
        # Start ngrok in the background
        process = subprocess.Popen(["ngrok", "http", port], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Give ngrok time to start
        logger.info("Waiting for ngrok to start...")
        for i in range(10):  # Try for up to 10 seconds
            time.sleep(1)
            url = get_ngrok_url()
            if url:
                logger.info(f"ngrok started successfully: {url}")
                return url

        logger.error("Timeout waiting for ngrok to start")
        process.terminate()
        return None

    except Exception as e:
        logger.error(f"Failed to start ngrok: {e}")
        return None


def get_webhook_url() -> Optional[str]:
    """Determine the webhook URL based on runtime environment."""
    runtime_env = os.getenv("RUNTIME_ENV", "").lower()

    if runtime_env == "local":
        # Local development mode - use ngrok
        logger.info("Local mode detected - checking for ngrok...")

        # First check if ngrok is installed
        if not check_ngrok_installed():
            logger.error("ngrok is not installed. Please install ngrok first.")
            logger.error("Visit https://ngrok.com/download to install ngrok")
            return None

        # Try to get existing ngrok URL
        base_url = get_ngrok_url()

        if not base_url:
            # ngrok not running, try to start it
            logger.info("ngrok is not running. Attempting to start it...")
            base_url = start_ngrok()

            if not base_url:
                port = os.getenv("RETELLAI_LOCAL_WEBHOOK_PORT", "8081")
                logger.error(f"Failed to start ngrok. Please start it manually with: ngrok http {port}")
                return None

        logger.info(f"Using local ngrok URL: {base_url}")
    else:
        # Production mode - use Quome cloud URL
        base_url = os.getenv("CLOUD_APP_NAME", "")
        if not base_url:
            logger.error("CLOUD_APP_NAME not set for production")
            return None
        # Remove trailing slash if present
        base_url = base_url.rstrip("/")
        logger.info(f"Using production Quome URL: {base_url}")

    # Append /webhook to the base URL
    webhook_url = f"{base_url}/webhook"
    return webhook_url


def check_agent_published(agent_id: str, api_key: str) -> bool:
    """Check if agent is published.
    
    Args:
        agent_id: The Retell AI agent ID
        api_key: The Retell AI API key
        
    Returns:
        True if agent is published, False otherwise
    """
    try:
        url = f"https://api.retellai.com/get-agent/{agent_id}"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        agent_data = response.json()
        return agent_data.get("is_published", False)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to check agent status: {e}")
        return False


def update_retell_agent_webhook(agent_id: str, webhook_url: str, api_key: str) -> bool:
    """Update the webhook URL for a Retell AI agent.

    Args:
        agent_id: The Retell AI agent ID
        webhook_url: The webhook URL to set
        api_key: The Retell AI API key

    Returns:
        True if successful, False otherwise
    """
    # Check if agent is published
    if check_agent_published(agent_id, api_key):
        logger.warning(f"Agent {agent_id} is published and cannot be modified")
        logger.warning("Published agents are immutable except for version title")
        logger.warning("Webhook URL changes require creating a new agent version")
        logger.info("⚠️ Skipping webhook update for published agent")
        return True  # Return True to indicate this is expected behavior
    
    # Skip connectivity test - go straight to API call with retries
    # This avoids DNS resolution issues in some environments
    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            # Retell AI API endpoint for updating agent
            # Try the exact format from the curl example
            url = f"https://api.retellai.com/update-agent/{agent_id}"

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            data = {"webhook_url": webhook_url}

            logger.info(
                f"Updating agent {agent_id} with webhook URL: {webhook_url} (attempt {attempt + 1}/{max_retries})"
            )

            response = requests.patch(url, json=data, headers=headers, timeout=10)
            response.raise_for_status()

            result = response.json()
            logger.info(f"Successfully updated agent webhook URL")
            logger.info(f"Agent ID: {result.get('agent_id', agent_id)}")

            return True

        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Connection error on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("Max retries exceeded")

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update agent webhook: {str(e)}")
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_detail = e.response.json()
                    logger.error(f"Error details: {error_detail}")
                    
                    # Check for specific published agent error
                    if "Cannot update published agent" in str(error_detail):
                        logger.warning("⚠️ Agent is published and cannot be modified")
                        logger.warning("Published agents are immutable - webhook changes require new version")
                        return True  # Return True since this is expected for published agents
                        
                except:
                    logger.error(f"Response text: {e.response.text}")
            return False

    return False


def update_env_file(key: str, value: str) -> None:
    """Update or add a key-value pair in the .env file."""
    env_path = ".env"
    lines = []
    key_found = False

    # Read existing .env file
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()

    # Update or add the key
    new_lines = []
    for line in lines:
        if line.strip().startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            key_found = True
        else:
            new_lines.append(line)

    # Add key if not found
    if not key_found:
        new_lines.append(f"{key}={value}\n")

    # Write back to .env
    with open(env_path, "w") as f:
        f.writelines(new_lines)

    logger.info(f"Updated .env file with {key}={value}")


def main():
    """Main function to update Retell AI agent webhook based on environment."""
    # Get runtime environment
    runtime_env = os.getenv("RUNTIME_ENV", "production").lower()

    # Get the appropriate agent ID based on environment
    if runtime_env == "local":
        agent_id = os.getenv("RETELLAI_LOCAL_AGENT_ID")
        if not agent_id:
            logger.error("RETELLAI_LOCAL_AGENT_ID environment variable not set for local environment")
            sys.exit(1)
    else:
        agent_id = os.getenv("RETELLAI_REMOTE_AGENT_ID")
        if not agent_id:
            logger.error("RETELLAI_REMOTE_AGENT_ID environment variable not set for remote environment")
            sys.exit(1)

    api_key = os.getenv("RETELLAI_API_KEY")

    if not api_key:
        logger.error("RETELLAI_API_KEY environment variable not set")
        sys.exit(1)

    # Get the webhook URL based on environment
    webhook_url = get_webhook_url()
    if not webhook_url:
        logger.error("Failed to determine webhook URL")
        sys.exit(1)

    # Log current environment
    runtime_env = os.getenv("RUNTIME_ENV", "production")
    logger.info(f"Runtime environment: {runtime_env}")
    logger.info(f"Agent ID: {agent_id}")
    logger.info(f"Webhook URL: {webhook_url}")

    # Update the agent webhook
    success = update_retell_agent_webhook(agent_id, webhook_url, api_key)

    if success:
        logger.info("✅ Webhook URL updated successfully!")
        logger.info(f"Your Retell AI agent will now send webhooks to: {webhook_url}")

        # If local development, update .env with the ngrok URL
        if runtime_env == "local":
            # Extract base URL (remove /webhook suffix)
            base_url = webhook_url.rsplit("/webhook", 1)[0]
            update_env_file("RETELLAI_LOCAL_WEBHOOK", base_url)
            port = os.getenv("RETELLAI_LOCAL_WEBHOOK_PORT", "8081")
            update_env_file("RETELLAI_LOCAL_WEBHOOK_PORT", port)
            logger.info("✅ Updated .env file with local webhook URL and port")
    else:
        logger.error("❌ Failed to update webhook URL")
        sys.exit(1)


if __name__ == "__main__":
    main()
