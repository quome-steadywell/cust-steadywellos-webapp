# Protocol Injection System Documentation

## Overview

The Protocol Injection System is a pre-call configuration service that enhances Retell AI agents with patient-specific clinical protocol questions and automated escalation logic. This system enables intelligent, protocol-driven patient check-in calls with automatic nurse escalation based on symptom severity.

## Key Features

- **Pre-call Agent Configuration**: Configures Retell AI agents with patient-specific protocol questions before call initiation
- **Protocol-Specific Questioning**: Dynamically loads questions based on patient's protocol type (Cancer, Heart Failure, COPD, FIT)
- **Intelligent Escalation**: Automatic nurse callback scheduling based on symptom severity thresholds
- **Conversational Branching**: Agent adapts conversation flow based on patient wellness status
- **Clinical Integration**: Seamlessly integrates with existing SteadywellOS clinical protocols

## Architecture

### Components

1. **ProtocolInjectionService** (`src/services/protocol_injection.py`)
   - Core service for agent configuration
   - Handles protocol loading and prompt generation
   - Manages Retell AI API communication

2. **Protocol Models** (`src/models/protocol.py`)
   - Stores clinical protocol definitions
   - Includes questions, decision trees, and interventions
   - Supports multiple protocol types

3. **Patient Models** (`src/models/patient.py`)
   - Links patients to specific protocol types
   - Contains patient demographic and contact information

4. **Test Scripts** (`scripts/test_protocol_injection.py`)
   - Validates protocol injection functionality
   - Supports both dry-run and live testing

## Protocol Types

The system supports the following clinical protocols:

- **CANCER**: Advanced cancer palliative care protocol (15 questions)
- **HEART_FAILURE**: Heart failure palliative care protocol (15 questions)  
- **COPD**: COPD palliative care protocol (15 questions)
- **FIT**: Wellness monitoring protocol (15 questions)
- **GENERAL**: General palliative care protocol

## Escalation Logic

The system implements a three-tier escalation model based on symptom severity:

### Escalation Thresholds

1. **Urgent (Score ≥7)**: "I'll arrange for a nurse to ring you in 10 minutes to discuss your symptoms."
2. **Moderate (Score 3-6)**: "I'll arrange for a nurse to ring you back in an hour."
3. **Stable (Score <3)**: "I'm hoping you will feel better. Let me schedule your next check-in."

### Evaluation Process

- Agent asks all protocol questions first
- Evaluates ALL responses against thresholds
- Triggers highest applicable escalation level
- Uses ANY logic (if ANY answer meets threshold, escalate)

## Call Flow

### 1. Pre-Call Configuration

```python
from src.services.protocol_injection import ProtocolInjectionService

# Configure agent before call
service = ProtocolInjectionService()
success = service.prepare_agent_for_call(patient_id, agent_id)
```

### 2. Agent Conversation Flow

1. **Initial Greeting**
   - "Hi, this is your nurse calling from SteadyWellOS Palliative Services for your scheduled check-in"

2. **Identity Verification (REQUIRED)**
   - "Am I speaking to [Patient First Name]? Can you verify your date of birth for me to proceed?"
   - Expected answer: [Patient's DOB formatted as "Month Day, Year"]
   - If correct: Proceed to wellness assessment
   - If incorrect: End call for privacy protection

3. **Wellness Assessment**
   - "How are you feeling today?"
   - Branch based on response:
     - Feeling well → Schedule follow-up
     - Feeling unwell → Proceed to protocol assessment

4. **Protocol Assessment** (if unwell AND identity verified)
   - Ask all 15 protocol-specific questions
   - Record responses on 0-10 scales or multiple choice
   - Examples:
     - "Rate your current pain level from 0-10"
     - "Are you experiencing nausea or vomiting?"
     - "Rate your fatigue level from 0-10"

5. **Escalation Decision**
   - Evaluate all responses against thresholds
   - Provide appropriate escalation message
   - End call professionally

### 6. Post-Call Processing

- Existing call system handles call recording
- Assessment data saved via existing workflows
- Nurse notifications triggered as appropriate

## API Integration

### Retell AI LLM Configuration

The system updates LLM prompts and publishes agents via Retell AI API:

```python
# Update LLM Prompt
PATCH https://api.retellai.com/update-retell-llm/{llm_id}

# Request Body
{
    "general_prompt": "Enhanced protocol-specific prompt..."
}

# Publish Agent (REQUIRED for changes to take effect)
POST https://api.retellai.com/publish-agent/{agent_id}

# Request Body
{}
```

### Agent and LLM IDs

- **Development Agent**: `agent_ca445602b7ce60f9d67037e3d8`
  - **LLM**: `llm_f3f91d752388582b921eab4a0a42`
- **Production Agent**: `agent_88609f029da1444efad68581eb`
  - **LLM**: `llm_a79d286cb8f09701e355cf0ff69a`

### Publishing Workflow

1. **Update LLM Prompt**: Modify `general_prompt` field with protocol-specific content
2. **Publish Agent**: Activate changes for live calls using publish endpoint
3. **Verify**: Check `is_published: true` and incremented version number

**Important**: Only published agent versions are used for actual calls. Unpublished changes remain in draft state.

## Database Schema

### Protocols Table

```sql
protocols (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    protocol_type ENUM('cancer', 'heart_failure', 'copd', 'fit', 'general'),
    version VARCHAR(50) DEFAULT '1.0',
    questions JSON NOT NULL,           -- Array of question objects
    decision_tree JSON NOT NULL,       -- Decision logic for escalation
    interventions JSON NOT NULL,       -- Recommended interventions
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Question Format

```json
{
    "id": 1,
    "text": "Rate your current pain level from 0-10",
    "type": "numeric",
    "min_value": 0,
    "max_value": 10,
    "category": "Pain Assessment",
    "symptom_type": "pain"
}
```

### Decision Tree Format

```json
{
    "id": 1,
    "symptom_type": "pain",
    "condition": "greater_than",
    "value": 7,
    "intervention_ids": [1, 2]
}
```

## Usage Examples

### Basic Protocol Configuration

```python
import requests
import os
from src.services.protocol_injection import ProtocolInjectionService

# Initialize service
service = ProtocolInjectionService()

# Configure agent for cancer patient
patient_id = 1  # Josh Kerm (Stage IV Lung Cancer)
agent_id = "agent_88609f029da1444efad68581eb"

# Step 1: Prepare agent with cancer protocol
success = service.prepare_agent_for_call(patient_id, agent_id)

if success:
    print("Agent configured successfully with cancer protocol")
    
    # Step 2: Publish agent to activate changes (REQUIRED)
    api_key = os.getenv('RETELLAI_API_KEY')
    publish_response = requests.post(
        f'https://api.retellai.com/publish-agent/{agent_id}',
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        },
        json={},
        timeout=10
    )
    
    if publish_response.status_code == 200:
        print("Agent published successfully - ready for live calls")
        # Proceed with existing call initiation logic
    else:
        print("Failed to publish agent")
