# Agencies App

## Overview

Manages organizational structures including agencies, branches, business areas, divisions, departmental services, and affiliations.

## Architecture

Layered architecture with separation of concerns:
- **views/** - HTTP request/response handling
- **services/** - Business logic
- **models.py** - Database models
- **serializers.py** - Data serialization
- **utils/** - Reusable helper functions
- **permissions/** - Authorization logic

## Models

### Affiliation
External user affiliations.
- `name` - Affiliation name (unique)

### Agency
Government agencies.
- `name` - Agency name
- `key_stakeholder` - FK to User
- `is_active` - Active status

### Branch
Agency branches (formerly workcenters).
- `name` - Branch name
- `agency` - FK to Agency
- `manager` - FK to User
- `old_id` - Legacy ID

### BusinessArea
Business areas within agencies (formerly programs).
- `name` - Business area name
- `slug` - URL-safe acronym
- `agency` - FK to Agency
- `division` - FK to Division
- `leader` - FK to User
- `caretaker` - FK to User
- `finance_admin` - FK to User
- `data_custodian` - FK to User
- `focus` - Business area focus (1250 chars)
- `introduction` - Introduction text
- `published` - Published status
- `is_active` - Active status
- `cost_center` - Cost center number

### Division
Department divisions.
- `name` - Division name
- `slug` - URL-safe acronym
- `director` - FK to User
- `approver` - FK to User
- `directorate_email_list` - M2M to User
- `old_id` - Legacy ID

### DepartmentalService
Departmental services.
- `name` - Service name
- `director` - FK to User
- `old_id` - Legacy ID

## API Endpoints

### Affiliations
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/affiliations/` | List affiliations (with search) |
| POST | `/affiliations/` | Create affiliation |
| GET | `/affiliations/<pk>/` | Get affiliation |
| PUT | `/affiliations/<pk>/` | Update affiliation |
| DELETE | `/affiliations/<pk>/` | Delete affiliation (cleans projects) |
| POST | `/affiliations/merge/` | Merge affiliations |
| POST | `/affiliations/clean-orphaned/` | Clean orphaned affiliations |

### Agencies
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/agencies/` | List agencies |
| POST | `/agencies/` | Create agency |
| GET | `/agencies/<pk>/` | Get agency |
| PUT | `/agencies/<pk>/` | Update agency |
| DELETE | `/agencies/<pk>/` | Delete agency |

### Branches
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/branches/` | List branches (with search) |
| POST | `/branches/` | Create branch |
| GET | `/branches/<pk>/` | Get branch |
| PUT | `/branches/<pk>/` | Update branch |
| DELETE | `/branches/<pk>/` | Delete branch |

### Business Areas
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/business-areas/` | List business areas |
| POST | `/business-areas/` | Create business area |
| GET | `/business-areas/<pk>/` | Get business area |
| PUT | `/business-areas/<pk>/` | Update business area |
| DELETE | `/business-areas/<pk>/` | Delete business area |
| GET | `/business-areas/my/` | Get user's business areas |
| POST | `/business-areas/unapproved-docs/` | Get unapproved docs |
| GET/POST | `/business-areas/problematic-projects/` | Get problematic projects |
| POST | `/business-areas/<pk>/set-active/` | Toggle active status |

### Divisions
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/divisions/` | List divisions |
| POST | `/divisions/` | Create division |
| GET | `/divisions/<pk>/` | Get division |
| PUT | `/divisions/<pk>/` | Update division |
| DELETE | `/divisions/<pk>/` | Delete division |
| GET/POST | `/divisions/<pk>/email-list/` | Manage email list |

### Departmental Services
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/services/` | List services |
| POST | `/services/` | Create service |
| GET | `/services/<pk>/` | Get service |
| PUT | `/services/<pk>/` | Update service |
| DELETE | `/services/<pk>/` | Delete service |

## Services

### AgencyService

**Affiliation Operations:**
- `list_affiliations()` - List all affiliations
- `get_affiliation(pk)` - Get affiliation by ID
- `create_affiliation(user, data)` - Create affiliation
- `update_affiliation(pk, user, data)` - Update affiliation
- `delete_affiliation(pk, user)` - Delete affiliation (cleans projects)
- `clean_orphaned_affiliations(user)` - Clean orphaned affiliations

**Agency Operations:**
- `list_agencies()` - List all agencies
- `get_agency(pk)` - Get agency by ID
- `create_agency(user, data)` - Create agency
- `update_agency(pk, user, data)` - Update agency
- `delete_agency(pk, user)` - Delete agency

**Branch Operations:**
- `list_branches()` - List all branches
- `get_branch(pk)` - Get branch by ID
- `create_branch(user, data)` - Create branch
- `update_branch(pk, user, data)` - Update branch
- `delete_branch(pk, user)` - Delete branch

**Business Area Operations:**
- `list_business_areas()` - List all business areas (optimized)
- `get_business_area(pk)` - Get business area by ID
- `create_business_area(user, data)` - Create business area
- `update_business_area(pk, user, data)` - Update business area
- `delete_business_area(pk, user)` - Delete business area
- `set_business_area_active(pk)` - Toggle active status

**Division Operations:**
- `list_divisions()` - List all divisions
- `get_division(pk)` - Get division by ID
- `create_division(user, data)` - Create division
- `update_division(pk, user, data)` - Update division
- `delete_division(pk, user)` - Delete division

**Departmental Service Operations:**
- `list_departmental_services()` - List all services
- `get_departmental_service(pk)` - Get service by ID
- `create_departmental_service(user, data)` - Create service
- `update_departmental_service(pk, user, data)` - Update service
- `delete_departmental_service(pk, user)` - Delete service

## Testing

```bash
cd backend
poetry run python manage.py test agencies
```

## Usage

```python
from agencies.services import AgencyService

# List business areas with optimized queries
business_areas = AgencyService.list_business_areas()

# Get specific business area
ba = AgencyService.get_business_area(pk=1)

# Toggle business area active status
updated_ba = AgencyService.set_business_area_active(pk=1)

# Clean orphaned affiliations
result = AgencyService.clean_orphaned_affiliations(user=request.user)
```

---

**Version**: 2.0  
