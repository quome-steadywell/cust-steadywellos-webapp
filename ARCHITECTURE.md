# SteadywellOS - Architecture Overview

This document provides a comprehensive overview of the SteadywellOS Palliative Care Platform architecture.

## System Architecture

```mermaid
graph TB
    Client[Client Browser]
    LoadBalancer[Load Balancer]
    WebServer[Web Server]
    API[FastAPI Application]
    DB[(PostgreSQL/TimescaleDB)]
    TwilioAPI[Twilio API]
    AnthropicAPI[Anthropic Claude API]
    
    Client --> LoadBalancer
    LoadBalancer --> WebServer
    WebServer --> API
    
    subgraph "Backend Application"
        API --> Routes
        Routes --> AuthAPI[Auth API]
        Routes --> PatientAPI[Patient API]
        Routes --> ProtocolAPI[Protocol API]
        Routes --> AssessmentAPI[Assessment API]
        Routes --> CallAPI[Call API]
        Routes --> DashboardAPI[Dashboard API]
        
        AuthAPI & PatientAPI & ProtocolAPI & AssessmentAPI & CallAPI & DashboardAPI --> Services
        Services --> RAGService[RAG Service]
        Services --> TwilioService[Twilio Service]
        
        AuthAPI & PatientAPI & ProtocolAPI & AssessmentAPI & CallAPI --> Models
        Models --> UserModel[User Model]
        Models --> PatientModel[Patient Model]
        Models --> ProtocolModel[Protocol Model]
        Models --> AssessmentModel[Assessment Model]
        Models --> CallModel[Call Model]
        Models --> MedicationModel[Medication Model]
        Models --> AuditLogModel[Audit Log Model]
    end
    
    RAGService --> AnthropicAPI
    TwilioService --> TwilioAPI
    Models --> DB
```

## Component Details

### Frontend
- HTML, CSS, Bootstrap-based responsive interface
- JavaScript for dynamic interactions
- Rendered templates for views (dashboard, patients, calls, assessments)

### Backend
- Python 3.10 with Flask framework
- RESTful API design with modular components
- JWT-based authentication system
- Role-based access control

### Database
- PostgreSQL with TimescaleDB extension for time-series data
- Models for users, patients, protocols, assessments, calls, and medications
- Audit logging for compliance and security

### External Services
- Twilio API for telephony integration (calls, SMS, recordings)
- Anthropic Claude API for protocol guidance and RAG capabilities

### Security Features
- JWT authentication
- Role-based authorization
- Secure password hashing
- Audit logging of system activities
- HTTPS for all communications

## Data Flow

1. Users authenticate through the web interface
2. User actions trigger API requests to the backend
3. Backend processes requests through appropriate controllers
4. Database operations performed via models
5. External services accessed through service layers
6. Results returned to users through the web interface

## API Structure

The API is organized around resources:
- `/api/auth`: Authentication endpoints
- `/api/patients`: Patient management
- `/api/protocols`: Protocol definitions and management
- `/api/assessments`: Patient assessments
- `/api/calls`: Call scheduling and management
- `/api/dashboard`: Dashboard data aggregation

## Deployment

The application is containerized using Docker with:
- Application container running Flask
- PostgreSQL database container
- Nginx for serving static files and proxying

## Scaling Considerations

- Horizontal scaling of application containers
- Database read replicas for scaling read operations
- In-memory caching for frequently accessed data
- Background task processing for asynchronous operations

## Future Enhancements

- Advanced caching for improved performance
- Distributed rate limiting 
- Message queue for background task processing