# SteadywellOS API Documentation

This document provides details about the RESTful API endpoints available in the SteadywellOS palliative care coordination platform.

## Authentication

All API endpoints (except authentication endpoints) require a valid JWT token in the Authorization header.

```
Authorization: Bearer <your_jwt_token>
```

### Login

**Endpoint**: `POST /api/v1/auth/login`

**Request body**:
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

**Response**:
```json
{
  "access_token": "jwt_token_here",
  "token_type": "Bearer",
  "expires_in": 86400,
  "refresh_token": "refresh_token_here",
  "user": {
    "id": 1,
    "username": "your_username",
    "email": "your_email@example.com",
    "full_name": "Your Name",
    "role": "nurse"
  }
}
```

### Refresh Token

**Endpoint**: `POST /api/v1/auth/refresh`

**Request headers**:
```
Authorization: Bearer <your_refresh_token>
```

**Response**:
```json
{
  "access_token": "new_jwt_token_here",
  "token_type": "Bearer",
  "expires_in": 86400
}
```

### Logout

**Endpoint**: `POST /api/v1/auth/logout`

**Request headers**:
```
Authorization: Bearer <your_jwt_token>
```

**Response**: `200 OK`

## User Management

### Get All Users

**Endpoint**: `GET /api/v1/users/`

**Permissions**: Admin only

**Response**:
```json
[
  {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "full_name": "Admin User",
    "role": "admin",
    "is_active": true
  },
  {
    "id": 2,
    "username": "nurse1",
    "email": "nurse1@example.com",
    "full_name": "Jane Smith",
    "role": "nurse",
    "is_active": true
  }
]
```

### Get User by ID

**Endpoint**: `GET /api/v1/users/:id`

**Permissions**: Admin or self

**Response**:
```json
{
  "id": 2,
  "username": "nurse1",
  "email": "nurse1@example.com",
  "full_name": "Jane Smith",
  "role": "nurse",
  "phone_number": "555-123-4567",
  "license_number": "RN12345",
  "is_active": true,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

### Create User

**Endpoint**: `POST /api/v1/users/`

**Permissions**: Admin only

**Request body**:
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "secure_password",
  "first_name": "New",
  "last_name": "User",
  "role": "nurse",
  "phone_number": "555-987-6543",
  "license_number": "RN54321"
}
```

**Response**: Same as Get User

### Update User

**Endpoint**: `PUT /api/v1/users/:id`

**Permissions**: Admin or self

**Request body**: (all fields optional)
```json
{
  "email": "updated@example.com",
  "first_name": "Updated",
  "last_name": "Name",
  "phone_number": "555-555-5555"
}
```

**Response**: Same as Get User

### Activate/Deactivate User

**Endpoint**: `PUT /api/v1/users/:id/activate` or `PUT /api/v1/users/:id/deactivate`

**Permissions**: Admin only

**Response**:
```json
{
  "message": "User username activated/deactivated"
}
```

## Patient Management

### Get All Patients

**Endpoint**: `GET /api/v1/patients/`

**Query parameters**:
- `protocol_type`: Filter by protocol type (cancer, heart_failure, copd)
- `search`: Search by name, MRN, or diagnosis
- `is_active`: Filter by active status (true/false)

**Response**:
```json
[
  {
    "id": 1,
    "mrn": "MRN12345",
    "full_name": "John Doe",
    "age": 72,
    "primary_diagnosis": "Stage IV Lung Cancer",
    "protocol_type": "cancer",
    "primary_nurse": {
      "id": 2,
      "full_name": "Jane Smith"
    },
    "is_active": true
  }
]
```

### Get Patient by ID

**Endpoint**: `GET /api/v1/patients/:id`

**Response**:
```json
{
  "id": 1,
  "mrn": "MRN12345",
  "first_name": "John",
  "last_name": "Doe",
  "date_of_birth": "1950-05-15",
  "gender": "male",
  "phone_number": "555-111-2222",
  "email": "john.doe@example.com",
  "address": "123 Main St, Anytown, USA",
  "primary_diagnosis": "Stage IV Lung Cancer",
  "secondary_diagnoses": "COPD, Hypertension",
  "protocol_type": "cancer",
  "primary_nurse_id": 2,
  "emergency_contact_name": "Jane Doe",
  "emergency_contact_phone": "555-222-3333",
  "emergency_contact_relationship": "Spouse",
  "advance_directive": true,
  "dnr_status": true,
  "allergies": "Penicillin",
  "notes": "Patient prefers morning calls",
  "is_active": true,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z",
  "full_name": "John Doe",
  "age": 72,
  "primary_nurse": {
    "id": 2,
    "full_name": "Jane Smith",
    "email": "nurse1@example.com"
  }
}
```

### Create Patient

**Endpoint**: `POST /api/v1/patients/`

**Permissions**: Admin, Nurse, Physician

**Request body**:
```json
{
  "mrn": "MRN67890",
  "first_name": "Mary",
  "last_name": "Johnson",
  "date_of_birth": "1945-09-20",
  "gender": "female",
  "phone_number": "555-333-4444",
  "email": "mary.johnson@example.com",
  "address": "456 Oak Ave, Somewhere, USA",
  "primary_diagnosis": "Heart Failure NYHA Class IV",
  "secondary_diagnoses": "Diabetes, Chronic Kidney Disease",
  "protocol_type": "heart_failure",
  "primary_nurse_id": 2,
  "emergency_contact_name": "Robert Johnson",
  "emergency_contact_phone": "555-444-5555",
  "emergency_contact_relationship": "Son",
  "advance_directive": true,
  "dnr_status": true,
  "allergies": "Sulfa drugs",
  "notes": "Hard of hearing, speak clearly and loudly"
}
```

**Response**: Same as Get Patient

## Additional Endpoints

Additional endpoints are available for:

- Protocols management
- Assessment creation and retrieval
- Call scheduling and management
- Dashboard statistics

Refer to the API source code for complete details on all available endpoints.