else:
    print("Failed to configure agent")
```

### Testing Protocol Injection

```bash
# Dry run test (no agent update)
python scripts/test_protocol_injection.py --patient-id 1

# Live test (updates actual agent LLM)
python scripts/test_protocol_injection.py --live --patient-id 1

# Complete workflow: Update + Publish
# Step 1: Update agent with protocol
python scripts/test_protocol_injection.py --live --patient-id 4

# Step 2: Publish agent to activate changes
python -c "
import requests, os
api_key = os.getenv('RETELLAI_API_KEY')
agent_id = os.getenv('RETELLAI_REMOTE_AGENT_ID')
response = requests.post(f'https://api.retellai.com/publish-agent/{agent_id}',
                        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
                        json={})
print(f'Published: {response.status_code == 200}')
"
```

## Configuration

### Environment Variables

```bash
# Required
RETELLAI_API_KEY=your_retell_api_key
RETELLAI_REMOTE_AGENT_ID=agent_88609f029da1444efad68581eb

# Database
DATABASE_LOCAL_URL=postgresql://user:pass@db:5432/pallcare_db
```

### Agent Configuration

The baseline agent prompt includes:

- Patient verification requirements
- Compassionate, professional tone guidelines
- Two-pathway branching logic (well vs unwell)
- Calendar scheduling integration
- Protocol-specific question injection points

## Error Handling

### Common Issues

1. **Patient Not Found**
   - Returns error with patient ID
   - Logs warning message

2. **Protocol Not Found**
   - Falls back to general protocol if available
   - Logs warning with protocol type

3. **Retell API Errors**
   - Retries with exponential backoff
   - Logs detailed error information
   - Returns false for failure cases

4. **Network Issues**
   - 10-second timeout on API calls
   - Detailed error logging
   - Graceful failure handling

## Testing

### Unit Tests

- Protocol loading validation
- Prompt generation testing  
- Escalation logic verification
- API integration testing

### Integration Tests

- End-to-end protocol injection
- Live agent configuration
- Call flow validation
- Threshold evaluation testing

### Manual Testing

Use the test script for manual validation:

```bash
# Test specific patient with dry run
docker exec retellai-protocol-injection-web-1 python scripts/test_protocol_injection.py --patient-id 1

# Update live agent
docker exec retellai-protocol-injection-web-1 python scripts/test_protocol_injection.py --live --patient-id 1
```

## Monitoring

### Logging

The system provides comprehensive logging:

- **INFO**: Successful operations, agent configurations
- **WARNING**: Fallback scenarios, missing protocols
- **ERROR**: API failures, database errors, configuration issues

### Metrics

Key metrics to monitor:

- Protocol injection success rate
- Agent configuration response times
- Escalation trigger frequency
- Question completion rates

## Security Considerations

### API Security

- Retell AI API key stored in environment variables
- HTTPS-only communication with Retell AI
- Request timeout limits to prevent hanging

### Data Privacy

- Patient information only used for prompt generation
- No sensitive data stored in agent prompts
- Compliance with healthcare data regulations

## Future Enhancements

### Planned Features

1. **Dynamic Protocol Updates**: Real-time protocol modifications
2. **Multi-language Support**: Protocols in multiple languages
3. **Advanced Analytics**: Detailed escalation reporting
4. **Custom Thresholds**: Patient-specific escalation levels
5. **Protocol Versioning**: A/B testing of protocol variations

### Integration Opportunities

- EHR system integration for real-time patient data
- Clinical decision support system integration
- Advanced analytics and reporting dashboards
- Mobile app notifications for nurse escalations

## Agent Publishing

### Programmatic Publishing

After updating LLM prompts, agents must be published to activate changes for live calls:

```python
import requests

