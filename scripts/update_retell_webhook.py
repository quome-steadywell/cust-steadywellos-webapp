#!/usr/bin/env python3
"""
Update Retell webhook URLs dynamically based on environment.

This script automatically updates webhook URLs for development and production environments:
- In TEST/local development: Uses ngrok tunnel URL
- In PROD/cloud deployment: Uses the configured cloud application URL

Usage:
    python update_retell_webhook.py [--force]

Options:
    --force    Force update even if URLs appear to be the same

Environment Variables:
    RUNTIME_ENV              - 'TEST' for local dev, 'CLOUD' for production
    DEV_STATE               - 'TEST' for dev mode, 'PROD' for production
    RETELL_LOCAL_WEBHOOK    - ngrok URL for local development
    CLOUD_APP_NAME          - Application name for cloud deployment
    APPLICATION_NAME        - Alternative application name
    RETELL_API_KEY          - Retell.ai API key for webhook updates
"""

import os
import sys
import json
import urllib.parse
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

class RetellWebhookUpdater:
    def __init__(self):
        self.runtime_env = os.getenv('RUNTIME_ENV', 'TEST')
        self.dev_state = os.getenv('DEV_STATE', 'TEST')
        self.retell_api_key = os.getenv('RETELL_API_KEY')
        
        if not self.retell_api_key:
            raise ValueError("RETELL_API_KEY environment variable is required")
    
    def get_webhook_url(self) -> str:
        """
        Determine the appropriate webhook URL based on the current environment.
        
        Returns:
            str: The webhook URL to use for Retell configuration
        """
        if self.runtime_env == 'TEST' or self.dev_state == 'TEST':
            # Local development - use ngrok URL
            local_webhook = os.getenv('RETELL_LOCAL_WEBHOOK')
            if local_webhook:
                # Ensure the URL has the proper webhook path
                if not local_webhook.endswith('/webhook'):
                    local_webhook = local_webhook.rstrip('/') + '/webhook'
                return local_webhook
            else:
                # Fallback to localhost
                return 'http://localhost:5000/webhook'
        else:
            # Production - use cloud URL
            cloud_app = (os.getenv('CLOUD_APP_NAME') or 
                        os.getenv('APPLICATION_NAME') or 
                        'palliative-care-platform')
            
            # Construct the cloud webhook URL
            return f"https://{cloud_app}.demo.quome.cloud/webhook"
    
    def make_api_request(self, url: str, data: Dict[Any, Any] = None, method: str = 'GET') -> Dict[Any, Any]:
        """
        Make an authenticated request to the Retell API.
        
        Args:
            url: The API endpoint URL
            data: Optional data for POST/PUT requests
            method: HTTP method (GET, POST, PUT, etc.)
            
        Returns:
            dict: The JSON response from the API
        """
        headers = {
            'Authorization': f'Bearer {self.retell_api_key}',
            'Content-Type': 'application/json'
        }
        
        request_data = None
        if data and method in ['POST', 'PUT', 'PATCH']:
            request_data = json.dumps(data).encode('utf-8')
        
        request = urllib.request.Request(url, data=request_data, headers=headers, method=method)
        
        try:
            with urllib.request.urlopen(request) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            raise Exception(f"HTTP {e.code}: {error_body}")
        except urllib.error.URLError as e:
            raise Exception(f"URL Error: {e.reason}")
    
    def get_agent_config(self, agent_id: str) -> Dict[Any, Any]:
        """
        Get the current configuration for a Retell agent.
        
        Args:
            agent_id: The Retell agent ID
            
        Returns:
            dict: The agent configuration
        """
        url = f"https://api.retellai.com/agent/{agent_id}"
        return self.make_api_request(url)
    
    def update_agent_webhook(self, agent_id: str, webhook_url: str) -> Dict[Any, Any]:
        """
        Update the webhook URL for a Retell agent.
        
        Args:
            agent_id: The Retell agent ID
            webhook_url: The new webhook URL
            
        Returns:
            dict: The updated agent configuration
        """
        url = f"https://api.retellai.com/agent/{agent_id}"
        data = {
            "webhook_url": webhook_url
        }
        return self.make_api_request(url, data, method='PATCH')
    
    def update_webhook(self, force: bool = False) -> bool:
        """
        Update the webhook URL for the configured Retell agent.
        
        Args:
            force: Force update even if URLs appear to be the same
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        # Get the agent ID from environment
        agent_id = os.getenv('PALLIATIVE_DEMO_AGENT_ID')
        if not agent_id:
            print("⚠️  PALLIATIVE_DEMO_AGENT_ID not found in environment variables")
            print("Webhook update skipped - no agent configured")
            return False
        
        try:
            # Determine the target webhook URL
            target_webhook_url = self.get_webhook_url()
            
            print(f"🔧 Environment: {self.runtime_env} (DEV_STATE: {self.dev_state})")
            print(f"🎯 Target webhook URL: {target_webhook_url}")
            
            # Get current agent configuration
            print(f"📡 Fetching current configuration for agent {agent_id}...")
            current_config = self.get_agent_config(agent_id)
            current_webhook = current_config.get('webhook_url', '')
            
            print(f"📋 Current webhook URL: {current_webhook}")
            
            # Check if update is needed
            if current_webhook == target_webhook_url and not force:
                print("✅ Webhook URL is already up to date")
                return True
            
            # Update the webhook URL
            print(f"🔄 Updating webhook URL...")
            updated_config = self.update_agent_webhook(agent_id, target_webhook_url)
            
            # Verify the update
            new_webhook = updated_config.get('webhook_url', '')
            if new_webhook == target_webhook_url:
                print(f"✅ Webhook URL updated successfully: {new_webhook}")
                return True
            else:
                print(f"❌ Webhook update failed - URL mismatch")
                print(f"   Expected: {target_webhook_url}")
                print(f"   Actual:   {new_webhook}")
                return False
                
        except Exception as e:
            print(f"❌ Error updating webhook: {e}")
            return False

def main():
    """Main entry point for the webhook updater script."""
    force = '--force' in sys.argv
    
    try:
        updater = RetellWebhookUpdater()
        success = updater.update_webhook(force=force)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()