# SteadywellOS Setup Guide

This guide provides detailed instructions for setting up and deploying the SteadywellOS palliative care coordination platform.

## Development Environment Setup

### Prerequisites

- Python 3.10 or higher
- PostgreSQL 14 or higher
- Node.js 16+ (optional, for frontend development)
- Git

### Clone the Repository

```bash
git clone https://github.com/your-organization/steadwellos.git
cd steadwellos
```

### Python Virtual Environment

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

### Environment Configuration

1. Copy the example environment file:

```bash
cp .env.example .env
```

2. Edit the `.env` file with your configuration:

```
# Application Settings
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=generate_a_secure_random_key

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/palliative_care_db

# Retell.ai Configuration (for telephony features)
RETELLAI_API_KEY=your_retellai_api_key
RETELLAI_LOCAL_AGENT_ID=your_local_agent_id
RETELLAI_REMOTE_AGENT_ID=your_remote_agent_id
RETELLAI_PHONE_NUMBER=your_retellai_phone_number

# RAG Model Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key

# Sentry Error Tracking (optional)
SENTRY_DSN=your_sentry_dsn_url
SENTRY_TRACES_SAMPLE_RATE=0.1
ENVIRONMENT=development
APP_VERSION=1.0.0
```

### Database Setup

1. Create a PostgreSQL database:

```bash
psql -U postgres
```

```sql
CREATE DATABASE palliative_care_db;
CREATE USER palliative_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE palliative_care_db TO palliative_user;
\q
```

2. Initialize the database:

```bash
# Using Just commands (recommended)
just db-reset

# Or using run.py directly
python run.py db create_tables
```

3. (Optional) Seed the database with initial data:

```bash
# Using Just
just db-seed

# Or using run.py
python run.py db seed
```

### Running the Development Server

Using Docker (recommended):
```bash
# Using Just
just up

# Or using docker-compose directly
docker-compose -f docker-compose-dev.yml up -d
```

The application will be available at http://localhost:8081

Or run locally:
```bash
flask run --debug
```

The application will be available at http://localhost:5000

## Production Deployment

### Docker Deployment

1. Configure production environment variables in `.env`

2. Build and start the Docker containers:

```bash
docker-compose up -d --build
```

3. Initialize the database (first time only):

```bash
docker-compose exec web flask create_db
docker-compose exec web flask seed_db  # Optional
```

### AWS Deployment

#### Prerequisites

- AWS account with appropriate permissions
- AWS CLI installed and configured
- Docker and Docker Compose

#### Deploying with AWS ECS

1. Create an ECR repository for the application:

```bash
aws ecr create-repository --repository-name steadwellos
```

2. Build and push the Docker image:

```bash
aws ecr get-login-password --region your-region | docker login --username AWS --password-stdin your-account-id.dkr.ecr.your-region.amazonaws.com

docker build -t your-account-id.dkr.ecr.your-region.amazonaws.com/steadwellos:latest .

docker push your-account-id.dkr.ecr.your-region.amazonaws.com/steadwellos:latest
```

3. Create ECS task definition, cluster, and service using the AWS Management Console or AWS CLI.

4. Configure RDS PostgreSQL database and add the connection string to environment variables.

#### Security Considerations

- Use AWS Secrets Manager for storing sensitive credentials
- Configure AWS RDS with encryption at rest
- Set up appropriate IAM roles and permissions
- Implement VPC with proper security groups
- Enable AWS WAF for web application firewall protection

## Troubleshooting

### Common Issues

1. **Database Connection Errors**:
   - Verify PostgreSQL is running
   - Check database credentials in `.env`
   - Ensure the database exists and permissions are set correctly

2. **API Authentication Issues**:
   - Ensure the SECRET_KEY is set in `.env`
   - Check that JWT_SECRET_KEY is properly configured
   - Verify the token expiration settings

3. **Twilio Integration Problems**:
   - Verify Twilio credentials are correct
   - Ensure the Twilio phone number is properly configured
   - Check Twilio webhooks configuration

### Logs

In development mode, logs are output to the console.

In production:

```bash
# Check Docker container logs
docker-compose logs -f web

# For AWS deployments
aws logs describe-log-groups
aws logs get-log-events --log-group-name /ecs/steadwellos --log-stream-name your-log-stream
```

## Maintenance

### Database Backups

1. Manual backup:

```bash
pg_dump -U username -d palliative_care_db > backup_$(date +%Y%m%d).sql
```

2. For Docker deployments:

```bash
docker-compose exec db pg_dump -U postgres -d palliative_care_db > backup_$(date +%Y%m%d).sql
```

3. For AWS RDS, configure automated snapshots through the AWS Console.

### Updates and Upgrades

1. Pull the latest code:

```bash
git pull origin main
```

2. Install any new dependencies:

```bash
uv pip install -r requirements.txt
```

3. Apply database migrations if any:

```bash
flask db upgrade
```

4. Restart the application:

```bash
# For Docker deployments
docker-compose restart web
```
