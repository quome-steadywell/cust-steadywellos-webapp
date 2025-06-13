import unittest
from unittest.mock import patch, MagicMock, Mock
import pytest
from flask import Flask, url_for
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse

from src.core.twilio_service import get_twilio_client, initiate_call, generate_call_twiml, process_call_recording
from src.models.call import Call, CallStatus
from src.models.patient import Patient, ProtocolType, Gender
from src.models.protocol import Protocol

# Mark all tests as nondestructive
pytestmark = pytest.mark.nondestructive

# Fixtures for common test scenarios
@pytest.fixture
def mock_twilio_client():
    """Create a mock Twilio client for testing"""
    client = MagicMock(spec=Client)

    # Mock calls resource
    calls = MagicMock()
    call = MagicMock()
    call.sid = "CA123456789"
    call.status = "queued"
    calls.create.return_value = call
    client.calls = calls

    # Mock recordings resource
    recording = MagicMock()
    recording.duration = 120
    client.recordings.return_value = MagicMock()
    client.recordings.return_value.fetch.return_value = recording

    # Mock transcriptions
    transcriptions = MagicMock()
    transcription = MagicMock()
    transcription.transcription_text = "This is a test transcription."
    transcriptions.list.return_value = [transcription]
    client.recordings.return_value.transcriptions = transcriptions

    return client

@pytest.fixture
def mock_call():
    """Create a mock Call object for testing"""
    call = Mock(spec=Call)
    call.id = 1
    call.patient_id = 1
    call.call_type = "assessment"
    call.status = CallStatus.SCHEDULED
    call.twilio_sid = None
    return call

@pytest.fixture
def mock_patient():
    """Create a mock Patient object for testing"""
    patient = Mock(spec=Patient)
    patient.id = 1
    patient.first_name = "John"
    patient.last_name = "Doe"
    patient.full_name = "John Doe"
    patient.age = 65
    patient.gender = Gender.MALE
    patient.primary_diagnosis = "Chronic Heart Failure"
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

    # Add get_latest_active_protocol as a class method
    protocol.get_latest_active_protocol = classmethod(lambda cls, protocol_type: protocol)

    return protocol

@pytest.fixture
def app():
    """Create a Flask app context for testing"""
    app = Flask(__name__)
    app.config['TWILIO_ACCOUNT_SID'] = 'test_account_sid'
    app.config['TWILIO_AUTH_TOKEN'] = 'test_auth_token'
    app.config['SERVER_NAME'] = 'localhost'

    # Set up application context
    with app.app_context():
        yield app

