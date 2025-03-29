# SteadywellOS - Palliative Care Coordination Platform

SteadywellOS is a comprehensive platform designed for palliative care coordination and remote patient management. It enables healthcare providers to efficiently manage patient assessments, schedule follow-up calls, and implement specialized care protocols for conditions like cancer, heart failure, and COPD.

## Quick Start

To initialize and run the system, use the included `init.sh` script:

```bash
chmod +x init.sh
./init.sh
```

This script will:
1. Check if Docker is running
2. Set up required environment variables
3. Configure Docker Compose
4. Build and start the containers
5. Initialize and seed the database

After initialization, the platform will be available at http://localhost:8080

## Default Login Credentials

The system is seeded with the following test users:

- **Admin**
  - Username: `admin`
  - Password: `password123`

- **Nurse**
  - Username: `nurse1`
  - Password: `password123`

- **Physician**
  - Username: `physician`
  - Password: `password123`

**IMPORTANT:** These are default test credentials. In a production environment, you must change these passwords.

## Features

- **Secure Authentication**: Role-based access control with secure login for healthcare providers
- **Protocol-Based Care**: Specialized protocols for cancer, heart failure, and COPD patients
- **Telephony Integration**: Automated calls, voice assessments, and transcription via Twilio
- **AI-Powered Guidance**: Uses RAG models to analyze patient information and suggest interventions
- **HIPAA-Compliant**: Secure handling of sensitive patient data with audit logging
- **Comprehensive Dashboard**: Real-time overview of patient status and upcoming tasks

## Technology Stack

- **Backend**: Python 3.10 with Flask framework
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Frontend**: HTML/CSS/JavaScript with Bootstrap 5
- **API**: RESTful API with JWT authentication
- **AI Integration**: Anthropic Claude for protocol guidance
- **Telephony**: Twilio API for voice calls and transcription
- **Deployment**: Docker containerization

## Environment Variables

Key environment variables to configure:

- `FLASK_APP`: Set to `run.py`
- `FLASK_ENV`: Set to `development` or `production`
- `SECRET_KEY`: Application secret key for security
- `DATABASE_URL`: PostgreSQL connection string
- `ANTHROPIC_API_KEY`: API key for Claude AI integration
- `TWILIO_ACCOUNT_SID`: Twilio account SID for telephony
- `TWILIO_AUTH_TOKEN`: Twilio authentication token
- `TWILIO_PHONE_NUMBER`: Twilio phone number for outgoing calls

## API Documentation

The application provides a RESTful API with the following main endpoints:

- `POST /api/v1/auth/login`: Authenticate and receive JWT token
- `GET /api/v1/patients`: List all patients
- `GET /api/v1/patients/:id`: Get patient details
- `POST /api/v1/calls`: Schedule a new call
- `POST /api/v1/assessments`: Create a new patient assessment

Refer to the full API documentation in the `/docs` directory.

## Protocols

SteadywellOS comes with three specialized protocols:

1. **Cancer Palliative Care Protocol**: Pain management, nausea control, and fatigue assessments
2. **Heart Failure Protocol**: Dyspnea, edema, and activity tolerance evaluations
3. **COPD Protocol**: Respiratory symptoms, oxygen use, and breathing technique assessments

Each protocol includes:
- Structured question sets for telephone assessments
- Severity rating systems for symptoms
- Decision tree algorithms for intervention recommendations
- Educational materials for patients and caregivers

## Development

To modify the platform:

1. Stop the containers: `docker-compose down`
2. Make your changes
3. Rebuild and restart: `docker-compose up -d --build`

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Palliative care specialists who provided domain expertise
- Telephone triage protocol references
- Anthropic for AI capabilities
- Twilio for telephony integration