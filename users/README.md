# Users App

Manages users, authentication, and staff profiles in the Science Projects Management System.

## Overview

The users app handles user authentication, user management, staff profiles, and related functionality.

## Architecture

**Layered Structure:**
- `views/` - HTTP request/response handling (8 files)
- `services/` - Business logic and transactions (5 files)
- `serializers/` - Data validation and serialization (5 files)
- `permissions/` - Authorization logic
- `utils/` - Reusable helper functions

## Models

### User

Django's built-in User model extended with custom fields.

**Key Fields:**
- `username` - Unique username
- `email` - Email address
- `first_name`, `last_name` - Name fields
- `display_first_name`, `display_last_name` - Display names
- `is_active`, `is_staff`, `is_superuser` - Status flags

### UserProfile

User profile information.

**Fields:**
- `user` - One-to-one with User
- `title` - Job title
- `expertise` - Areas of expertise
- `about` - About text

### PublicStaffProfile

Public-facing staff profile.

**Fields:**
- `user` - One-to-one with User
- `about` - About text
- `expertise` - Expertise areas
- `public` - Public visibility flag
- `is_active` - Active status
- `custom_title`, `custom_title_on` - Custom title override
- `public_email`, `public_email_on` - Public email override

### EmploymentEntry

Employment history entry.

**Fields:**
- `profile` - Foreign key to PublicStaffProfile
- `position` - Job position
- `organisation` - Organization name
- `start_year`, `end_year` - Employment period

### EducationEntry

Education history entry.

**Fields:**
- `profile` - Foreign key to PublicStaffProfile
- `qualification` - Qualification name
- `institution` - Institution name
- `year` - Year obtained

### UserWork

User work/membership information.

**Fields:**
- `user` - One-to-one with User
- `title` - Job title
- `business_area` - Foreign key to BusinessArea
- `affiliation` - Foreign key to Affiliation
- `branch` - Foreign key to Branch

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/users/login/` | User login |
| POST | `/api/v1/users/logout/` | User logout |
| PUT | `/api/v1/users/change-password/` | Change password |

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/users/` | List users |
| POST | `/api/v1/users/` | Create user |
| GET | `/api/v1/users/{id}/` | Get user detail |
| PUT | `/api/v1/users/{id}/` | Update user |
| DELETE | `/api/v1/users/{id}/` | Delete user |
| GET | `/api/v1/users/me/` | Get current user |

### Staff Profiles
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/staff-profiles/` | List staff profiles |
| POST | `/api/v1/staff-profiles/` | Create staff profile |
| GET | `/api/v1/staff-profiles/{id}/` | Get profile detail |
| PUT | `/api/v1/staff-profiles/{id}/` | Update profile |
| DELETE | `/api/v1/staff-profiles/{id}/` | Delete profile |
| GET | `/api/v1/staff-profiles/my/` | Get my profile |
| POST | `/api/v1/staff-profiles/{id}/toggle-visibility/` | Toggle visibility |

### Profile Entries
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/staff-profiles/{id}/employment/` | List employment |
| POST | `/api/v1/staff-profiles/{id}/employment/` | Create employment |
| GET | `/api/v1/employment/{id}/` | Get employment detail |
| PUT | `/api/v1/employment/{id}/` | Update employment |
| DELETE | `/api/v1/employment/{id}/` | Delete employment |
| GET | `/api/v1/staff-profiles/{id}/education/` | List education |
| POST | `/api/v1/staff-profiles/{id}/education/` | Create education |
| GET | `/api/v1/education/{id}/` | Get education detail |
| PUT | `/api/v1/education/{id}/` | Update education |
| DELETE | `/api/v1/education/{id}/` | Delete education |

## Services

### UserService

Handles user operations.

**Methods:**
- `authenticate_user(username, password)` - Authenticate user
- `login_user(request, user)` - Log in user
- `logout_user(request)` - Log out user
- `change_password(user, old_password, new_password)` - Change password
- `list_users(filters, search)` - List users
- `get_user(user_id)` - Get user by ID
- `create_user(data)` - Create user
- `update_user(user_id, data)` - Update user
- `delete_user(user_id)` - Delete user
- `toggle_active(user_id)` - Toggle active status
- `switch_admin(user_id)` - Toggle admin status

### ProfileService

Handles profile operations.

**Methods:**
- `list_staff_profiles(filters, search)` - List staff profiles
- `get_staff_profile(profile_id)` - Get profile by ID
- `create_staff_profile(user_id, data)` - Create profile
- `update_staff_profile(profile_id, data)` - Update profile
- `delete_staff_profile(profile_id)` - Delete profile
- `toggle_visibility(profile_id)` - Toggle visibility

### EmploymentService / EducationService

Handle employment and education entries.

**Methods:**
- `list_employment/education(profile_id)` - List entries
- `get_employment/education(entry_id)` - Get entry
- `create_employment/education(profile_id, data)` - Create entry
- `update_employment/education(entry_id, data)` - Update entry
- `delete_employment/education(entry_id)` - Delete entry

### ExportService

Handles data export.

**Methods:**
- `generate_staff_csv()` - Generate CSV export

## Permissions

### CanManageUser
Users can manage themselves, admins can manage any user.

### CanManageProfile
Users can manage their own profile, admins can manage any.

### CanViewProfile
Public profiles visible to all, private profiles visible to owner and admins.

### CanManageStaffProfile
Users can manage their own staff profile, admins can manage any.

### CanExportData
Only admins can export data.

## Testing

Run tests:
```bash
poetry run python manage.py test users
```

## Usage

### Authenticate User

```python
from users.services import UserService

user = UserService.authenticate_user('username', 'password')
if user:
    UserService.login_user(request, user)
```

### Create Staff Profile

```python
from users.services import ProfileService

profile = ProfileService.create_staff_profile(user_id, {
    'about': 'About text',
    'expertise': 'Expertise areas',
    'public': True,
})
```

### List Users

```python
from users.services import UserService

users = UserService.list_users(
    filters={'is_active': True},
    search='john'
)
```
