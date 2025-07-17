SteadywellOS is a comprehensive platform designed for palliative care coordination and remote patient management. It enables healthcare providers to efficiently manage patient assessments, schedule follow-up calls, and implement specialized care protocols for conditions like cancer, heart failure, and COPD.

## 🏛️ System Architecture

```mermaid
classDiagram
    %% Core Application Components
    class Flask {
        +create_app()
    }

    class Config {
        +SECRET_KEY
        +JWT_SECRET_KEY
        +DATABASE_URL
        +RETELLAI_API_KEY
        +ANTHROPIC_API_KEY
        +SENTRY_DSN
    }

    %% Database Models
    class User {
        +id: Integer
        +username: String
        +email: String
        +password: String
        +first_name: String
        +last_name: String
        +role: UserRole
        +phone_number: String
        +is_active: Boolean
        +login_attempts: Integer
        +check_password(password)
        +increment_login_attempts()
        +reset_login_attempts()
        +is_account_locked()
    }

    class Patient {
        +id: Integer
        +mrn: String
        +first_name: String
        +last_name: String
        +date_of_birth: Date
        +gender: Gender
        +primary_diagnosis: String
        +protocol_type: ProtocolType
        +primary_nurse_id: Integer
        +is_active: Boolean
        +full_name()
        +age()
        +last_assessment()
    }

    class Protocol {
        +id: Integer
        +name: String
        +description: Text
        +protocol_type: ProtocolType
        +version: String
        +questions: JSON
        +decision_tree: JSON
        +interventions: JSON
        +is_active: Boolean
        +get_latest_active_protocol(protocol_type)
    }

    class Assessment {
        +id: Integer
        +patient_id: Integer
        +protocol_id: Integer
        +conducted_by_id: Integer
        +call_id: Integer
        +assessment_date: DateTime
        +responses: JSON
        +symptoms: JSON
        +interventions: JSON
        +notes: Text
        +follow_up_needed: Boolean
        +follow_up_priority: FollowUpPriority
        +ai_guidance: Text
        +urgent_symptoms(threshold)
    }

    class Call {
        +id: Integer
        +patient_id: Integer
        +conducted_by_id: Integer
        +scheduled_time: DateTime
        +start_time: DateTime
        +end_time: DateTime
        +duration: Float
        +status: CallStatus
        +call_type: String
        +retell_call_id: String
        +recording_url: String
        +transcript: Text
        +is_overdue()
        +update_status(status)
    }

    %% Services
    class AnthropicClient {
        +call_model(model, prompt, system, messages, max_tokens)
        +get_anthropic_client(api_key)
    }

    class RetellService {
        +get_retell_client()
        +initiate_call(to_number, from_number, call_id, call_type)
        +end_call(retell_call_id)
        +update_webhook_url(agent_id, webhook_url)
    }

    class RAGService {
        +process_assessment(patient, protocol, symptoms, responses)
        +generate_call_script(patient, protocol, call_type)
        +analyze_call_transcript(transcript, patient, protocol)
    }

    %% Relationships
    User "1" -- "*" Patient : primary_nurse
    User "1" -- "*" Assessment : conducted_by
    User "1" -- "*" Call : conducted_by

    Patient "1" -- "*" Assessment : has
    Patient "1" -- "*" Call : has

    Protocol "1" -- "*" Assessment : used_in

    Assessment "0..1" -- "0..1" Call : associated_with

    RAGService --> AnthropicClient : uses
    Call --> RetellService : uses
```

## 🚀 Quick Start

