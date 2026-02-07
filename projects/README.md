# Projects App

Django app for managing science projects, including core function, science, student, and external projects.

## Architecture

Layered architecture with clear separation of concerns:

```
projects/
├── models.py              # Data models
├── views/                 # HTTP request/response (to be refactored)
├── serializers/           # Data serialization
│   ├── base.py           # Core project serializers
│   ├── details.py        # Project details serializers
│   ├── members.py        # Team member serializers
│   ├── areas.py          # Location/area serializers
│   └── export.py         # CSV export serializers
├── services/              # Business logic
│   ├── project_service.py    # Core project operations
│   ├── member_service.py     # Team management
│   ├── details_service.py    # Project details management
│   ├── area_service.py       # Location management
│   └── export_service.py     # CSV exports
├── utils/                 # Reusable utilities
│   ├── filters.py        # Query filtering
│   ├── helpers.py        # Helper functions
│   └── files.py          # File operations
└── permissions/           # Authorization
    └── project_permissions.py
```

## Models

### Project
Core project model with fields:
- `kind`: Project type (science, student, external, core_function)
- `status`: Project status (new, pending, active, completed, etc.)
- `year`, `number`: Project identification
- `title`, `description`, `tagline`, `keywords`: Project information
- `start_date`, `end_date`: Project timeline
- `business_area`: Related business area

### ProjectDetail
Additional project details:
- `creator`, `modifier`, `owner`: User relationships
- `data_custodian`, `site_custodian`: Custodian roles
- `service`: Departmental service

### StudentProjectDetails
Student-specific details:
- `level`: Academic level (PhD, MSc, Honours, etc.)
- `organisation`: Academic institution

### ExternalProjectDetails
External project details:
- `collaboration_with`: Partner organizations
- `budget`: Project budget
- `description`, `aims`: Project information

### ProjectMember
Team membership:
- `user`: Team member
- `is_leader`: Leadership flag
- `role`: Member role (supervising, research, technical, etc.)
- `time_allocation`: FTE allocation
- `position`: Display order

### ProjectArea
Project locations:
- `areas`: Array of location IDs

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/projects/` | List projects with filters |
| POST | `/api/projects/` | Create project |
| GET | `/api/projects/<id>` | Get project details |
| PUT | `/api/projects/<id>` | Update project |
| DELETE | `/api/projects/<id>` | Delete project |
| GET | `/api/projects/map` | Get projects for map view |
| GET | `/api/projects/mine` | Get user's projects |
| GET | `/api/projects/<id>/team` | Get project team |
| POST | `/api/projects/project_members` | Add team member |
| DELETE | `/api/projects/project_members/<project_id>/<user_id>` | Remove member |
| POST | `/api/projects/promote` | Promote member to leader |
| GET | `/api/projects/download` | Export all projects CSV |
| GET | `/api/projects/download-ar` | Export annual report projects CSV |

## Services

### ProjectService
Core project operations:
- `list_projects(user, filters)` - List with filtering and N+1 optimization
- `get_project(pk)` - Get single project
- `create_project(user, data)` - Create new project
- `update_project(pk, user, data)` - Update project
- `delete_project(pk, user)` - Delete project
- `suspend_project(pk, user)` - Suspend project
- `toggle_user_profile_visibility(pk, user)` - Toggle profile visibility

### MemberService
Team management:
- `list_members(project_id, user_id)` - List members
- `get_member(project_id, user_id)` - Get specific member
- `add_member(project_id, user_id, data, user)` - Add member
- `update_member(project_id, user_id, data, user)` - Update member
- `remove_member(project_id, user_id, user)` - Remove member
- `promote_to_leader(project_id, user_id, user)` - Promote to leader

### DetailsService
Project details management:
- `get_project_details(project_id)` - Get base details
- `get_student_details(project_id)` - Get student details
- `get_external_details(project_id)` - Get external details
- `create_project_details(project_id, data, user)` - Create details
- `update_project_details(project_id, data, user)` - Update details

### AreaService
Location management:
- `get_project_area(project_id)` - Get project areas
- `create_project_area(project_id, area_ids, user)` - Create areas
- `update_project_area(project_id, area_ids, user)` - Update areas

### ExportService
CSV exports:
- `export_all_projects_csv(user)` - Export all projects
- `export_annual_report_projects_csv(user)` - Export AR projects

## Permissions

- `CanViewProject` - All authenticated users
- `CanEditProject` - Project leaders and superusers
- `CanManageProjectMembers` - Project leaders and superusers
- `IsProjectLeader` - Project leaders only
- `IsProjectMember` - Project members only

## Usage

### Creating a Project

```python
from projects.services import ProjectService

project = ProjectService.create_project(
    user=request.user,
    data={
        'kind': 'science',
        'year': 2024,
        'title': 'My Project',
        'description': 'Project description',
        'business_area': 1,
    }
)
```

### Listing Projects with Filters

```python
from projects.services import ProjectService

projects = ProjectService.list_projects(
    user=request.user,
    filters={
        'searchTerm': 'CF-2024',
        'projectstatus': 'active',
        'businessarea': '1',
    }
)
```

### Managing Team Members

```python
from projects.services import MemberService

# Add member
member = MemberService.add_member(
    project_id=1,
    user_id=2,
    data={'role': 'research', 'is_leader': False},
    requesting_user=request.user
)

# Promote to leader
MemberService.promote_to_leader(
    project_id=1,
    user_id=2,
    requesting_user=request.user
)
```

## Testing

Run tests:
```bash
cd backend
poetry run python manage.py test projects
```