def publish_agent(agent_id, api_key):
    """Publish agent to activate prompt changes for live calls"""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(
        f'https://api.retellai.com/publish-agent/{agent_id}',
        headers=headers,
        json={},
        timeout=10
    )
    
    return response.status_code == 200

# Example usage
api_key = os.getenv('RETELLAI_API_KEY')
agent_id = os.getenv('RETELLAI_REMOTE_AGENT_ID')
success = publish_agent(agent_id, api_key)
```

### Publishing Both Agents

Update and publish both LOCAL and REMOTE agents for consistency:

```bash
# Update protocol injection for patient
docker exec retellai-protocol-injection-web-1 python scripts/test_protocol_injection.py --live --patient-id 4

# Publish both agents programmatically
docker exec retellai-protocol-injection-web-1 python -c "
import requests
import os

api_key = os.getenv('RETELLAI_API_KEY')
agents = [
    os.getenv('RETELLAI_LOCAL_AGENT_ID'),
    os.getenv('RETELLAI_REMOTE_AGENT_ID')
]

for agent_id in agents:
    response = requests.post(
        f'https://api.retellai.com/publish-agent/{agent_id}',
        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
        json={}, timeout=10
    )
    print(f'Published {agent_id}: {response.status_code == 200}')
"
```

**Important**: Only published agent versions are used for actual calls. Unpublished changes remain in draft state.

## Troubleshooting

### Common Issues

1. **Agent Not Asking for Date of Birth**
   - **Cause**: Agent not published after protocol injection
   - **Solution**: Publish agent using `POST /publish-agent/{agent_id}`
   - **Verification**: Check `is_published: true` in agent response

2. **Agent Trying to Transfer Calls**
   - **Cause**: Old published version without anti-transfer instruction
   - **Solution**: Update prompt with "DO NOT attempt to transfer" and publish agent
   - **Verification**: Check call transcripts for proper escalation messaging

3. **Agent Using Wrong Questions**
   - **Cause**: Protocol injection worked but agent not published
   - **Solution**: Publish agent after protocol injection
   - **Verification**: Test call should use patient-specific protocol questions

4. **Protocol Questions Missing**
   - Ensure protocol exists in database
   - Verify protocol is marked as active
   - Check patient protocol_type assignment
   - **New**: Verify agent is published after protocol injection

5. **Escalation Logic Not Working**
   - Verify decision tree configuration
   - Check threshold values in database
   - Review prompt generation logs
   - **New**: Ensure agent is published with updated escalation logic

### Debug Commands

```bash
# Check protocol data
python scripts/check_protocols.py

# Inspect protocol structure
python scripts/inspect_protocol_data.py

# Test protocol injection (dry run)
python scripts/test_protocol_injection.py --patient-id 1

# Test protocol injection (live update)
python scripts/test_protocol_injection.py --live --patient-id 1

# Check agent publication status
python -c "
import requests, os
api_key = os.getenv('RETELLAI_API_KEY')
agent_id = os.getenv('RETELLAI_REMOTE_AGENT_ID')
response = requests.get(f'https://api.retellai.com/get-agent/{agent_id}', 
                       headers={'Authorization': f'Bearer {api_key}'})
data = response.json()
print(f'Version: {data.get(\"version\")}, Published: {data.get(\"is_published\")}')
"

# Publish agent after protocol injection
python -c "
import requests, os
api_key = os.getenv('RETELLAI_API_KEY')
agent_id = os.getenv('RETELLAI_REMOTE_AGENT_ID')
response = requests.post(f'https://api.retellai.com/publish-agent/{agent_id}',
                        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
                        json={})
print(f'Published: {response.status_code == 200}')
"
```

## Support

For technical support or questions about the Protocol Injection System:

1. Check the troubleshooting section above
2. Review system logs for error details
3. Test with the provided test scripts
4. Consult the source code documentation

## Changelog

### v1.1.0 (Current)
- **NEW**: Programmatic agent publishing via `POST /publish-agent/{agent_id}` endpoint
- **NEW**: Identity verification with date of birth before protocol questions
- **FIX**: Anti-transfer instruction to prevent unwanted call redirects
- **FIX**: LLM prompt updates now use `general_prompt` field instead of agent prompt
- **FIX**: Agent versioning/caching issues resolved with mandatory publishing
- Enhanced troubleshooting documentation with agent publishing guidance
- Updated debug commands for checking publication status

### v1.0.0
- Initial implementation of protocol injection system
- Support for 4 protocol types (Cancer, Heart Failure, COPD, FIT)
- Three-tier escalation logic (10 min, 1 hour, schedule next)
- Pre-call agent configuration
- Comprehensive testing framework
- Full documentation and examples