# Locations App

Geographic area management for the Science Projects Management System.

## Overview

Manages geographic areas including DBCA districts, DBCA regions, IMCRA, IBRA, and NRM areas.

## Architecture

Follows layered architecture pattern:
- **views/** - HTTP request/response handling
- **services/** - Business logic
- **serializers.py** - Data serialization
- **models.py** - Database models
- **utils/** - Helper functions
- **permissions/** - Authorization logic

## Models

### Area
- `name` - Area name
- `area_type` - Type of area (dbcadistrict, dbcaregion, imcra, ibra, nrm)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/locations/` | GET | List all areas |
| `/api/v1/locations/` | POST | Create area |
| `/api/v1/locations/<id>` | GET | Get area detail |
| `/api/v1/locations/<id>` | PUT | Update area |
| `/api/v1/locations/<id>` | DELETE | Delete area |
| `/api/v1/locations/dbcadistricts` | GET | List DBCA districts |
| `/api/v1/locations/dbcaregions` | GET | List DBCA regions |
| `/api/v1/locations/imcras` | GET | List IMCRA areas |
| `/api/v1/locations/ibras` | GET | List IBRA areas |
| `/api/v1/locations/nrms` | GET | List NRM areas |

## Services

### AreaService
- `list_areas(area_type=None)` - List areas with optional type filter
- `get_area(pk)` - Get area by ID
- `create_area(user, data)` - Create new area
- `update_area(pk, user, data)` - Update area
- `delete_area(pk, user)` - Delete area

## Testing

```bash
poetry run python manage.py test locations
```

## Usage

```python
from locations.services import AreaService
from locations.serializers import AreaSerializer

# List all areas
areas = AreaService.list_areas()

# List areas by type
districts = AreaService.list_areas(area_type="dbcadistrict")

# Get specific area
area = AreaService.get_area(pk=1)

# Create area
area = AreaService.create_area(user, {
    'name': 'Perth District',
    'area_type': 'dbcadistrict'
})
```
