import unittest
from unittest.mock import patch, MagicMock
import json
import pytest
import requests

from src.core.anthropic_client import AnthropicClientWrapper, get_anthropic_client

# Mark all tests as nondestructive
pytestmark = pytest.mark.nondestructive


class TestAnthropicClientWrapper(unittest.TestCase):
    """Test cases for AnthropicClientWrapper"""

    def setUp(self):
        """Set up test fixtures"""
        self.api_key = "test-api-key"
        self.client = AnthropicClientWrapper(self.api_key)

        # Mock response for successful API call
        self.mock_success_response = MagicMock()
        self.mock_success_response.status_code = 200
        self.mock_success_response.json.return_value = {
            "content": [{"text": "This is a test response"}]
        }

        # Mock response for failed API call
        self.mock_error_response = MagicMock()
        self.mock_error_response.status_code = 400
        self.mock_error_response.text = "Bad Request"

    @patch("requests.post")
    def test_init(self, mock_post):
        """Test initialization of AnthropicClientWrapper"""
        client = AnthropicClientWrapper(self.api_key)
        self.assertEqual(client.api_key, self.api_key)

    @patch("requests.post")
    def test_call_model_with_messages(self, mock_post):
        """Test call_model with messages format"""
        # Setup
        mock_post.return_value = self.mock_success_response
        messages = [{"role": "user", "content": "Hello"}]
        system = "You are a helpful assistant"

        # Execute
        result = self.client.call_model(
            model="claude-3-sonnet-20240229", messages=messages, system=system
        )

        # Verify
        mock_post.assert_called_once()
        call_args = mock_post.call_args[1]

        # Check headers
        self.assertEqual(call_args["headers"]["x-api-key"], self.api_key)
        self.assertEqual(call_args["headers"]["anthropic-version"], "2023-06-01")

        # Check payload
        payload = call_args["json"]
        self.assertEqual(payload["model"], "claude-3-sonnet-20240229")
        self.assertEqual(payload["messages"], messages)
        self.assertEqual(payload["system"], system)

        # Check result
        self.assertEqual(result, "This is a test response")

    @patch("requests.post")
    def test_call_model_with_prompt(self, mock_post):
        """Test call_model with prompt format (legacy)"""
        # Setup
        mock_post.return_value = self.mock_success_response
        prompt = "Hello, how are you?"

        # Execute
        result = self.client.call_model(model="claude-3-sonnet-20240229", prompt=prompt)

        # Verify
        mock_post.assert_called_once()
        call_args = mock_post.call_args[1]

        # Check payload
        payload = call_args["json"]
        self.assertEqual(payload["prompt"], prompt)
        self.assertEqual(payload["temperature"], 0.2)

        # Check result
        self.assertEqual(result, "This is a test response")

    @patch("requests.post")
    def test_call_model_error(self, mock_post):
        """Test call_model with error response"""
        # Setup
        mock_post.return_value = self.mock_error_response

        # Execute and verify
        with self.assertRaises(Exception) as context:
            self.client.call_model(model="claude-3-sonnet-20240229", prompt="Hello")

        self.assertIn("API call failed: 400 Bad Request", str(context.exception))

    def test_get_anthropic_client(self):
        """Test get_anthropic_client function"""
        client = get_anthropic_client(self.api_key)
        self.assertIsInstance(client, AnthropicClientWrapper)
        self.assertEqual(client.api_key, self.api_key)


# Parameterized tests for edge cases
@pytest.mark.parametrize(
    "model,max_tokens,expected_max_tokens",
    [
        ("claude-3-sonnet-20240229", 1000, 1000),
        ("claude-3-sonnet-20240229", None, 1000),  # Default value
        ("claude-3-sonnet-20240229", 0, 0),  # Edge case
        ("claude-3-sonnet-20240229", 100000, 100000),  # Large value
    ],
)
def test_call_model_max_tokens(model, max_tokens, expected_max_tokens):
    """Test call_model with different max_tokens values"""
    # Setup
    client = AnthropicClientWrapper("test-api-key")

    # Mock the requests.post method
    with patch("requests.post") as mock_post:
        # Configure the mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"content": [{"text": "Test response"}]}
        mock_post.return_value = mock_response

        # Call the method with the test parameters
        kwargs = {"model": model, "messages": [{"role": "user", "content": "Hello"}]}
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens

        client.call_model(**kwargs)

        # Verify the correct max_tokens was used
        payload = mock_post.call_args[1]["json"]
        assert payload["max_tokens"] == expected_max_tokens


if __name__ == "__main__":
    unittest.main()
