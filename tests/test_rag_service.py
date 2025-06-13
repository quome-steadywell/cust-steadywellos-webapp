import unittest
from unittest.mock import patch, MagicMock, Mock
import json
import pytest
from flask import Flask, current_app

from src.core.rag_service import process_assessment, generate_call_script, analyze_call_transcript
from src.models.patient import Patient, ProtocolType, Gender
from src.models.protocol import Protocol

# Mark all tests as nondestructive
pytestmark = pytest.mark.nondestructive

# Fixtures for common test scenarios
@pytest.fixture
def mock_patient():
    """Create a mock Patient object for testing"""
    patient = Mock(spec=Patient)
    patient.id = 1
    patient.full_name = "John Doe"
    patient.first_name = "John"
    patient.last_name = "Doe"
    patient.age = 65
    patient.gender = Gender.MALE
    patient.primary_diagnosis = "Chronic Heart Failure"
    patient.secondary_diagnoses = "Hypertension, Type 2 Diabetes"
    patient.protocol_type = ProtocolType.HEART_FAILURE
    return patient

@pytest.fixture
def mock_protocol():
    """Create a mock Protocol object for testing"""
    protocol = Mock(spec=Protocol)
    protocol.id = 1
    protocol.name = "Heart Failure Protocol"
    protocol.protocol_type = ProtocolType.HEART_FAILURE
    protocol.version = "1.0"
    protocol.questions = [
        {"id": "q1", "text": "How would you rate your breathing difficulty today?", "type": "scale", "min": 0, "max": 10},
        {"id": "q2", "text": "Have you noticed any swelling in your ankles or legs?", "type": "boolean"}
    ]
    protocol.decision_tree = {
        "root": {
            "condition": "q1 > 5",
            "true_branch": "intervention_1",
            "false_branch": "check_swelling"
        },
        "check_swelling": {
            "condition": "q2 == true",
            "true_branch": "intervention_2",
            "false_branch": "intervention_3"
        }
    }
    protocol.interventions = {
        "intervention_1": "Contact physician immediately for breathing difficulty.",
        "intervention_2": "Elevate legs and monitor swelling. Contact care team if worsens.",
        "intervention_3": "Continue regular monitoring."
    }

    # Add get_latest_active_protocol as a class method
    protocol.get_latest_active_protocol = classmethod(lambda cls, protocol_type: protocol)

    return protocol

@pytest.fixture
def mock_anthropic_client():
    """Create a mock Anthropic client for testing"""
    client = MagicMock()
    client.call_model.return_value = "This is a test response from the AI model."
    return client

# Use the app fixture from conftest.py instead