class TestTwilioService(unittest.TestCase):
    """Test cases for Twilio service functions"""

    @pytest.fixture(autouse=True)
    def setup_app_context(self, app):
        """Set up app context for each test"""
        self.app = app
        self.app.config['TWILIO_ACCOUNT_SID'] = 'test_account_sid'
        self.app.config['TWILIO_AUTH_TOKEN'] = 'test_auth_token'
        self.app.config['SERVER_NAME'] = 'localhost'
        with self.app.app_context():
            with self.app.test_request_context():
                yield

    def setUp(self):
        """Set up test fixtures"""

        # Create mock objects
        self.call = Mock(spec=Call)
        self.call.id = 1
        self.call.patient_id = 1
        self.call.call_type = "assessment"
        self.call.status = CallStatus.SCHEDULED
        self.call.twilio_sid = None

        self.patient = Mock(spec=Patient)
        self.patient.id = 1
        self.patient.first_name = "John"
        self.patient.last_name = "Doe"
        self.patient.full_name = "John Doe"

        # Mock Patient.query
        self.patient_query = MagicMock()
        self.patient_query.get.return_value = self.patient

    def tearDown(self):
        """Clean up after tests"""
        # No need to pop contexts as they are handled by the context manager

    @patch('src.core.twilio_service.Client')
    def test_get_twilio_client(self, mock_client_class):
        """Test get_twilio_client function"""
        # Setup
        mock_client_class.return_value = "mock_client"

        # Execute
        client = get_twilio_client()

        # Verify
        mock_client_class.assert_called_once_with('test_account_sid', 'test_auth_token')
        self.assertEqual(client, "mock_client")

    def test_get_twilio_client_missing_credentials(self):
        """Test get_twilio_client with missing credentials"""
        # Setup
        self.app.config['TWILIO_ACCOUNT_SID'] = None

        # Execute and verify
        with self.assertRaises(ValueError) as context:
            get_twilio_client()

        self.assertIn("Twilio credentials not configured", str(context.exception))

    @patch('src.core.twilio_service.get_twilio_client')
    @patch('src.core.twilio_service.url_for')
    def test_initiate_call(self, mock_url_for, mock_get_client):
        """Test initiate_call function"""
        # Setup
        mock_client = MagicMock()
        mock_call = MagicMock()
        mock_call.sid = "CA123456789"
        mock_call.status = "queued"
        mock_client.calls.create.return_value = mock_call
        mock_get_client.return_value = mock_client

        mock_url_for.side_effect = lambda endpoint, **kwargs: f"https://example.com/{endpoint}"

        # Execute
        result = initiate_call(
            to_number="+15551234567",
            from_number="+15557654321",
            call_id=1,
            call_type="assessment"
        )

        # Verify
        mock_get_client.assert_called_once()
        mock_client.calls.create.assert_called_once()
        self.assertEqual(result["call_sid"], "CA123456789")
        self.assertEqual(result["status"], "queued")

    @patch('src.core.twilio_service.Patient')
    def test_generate_call_twiml_assessment(self, mock_patient_class):
        """Test generate_call_twiml for assessment call type"""
        # Setup
        mock_patient_class.query.get.return_value = self.patient
        self.call.call_type = "assessment"

        # Execute
        result = generate_call_twiml(self.call)

        # Verify
        mock_patient_class.query.get.assert_called_once_with(1)
        self.assertIsInstance(result, str)
        self.assertIn("Hello, this is the palliative care coordination service", result)
        self.assertIn("John Doe", result)

    @patch('src.core.twilio_service.Patient')
    def test_generate_call_twiml_follow_up(self, mock_patient_class):
        """Test generate_call_twiml for follow_up call type"""
        # Setup
        mock_patient_class.query.get.return_value = self.patient
        self.call.call_type = "follow_up"

        # Execute
        result = generate_call_twiml(self.call)

        # Verify
        mock_patient_class.query.get.assert_called_once_with(1)
        self.assertIsInstance(result, str)
        self.assertIn("follow up with", result)
        self.assertIn("John Doe", result)

    @patch('src.core.twilio_service.Patient')
    def test_generate_call_twiml_generic(self, mock_patient_class):
        """Test generate_call_twiml for generic call type"""
        # Setup
        mock_patient_class.query.get.return_value = self.patient
        self.call.call_type = "generic"

        # Execute
        result = generate_call_twiml(self.call)

        # Verify
        mock_patient_class.query.get.assert_called_once_with(1)
        self.assertIsInstance(result, str)
        self.assertIn("A care coordinator will be with you shortly", result)

    @patch('src.core.twilio_service.Patient')
    def test_generate_call_twiml_patient_not_found(self, mock_patient_class):
        """Test generate_call_twiml when patient not found"""
        # Setup
        mock_patient_class.query.get.return_value = None

        # Execute
        result = generate_call_twiml(self.call)

        # Verify
        mock_patient_class.query.get.assert_called_once_with(1)
        self.assertIsInstance(result, str)
        self.assertIn("Error: Patient information not found", result)

    @patch('src.core.twilio_service.get_twilio_client')
    @patch('src.core.twilio_service.Patient')
    @patch('src.core.twilio_service.Protocol')
    @patch('src.core.twilio_service.analyze_call_transcript')
    def test_process_call_recording(self, mock_analyze, mock_protocol_class, mock_patient_class, mock_get_client):
        """Test process_call_recording function"""
        # Setup
        mock_client = MagicMock()
        mock_recording = MagicMock()
        mock_recording.duration = 120
        mock_client.recordings.return_value.fetch.return_value = mock_recording

        mock_transcription = MagicMock()
        mock_transcription.transcription_text = "This is a test transcription."
        mock_client.recordings.return_value.transcriptions.list.return_value = [mock_transcription]

        mock_get_client.return_value = mock_client

        mock_patient = MagicMock()
        mock_patient.protocol_type = ProtocolType.HEART_FAILURE
        mock_patient_class.query.get.return_value = mock_patient

        mock_protocol = MagicMock()
        mock_protocol_class.get_latest_active_protocol.return_value = mock_protocol

        mock_analyze.return_value = {"symptoms": {"pain": 5}}

        # Execute
        result = process_call_recording(
            recording_sid="RE123456789",
            recording_url="https://example.com/recording.mp3",
            call=self.call
        )

        # Verify
        mock_get_client.assert_called_once()
        mock_client.recordings.assert_called_with("RE123456789")
        mock_client.recordings.return_value.fetch.assert_called_once()
        mock_client.recordings.return_value.transcriptions.list.assert_called_once()

        self.assertEqual(result["recording_url"], "https://example.com/recording.mp3")
        self.assertEqual(result["transcript"], "This is a test transcription.")
        self.assertEqual(result["duration"], 120)
        self.assertEqual(result["analysis"], {"symptoms": {"pain": 5}})

    @patch('src.core.twilio_service.get_twilio_client')
    def test_process_call_recording_no_transcription(self, mock_get_client):
        """Test process_call_recording with no transcription"""
        # Setup
        mock_client = MagicMock()
        mock_recording = MagicMock()
        mock_recording.duration = 120
        mock_client.recordings.return_value.fetch.return_value = mock_recording

        # Empty transcriptions list
        mock_client.recordings.return_value.transcriptions.list.return_value = []

        mock_get_client.return_value = mock_client

        # Execute
        result = process_call_recording(
            recording_sid="RE123456789",
            recording_url="https://example.com/recording.mp3",
            call=self.call
        )

        # Verify
        self.assertEqual(result["transcript"], "[Transcription not available]")
        self.assertIsNone(result["analysis"])

    @patch('src.core.twilio_service.get_twilio_client')
    def test_process_call_recording_exception(self, mock_get_client):
        """Test process_call_recording with exception"""
        # Setup
        mock_get_client.side_effect = Exception("Test exception")

        # Execute
        result = process_call_recording(
            recording_sid="RE123456789",
            recording_url="https://example.com/recording.mp3",
            call=self.call
        )

        # Verify
        self.assertEqual(result["recording_url"], "https://example.com/recording.mp3")
        self.assertEqual(result["transcript"], "[Error processing recording]")
        self.assertEqual(result["error"], "Test exception")

