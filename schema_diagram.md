# SteadwellOS Palliative Care Database Schema

## Entity Relationship Diagram

```mermaid
erDiagram
    USERS {
        int id PK
        varchar username UK
        varchar email UK
        varchar password
        varchar first_name
        varchar last_name
        userrole role
        varchar phone_number
        varchar license_number
        boolean is_active
        int login_attempts
        timestamp last_login_at
        timestamp created_at
        timestamp updated_at
    }

    PATIENTS {
        int id PK
        varchar mrn UK
        varchar first_name
        varchar last_name
        date date_of_birth
        gender gender
        varchar phone_number
        varchar email
        text address
        varchar primary_diagnosis
        text secondary_diagnoses
        protocoltype protocol_type
        int primary_nurse_id FK
        varchar emergency_contact_name
        varchar emergency_contact_phone
        varchar emergency_contact_relationship
        boolean advance_directive
        boolean dnr_status
        text allergies
        text notes
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    PROTOCOLS {
        int id PK
        varchar name
        text description
        protocoltype protocol_type
        varchar version
        json questions
        json decision_tree
        json interventions
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    CALLS {
        int id PK
        int patient_id FK
        int conducted_by_id FK
        timestamp scheduled_time
        timestamp start_time
        timestamp end_time
        double duration
        callstatus status
        varchar call_type
        varchar twilio_call_sid
        varchar recording_url
        text transcript
        text notes
        timestamp created_at
        timestamp updated_at
    }

    ASSESSMENTS {
        int id PK
        int patient_id FK
        int protocol_id FK
        int conducted_by_id FK
        int call_id FK
        timestamp assessment_date
        json responses
        json symptoms
        json interventions
        text notes
        boolean follow_up_needed
        timestamp follow_up_date
        followuppriority follow_up_priority
        text ai_guidance
        timestamp created_at
        timestamp updated_at
    }

    MEDICATIONS {
        int id PK
        int patient_id FK
        varchar name
        varchar dosage
        varchar dosage_unit
        medicationroute route
        medicationfrequency frequency
        varchar custom_frequency
        varchar indication
        varchar prescriber
        date start_date
        date end_date
        text instructions
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    AUDIT_LOGS {
        int id PK
        int user_id FK
        varchar action
        varchar resource_type
        int resource_id
        json details
        varchar ip_address
        varchar user_agent
        timestamp timestamp
    }

    %% Relationships
    USERS ||--o{ PATIENTS : "primary_nurse_id"
    USERS ||--o{ CALLS : "conducted_by_id"
    USERS ||--o{ ASSESSMENTS : "conducted_by_id"
    USERS ||--o{ AUDIT_LOGS : "user_id"
    
    PATIENTS ||--o{ CALLS : "patient_id"
    PATIENTS ||--o{ ASSESSMENTS : "patient_id"
    PATIENTS ||--o{ MEDICATIONS : "patient_id"
    
    PROTOCOLS ||--o{ ASSESSMENTS : "protocol_id"
    
    CALLS ||--o{ ASSESSMENTS : "call_id"
```

## Key Relationships

### 1. **Users to Patients** (One-to-Many)
- Each patient has one primary nurse
- Each nurse can be assigned to multiple patients
- **FK**: `patients.primary_nurse_id` → `users.id`

### 2. **Patients to Calls** (One-to-Many)
- Each patient can have multiple calls
- Each call belongs to one patient
- **FK**: `calls.patient_id` → `patients.id`

### 3. **Users to Calls** (One-to-Many)
- Each call is conducted by one user (nurse)
- Each user can conduct multiple calls
- **FK**: `calls.conducted_by_id` → `users.id`

### 4. **Patients to Assessments** (One-to-Many)
- Each patient can have multiple assessments
- Each assessment belongs to one patient
- **FK**: `assessments.patient_id` → `patients.id`

### 5. **Protocols to Assessments** (One-to-Many)
- Each assessment uses one protocol
- Each protocol can be used in multiple assessments
- **FK**: `assessments.protocol_id` → `protocols.id`

### 6. **Users to Assessments** (One-to-Many)
- Each assessment is conducted by one user
- Each user can conduct multiple assessments
- **FK**: `assessments.conducted_by_id` → `users.id`

### 7. **Calls to Assessments** (One-to-Many)
- Each assessment can optionally be linked to a call
- Each call can have multiple assessments
- **FK**: `assessments.call_id` → `calls.id`

### 8. **Patients to Medications** (One-to-Many)
- Each patient can have multiple medications
- Each medication belongs to one patient
- **FK**: `medications.patient_id` → `patients.id`

### 9. **Users to Audit Logs** (One-to-Many)
- Each audit log entry is created by one user
- Each user can have multiple audit log entries
- **FK**: `audit_logs.user_id` → `users.id`

## Enum Types

### UserRole
- `nurse`
- `administrator`
- `patient`

### Gender
- `male`
- `female`
- `other`

### ProtocolType
- `cancer`
- `heart_failure`
- `copd`
- `general`

### CallStatus
- `scheduled`
- `in_progress`
- `completed`
- `missed`
- `cancelled`

### FollowUpPriority
- `low`
- `medium`
- `high`
- `urgent`

### MedicationRoute
- `oral`
- `iv`
- `im`
- `sc`
- `topical`
- `inhalation`
- `other`

### MedicationFrequency
- `once_daily`
- `twice_daily`
- `three_times_daily`
- `four_times_daily`
- `as_needed`
- `custom`

## Data Flow

1. **Patient Registration**: Patients are created and assigned to a primary nurse
2. **Protocol Selection**: Based on patient's condition, appropriate protocols are selected
3. **Call Scheduling**: Calls are scheduled for patient check-ins
4. **Assessment Execution**: During calls, assessments are conducted using protocols
5. **Medication Management**: Patient medications are tracked and managed
6. **Audit Trail**: All actions are logged in audit_logs for compliance

## JSON Fields

### Assessments
- **responses**: Patient responses to protocol questions
- **symptoms**: Recorded symptoms with severity scores
- **interventions**: Recommended actions and interventions

### Protocols
- **questions**: Assessment questions for the protocol
- **decision_tree**: Logic for determining next steps
- **interventions**: Available interventions for the protocol

### Audit Logs
- **details**: Additional context about the logged action