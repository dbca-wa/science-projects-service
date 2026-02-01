# Caretakers App

Manages caretaker relationships in the Science Projects Management System.

## Overview

The caretaker system allows users to temporarily manage projects and documents on behalf of other users who are on leave or unavailable.

## Architecture

**Layered Structure:**
- `views/` - HTTP request/response handling
- `services/` - Business logic and transactions
- `serializers/` - Data validation and serialization
- `permissions/` - Authorization logic
- `utils/` - Reusable helper functions

## Models

### Caretaker

Represents a caretaker relationship between two users.

**Fields:**
- `user` - User being caretaken for
- `caretaker` - User acting as caretaker
- `start_date` - When caretaking starts
- `end_date` - When caretaking ends (nullable)
- `reason` - Reason for caretaking
- `created_at` - Creation timestamp

**Related Names:**
- `user.caretakers` - All caretakers for this user
- `caretaker.caretaking_for` - All users this user is caretaking for

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/caretakers/` | List caretakers |
| POST | `/api/v1/caretakers/` | Create caretaker |
| GET | `/api/v1/caretakers/{id}` | Get caretaker detail |
| PUT | `/api/v1/caretakers/{id}` | Update caretaker |
| DELETE | `/api/v1/caretakers/{id}` | Remove caretaker |
| GET | `/api/v1/caretakers/requests/` | Get pending requests |
| POST | `/api/v1/caretakers/requests/{id}/approve/` | Approve request |
| POST | `/api/v1/caretakers/requests/{id}/reject/` | Reject request |
| GET | `/api/v1/caretakers/check/` | Check caretaker status |
| POST | `/api/v1/caretakers/admin-set/` | Admin set caretaker |

## Services

### CaretakerService

Handles caretaker CRUD operations.

**Methods:**
- `list_caretakers(filters)` - List with optional filters
- `get_caretaker(caretaker_id)` - Get by ID
- `create_caretaker(data)` - Create new caretaker
- `update_caretaker(caretaker_id, data)` - Update existing
- `delete_caretaker(caretaker_id)` - Delete caretaker

### RequestService

Handles caretaker request workflows.

**Methods:**
- `get_pending_requests(user_id)` - Get pending requests for user
- `approve_request(task_id, user)` - Approve caretaker request
- `reject_request(task_id, user)` - Reject caretaker request
- `check_caretaker_status(user)` - Check user's caretaker status

### TaskService

Integrates with AdminTask system.

**Methods:**
- `admin_set_caretaker(user_pk, caretaker_pk, reason)` - Admin creates caretaker

## Permissions

### CanManageCaretaker

Users can manage caretakers if:
- They are the caretaker themselves
- They are the user being caretaken for
- They are an admin

### CanRespondToCaretakerRequest

Users can respond to requests if:
- They are the requested caretaker
- They are an admin

## Validation Rules

1. Cannot caretake for yourself
2. Cannot create duplicate caretaker relationships
3. End date must be after start date (if provided)

## Testing

Run tests:
```bash
poetry run python manage.py test caretakers
```

**Coverage:** 61 tests covering models, serializers, views, and integration.

## Usage

### Create Caretaker Request

```python
from caretakers.services import CaretakerService

caretaker = CaretakerService.create_caretaker({
    'user': user_id,
    'caretaker': caretaker_id,
    'reason': 'On leave',
    'start_date': '2026-02-01',
    'end_date': '2026-02-15'
})
```

### Approve Request

```python
from caretakers.services import RequestService

RequestService.approve_request(task_id, approving_user)
```

### Check Status

```python
from caretakers.services import RequestService

status = RequestService.check_caretaker_status(user)
```

---