# Parameterized tests for edge cases
@pytest.mark.parametrize("to_number,from_number,expected_exception", [
    ("+15551234567", "+15557654321", None),  # Normal case
    ("", "+15557654321", "Exception"),  # Empty to_number
    ("+15551234567", "", "Exception"),  # Empty from_number
    ("invalid", "+15557654321", "Exception"),  # Invalid to_number
])
def test_initiate_call_edge_cases(to_number, from_number, expected_exception, app):
    """Test initiate_call with edge cases"""
    with app.app_context():
        with patch('src.core.twilio_service.get_twilio_client') as mock_get_client:
            with patch('src.core.twilio_service.url_for') as mock_url_for:
                # Setup
                mock_client = MagicMock()
                if expected_exception:
                    mock_client.calls.create.side_effect = Exception("Test exception")
                else:
                    mock_call = MagicMock()
                    mock_call.sid = "CA123456789"
                    mock_call.status = "queued"
                    mock_client.calls.create.return_value = mock_call

                mock_get_client.return_value = mock_client
                mock_url_for.side_effect = lambda endpoint, **kwargs: f"https://example.com/{endpoint}"

                # Execute and verify
                if expected_exception:
                    with pytest.raises(Exception):
                        initiate_call(to_number=to_number, from_number=from_number, call_id=1, call_type="assessment")
                else:
                    result = initiate_call(to_number=to_number, from_number=from_number, call_id=1, call_type="assessment")
                    assert result["call_sid"] == "CA123456789"
                    assert result["status"] == "queued"

if __name__ == '__main__':
    unittest.main()