SteadywellOS can be set up and run using the Just command runner or directly using the shell scripts in the `scripts` directory.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- [Just](https://github.com/casey/just#installation) (optional but recommended)
- [1Password CLI](https://developer.1password.com/docs/cli/get-started/) (optional but recommended 1Password secret references)

### Installation Steps

#### Step 1: Set up environment variables

If using just

```bash
cp .env.example .env.secrets
```

If you're going to run scripts manually without just you'll also want to copy `.env.secrets` into `.env`

```bash
cp .env.secrets .env
```

#### Step 2: Install dependencies

**Option 1: Using Just (recommended)**

```bash
# Install dependencies using the just command
just install
```

**Option 2: Manual installation**

```bash
# Install uv (if not already installed)
pip install uv

# Create a virtual environment using uv
uv venv .venv

# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies using uv
uv pip install -r requirements.txt
```

This will:

- Set up a Python virtual environment in the .venv directory
- Install all required dependencies using uv
- Prepare the environment for running the application

**Option 3: PyCharm Setup**

If you're using PyCharm as your IDE, you can configure it to use the local `.venv` virtual environment:

1. See the detailed instructions in [docs/pycharm_setup.md](docs/pycharm_setup.md)
2. This will ensure PyCharm uses the correct Python interpreter and dependencies

**Database Connection in PyCharm**

To connect PyCharm to the Docker PostgreSQL database:

1. Start the Docker containers using `just up` or `docker-compose -f docker-compose-dev.yml up`
2. Follow the instructions in [pycharm_db_connection.md](pycharm_db_connection.md) to configure the database connection
3. You can use the provided test script to verify the connection: `python test_db_connection.py`

#### Step 3: Start the application

```bash
# Using Just (recommended)
just up

# Or using the script directly
./scripts/up.sh
```

This will:

- Build and start all necessary containers
- Configure the application environment
- Make the application available at http://localhost:8081

#### Step 3: Initialize and seed the database

The database is automatically initialized during startup, but you can also do it manually:

```bash
# Using Just
just db-init   # Initialize database schema
just db-seed   # Seed with sample data

# Or using scripts directly
./scripts/db_init.sh
./scripts/db_seed.sh
```

After completing these steps, the platform will be available at http://localhost:8081

## 🔑 Default Login Credentials

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

## 📁 Project Structure

The project is organized into the following directories:

- `app/` - Main application code
  - `api/` - API endpoints and routes
  - `models/` - Database models
  - `schemas/` - Pydantic schemas for validation
  - `services/` - Business logic and external services
  - `static/` - Static assets (CSS, JS)
  - `templates/` - HTML templates
  - `utils/` - Utility functions
- `config/` - Configuration files
- `data/` - Data files and backups
- `docs/` - Documentation files
- `logs/` - Log files
- `scripts/` - Utility scripts
  - `obsolete/` - Deprecated scripts
- `tests/` - Test files

## 🧰 Key Scripts

| Script                            | Purpose                               | When to Use                         |
| --------------------------------- | ------------------------------------- | ----------------------------------- |
| `scripts/install.sh`              | Initial setup and dependency checks   | First-time setup                    |
| `scripts/up.sh`                   | Start application containers          | Starting the application            |
| `scripts/down.sh`                 | Stop application containers           | Shutting down the application       |
| `scripts/db_reset.sh`             | Reset database to clean state         | When database is corrupted          |
| `scripts/db_seed.sh`              | Populate database with sample data    | After database initialization       |
| `scripts/db_backup.sh`            | Create database backups               | Before changes or regularly         |
| `scripts/db_reset_from_backup.sh` | Restore database from backup          | After failure or to revert changes  |
| `scripts/protocol_ingest.py`      | Initialize clinical protocols         | During setup or updating protocols  |
| `scripts/upgrade_anthropic.sh`    | Update Anthropic library              | When API compatibility issues arise |
| `scripts/push_to_dockerhub.sh`    | Build and push container to DockerHub | When deploying new versions         |
| `scripts/push_to_quome.sh`        | Deploy container to Quome             | When deploying to production        |
| `run.py`                          | Main application entry point          | Various database operations         |

## 🛠️ Available Commands

The following commands are available through the Just command runner:

| Command                  | Description                                                      |
| ------------------------ | ---------------------------------------------------------------- |
| `just install`           | Install dependencies using uv                                    |
| `just dev`               | Quick development setup (build and start)                        |
| `just prod`              | Quick production test setup                                      |
| `just up`                | Start the development environment                                |
| `just up-dev`            | Start development environment with logs                          |
| `just up-prod`           | Start production test environment                                |
| `just down`              | Stop all containers                                              |
| `just logs`              | View application logs                                            |
| `just ps`                | Show container status                                            |
| `just shell`             | Start shell in web container                                     |
| `just db`                | Connect to PostgreSQL database                                   |
| `just db-reset`          | Reset database (development)                                     |
| `just status`            | Show deployment status                                           |
| `just test-api`          | Test API endpoints                                               |
| `just test-webhook`      | Test webhook endpoint                                            |
| `just build-dev`         | Build development containers                                      |
| `just build-prod`        | Build production containers                                       |
| `just build-all`         | Build both environments                                          |
| `just deploy`            | Deploy to Quome Cloud                                            |
| `just logs-quome`        | Check Quome Cloud logs                                           |
| `just clean`             | Clean all Docker resources                                       |
| `just help`              | Show help information                                            |

### Protocol Initialization

The system includes specialized care protocols for different conditions:

```bash
# Initialize all protocol types
just protocols

# Initialize a specific protocol type
just protocols cancer
just protocols heart_failure
just protocols copd
```

Each protocol includes:

- Structured assessment questions
- Recommended interventions based on symptoms
- Decision tree logic for determining appropriate care actions

## ✨ Features

- **Secure Authentication**: Role-based access control with secure login and auto-logout for healthcare providers
- **DOB Verification System**: Mandatory date-of-birth verification before any health information is shared during calls
- **Protocol-Based Care**: Specialized protocols for cancer, heart failure, and COPD patients
- **Telephony Integration**: Automated calls, voice assessments, and transcription via Retell.ai
- **AI-Powered Guidance**: Uses RAG models to analyze patient information and suggest interventions
- **HIPAA-Compliant**: Secure handling of sensitive patient data with audit logging
- **Comprehensive Dashboard**: Real-time overview of patient status and upcoming tasks
- **Error Tracking**: Production error monitoring with Sentry integration
- **Auto-Webhook Configuration**: Automatic webhook URL updates for local/production environments

### 🔒 DOB Verification Security

The platform implements a robust DOB verification system to protect patient privacy:

- **Mandatory Verification**: All calls require successful date-of-birth confirmation before health discussions
- **Immediate Call Termination**: Incorrect DOB results in automatic call disconnection
- **Dynamic Variable Injection**: Patient-specific data is injected at call time using Retell AI's dynamic variables
- **Multiple Format Support**: Accepts various date formats (MM/DD/YYYY, spelled out, abbreviated)
- **No Information Leakage**: Agent never reveals correct DOB when verification fails
- **Protocol Integration**: Works seamlessly with all care protocols (cancer, heart failure, COPD)

For detailed technical information, see [DOB Verification System Documentation](docs/dob-verification-system.md).

## 🔧 Technology Stack

- **Backend**: Python 3.10 with Flask framework
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Frontend**: HTML/CSS/JavaScript with Bootstrap 5
- **API**: RESTful API with JWT authentication
- **AI Integration**: Anthropic Claude for protocol guidance
- **Telephony**: Retell.ai for voice calls and transcription
- **Error Tracking**: Sentry for production monitoring
- **Deployment**: Docker containerization with Quome Cloud support

## 🔐 Environment Variables

Key environment variables to configure:

### Core Application
- `FLASK_APP`: Set to `run.py`
- `FLASK_ENV`: Set to `development` or `production`
- `SECRET_KEY`: Application secret key for security
- `DATABASE_URL`: PostgreSQL connection string

### Integrations
- `ANTHROPIC_API_KEY`: API key for Claude AI integration
- `RETELLAI_API_KEY`: API key for Retell.ai telephony
- `RETELLAI_LOCAL_AGENT_ID`: Agent ID for local development
- `RETELLAI_REMOTE_AGENT_ID`: Agent ID for production
- `RETELLAI_PHONE_NUMBER`: Phone number for outgoing calls

### Error Tracking (Optional)
- `SENTRY_DSN`: Sentry DSN for error tracking
- `SENTRY_TRACES_SAMPLE_RATE`: Performance monitoring sample rate (0.0-1.0)
- `ENVIRONMENT`: Current environment (development/staging/production)
- `APP_VERSION`: Application version for tracking releases

## 📡 API Documentation

The application provides a RESTful API with the following main endpoints:

- `POST /api/v1/auth/login`: Authenticate and receive JWT token
- `GET /api/v1/patients`: List all patients
- `GET /api/v1/patients/:id`: Get patient details
- `POST /api/v1/calls`: Schedule a new call
- `POST /api/v1/assessments`: Create a new patient assessment

Refer to the full API documentation in the `/docs` directory.

## 📋 Protocols

SteadwellOS comes with three specialized protocols:

1. **Cancer Palliative Care Protocol**: Pain management, nausea control, and fatigue assessments
2. **Heart Failure Protocol**: Dyspnea, edema, and activity tolerance evaluations
3. **COPD Protocol**: Respiratory symptoms, oxygen use, and breathing technique assessments

Each protocol includes:

- Structured question sets for telephone assessments
- Severity rating systems for symptoms
- Decision tree algorithms for intervention recommendations
- Educational materials for patients and caregivers

## 👨‍💻 Development

To modify the platform:

1. Stop the containers: `docker-compose down`
2. Make your changes
3. Rebuild and restart: `docker-compose up -d --build`

## 📄 License

This project is licensed under the MIT License—see the LICENSE file for details.

## 🙏 Acknowledgments

- Palliative care specialists who provided domain expertise
- Telephone triage protocol references
- Anthropic for AI capabilities
- Twilio for telephony integration
