"""
Custom Anthropic client wrapper to handle compatibility issues
"""


class AnthropicClientWrapper:
    """
    A minimal wrapper around Anthropic API to handle compatibility issues
    """

    def __init__(self, api_key):
        """Initialize the client with just the API key"""
        self.api_key = api_key

    def call_model(self, model, prompt=None, system=None, messages=None, max_tokens=1000):
        """
        Make a call to Claude model using the appropriate API
        Works with any version of the client library by calling APIs directly
        """
        import requests
        import json

        # Direct API call to avoid client library issues
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        # Handle different API call formats
        if messages:
            # Messages API
            payload = {"model": model, "max_tokens": max_tokens, "messages": messages}
            if system:
                payload["system"] = system
        else:
            # Completion API (legacy)
            payload = {
                "model": model,
                "prompt": prompt,
                "max_tokens_to_sample": max_tokens,
                "temperature": 0.2,
            }

        # Make direct API call
        response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)

        # Handle response
        if response.status_code == 200:
            data = response.json()
            return data.get("content", [{"text": "No content returned"}])[0]["text"]
        else:
            error_message = f"API call failed: {response.status_code} {response.text}"
            raise Exception(error_message)


def get_anthropic_client(api_key):
    """Get a working Anthropic client that handles compatibility issues"""
    return AnthropicClientWrapper(api_key)