class TestRagService(unittest.TestCase):
    """Test cases for RAG service functions"""

    @pytest.fixture(autouse=True)
    def setup_app_context(self, app):
        """Set up app context for each test"""
        self.app = app
        self.app.config['ANTHROPIC_API_KEY'] = 'test-api-key'
        with self.app.app_context():
            yield

    def setUp(self):
        """Set up test fixtures"""

        # Create mock objects
        self.patient = Mock(spec=Patient)
        self.patient.id = 1
        self.patient.full_name = "John Doe"
        self.patient.age = 65
        self.patient.gender = Gender.MALE
        self.patient.primary_diagnosis = "Chronic Heart Failure"
        self.patient.secondary_diagnoses = "Hypertension, Type 2 Diabetes"
        self.patient.protocol_type = ProtocolType.HEART_FAILURE

        self.protocol = Mock(spec=Protocol)
        self.protocol.name = "Heart Failure Protocol"
        self.protocol.protocol_type = ProtocolType.HEART_FAILURE
        self.protocol.version = "1.0"
        self.protocol.questions = [
            {"id": "q1", "text": "How would you rate your breathing difficulty today?", "type": "scale", "min": 0, "max": 10},
            {"id": "q2", "text": "Have you noticed any swelling in your ankles or legs?", "type": "boolean"}
        ]
        self.protocol.decision_tree = {
            "root": {
                "condition": "q1 > 5",
                "true_branch": "intervention_1",
                "false_branch": "check_swelling"
            },
            "check_swelling": {
                "condition": "q2 == true",
                "true_branch": "intervention_2",
                "false_branch": "intervention_3"
            }
        }
        self.protocol.interventions = {
            "intervention_1": "Contact physician immediately for breathing difficulty.",
            "intervention_2": "Elevate legs and monitor swelling. Contact care team if worsens.",
            "intervention_3": "Continue regular monitoring."
        }

        # Mock symptoms and responses
        self.symptoms = {
            "breathing_difficulty": 7,
            "fatigue": 5,
            "swelling": 3
        }

        self.responses = {
            "q1": 7,
            "q2": True
        }

    def tearDown(self):
        """Clean up after tests"""
        # No need to pop context as it's handled by the context manager

    @patch('src.core.rag_service.get_anthropic_client')
    def test_process_assessment(self, mock_get_client):
        """Test process_assessment function"""
        # Setup
        mock_client = MagicMock()
        mock_client.call_model.return_value = "Test AI guidance response"
        mock_get_client.return_value = mock_client

        # Execute
        result = process_assessment(self.patient, self.protocol, self.symptoms, self.responses)

        # Verify
        mock_get_client.assert_called_once_with(current_app.config.get('ANTHROPIC_API_KEY'))
        mock_client.call_model.assert_called_once()
        self.assertEqual(result, "Test AI guidance response")

        # Check that the prompt contains key patient and protocol information
        call_args = mock_client.call_model.call_args[1]
        messages = call_args['messages']
        prompt = messages[0]['content']
        self.assertIn(self.patient.primary_diagnosis, prompt)
        self.assertIn(self.patient.full_name, prompt)
        self.assertIn(json.dumps(self.symptoms, indent=2), prompt)

    @patch('src.core.rag_service.get_anthropic_client')
    def test_generate_call_script(self, mock_get_client):
        """Test generate_call_script function"""
        # Setup
        mock_client = MagicMock()
        mock_client.call_model.return_value = "Test call script response"
        mock_get_client.return_value = mock_client
        call_type = "initial_assessment"

        # Execute
        result = generate_call_script(self.patient, self.protocol, call_type)

        # Verify
        mock_get_client.assert_called_once_with(current_app.config.get('ANTHROPIC_API_KEY'))
        mock_client.call_model.assert_called_once()
        self.assertEqual(result, "Test call script response")

        # Check that the prompt contains key information
        call_args = mock_client.call_model.call_args[1]
        messages = call_args['messages']
        prompt = messages[0]['content']
        self.assertIn(self.patient.primary_diagnosis, prompt)
        self.assertIn(call_type, prompt)
        self.assertIn(json.dumps(self.protocol.questions, indent=2), prompt)

    @patch('src.core.rag_service.get_anthropic_client')
    def test_analyze_call_transcript(self, mock_get_client):
        """Test analyze_call_transcript function"""
        # Setup
        mock_client = MagicMock()
        mock_client.call_model.return_value = """```json
        {
            "symptoms": {
                "breathing_difficulty": 7,
                "fatigue": 5
            },
            "concerns": ["Worried about medication side effects"],
            "medication_issues": ["Missed dose yesterday"],
            "psychosocial_factors": ["Feeling isolated"],
            "recommended_actions": ["Follow up with primary care"]
        }
        ```"""
        mock_get_client.return_value = mock_client
        transcript = "This is a test transcript of a patient call."

        # Execute
        result = analyze_call_transcript(transcript, self.patient, self.protocol)

        # Verify
        mock_get_client.assert_called_once_with(current_app.config.get('ANTHROPIC_API_KEY'))
        mock_client.call_model.assert_called_once()

        # Check that result is parsed correctly
        self.assertIsInstance(result, dict)
        self.assertIn("symptoms", result)
        self.assertIn("concerns", result)
        self.assertEqual(result["symptoms"]["breathing_difficulty"], 7)

    @patch('src.core.rag_service.get_anthropic_client')
    def test_analyze_call_transcript_invalid_json(self, mock_get_client):
        """Test analyze_call_transcript with invalid JSON response"""
        # Setup
        mock_client = MagicMock()
        mock_client.call_model.return_value = "This is not valid JSON"
        mock_get_client.return_value = mock_client
        transcript = "This is a test transcript of a patient call."

        # Execute
        result = analyze_call_transcript(transcript, self.patient, self.protocol)

        # Verify
        self.assertIsInstance(result, dict)
        self.assertIn("analysis", result)
        self.assertEqual(result["analysis"], "This is not valid JSON")

    @patch('src.core.rag_service.get_anthropic_client')
    def test_process_assessment_exception(self, mock_get_client):
        """Test process_assessment with exception"""
        # Setup
        mock_get_client.side_effect = Exception("Test exception")

        # Execute
        result = process_assessment(self.patient, self.protocol, self.symptoms, self.responses)

        # Verify
        self.assertIn("Error generating guidance", result)
        self.assertIn("Test exception", result)

# Parameterized tests for edge cases
@pytest.mark.parametrize("transcript,expected_keys", [
    ("Normal transcript", ["analysis"]),  # Normal case
    ("", ["analysis"]),  # Empty transcript
    ("Very long " + "transcript " * 100, ["analysis"]),  # Very long transcript
])
def test_analyze_call_transcript_edge_cases(transcript, expected_keys, mock_patient, mock_protocol, app_context, app):
    """Test analyze_call_transcript with edge cases"""
    with patch('src.core.rag_service.get_anthropic_client') as mock_get_client:
        # Setup
        mock_client = MagicMock()
        mock_client.call_model.return_value = "Not JSON"
        mock_get_client.return_value = mock_client

        # Execute
        result = analyze_call_transcript(transcript, mock_patient, mock_protocol)

        # Verify
        assert isinstance(result, dict)
        for key in expected_keys:
            assert key in result

if __name__ == '__main__':
    unittest.main()
