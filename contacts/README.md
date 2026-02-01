# Contacts App

Contact management for addresses, agencies, branches, and users.

## Overview

Manages contact information including addresses, agency contacts, branch contacts, and user contacts.

## Architecture

Follows layered architecture pattern:
- **views/** - HTTP request/response handling
- **services/** - Business logic
- **serializers.py** - Data serialization
- **models.py** - Database models
- **utils/** - Helper functions
- **permissions/** - Authorization logic

## Models

### Address
- Physical address information

### AgencyContact
- Contact information for external agencies

### BranchContact
- Contact information for DBCA branches

### UserContact
- Contact information for users

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/contacts/addresses` | GET | List addresses |
| `/api/v1/contacts/addresses` | POST | Create address |
| `/api/v1/contacts/addresses/<id>` | GET | Get address |
| `/api/v1/contacts/addresses/<id>` | PUT | Update address |
| `/api/v1/contacts/addresses/<id>` | DELETE | Delete address |
| `/api/v1/contacts/agency_contacts` | GET | List agency contacts |
| `/api/v1/contacts/agency_contacts` | POST | Create agency contact |
| `/api/v1/contacts/agency_contacts/<id>` | GET | Get agency contact |
| `/api/v1/contacts/agency_contacts/<id>` | PUT | Update agency contact |
| `/api/v1/contacts/agency_contacts/<id>` | DELETE | Delete agency contact |
| `/api/v1/contacts/branch_contacts` | GET | List branch contacts |
| `/api/v1/contacts/branch_contacts` | POST | Create branch contact |
| `/api/v1/contacts/branch_contacts/<id>` | GET | Get branch contact |
| `/api/v1/contacts/branch_contacts/<id>` | PUT | Update branch contact |
| `/api/v1/contacts/branch_contacts/<id>` | DELETE | Delete branch contact |
| `/api/v1/contacts/user_contacts` | GET | List user contacts |
| `/api/v1/contacts/user_contacts` | POST | Create user contact |
| `/api/v1/contacts/user_contacts/<id>` | GET | Get user contact |
| `/api/v1/contacts/user_contacts/<id>` | PUT | Update user contact |
| `/api/v1/contacts/user_contacts/<id>` | DELETE | Delete user contact |

## Services

### ContactService
- `list_addresses()` - List all addresses
- `get_address(pk)` - Get address by ID
- `create_address(user, data)` - Create address
- `update_address(pk, user, data)` - Update address
- `delete_address(pk, user)` - Delete address
- `list_agency_contacts()` - List agency contacts
- `get_agency_contact(pk)` - Get agency contact
- `create_agency_contact(user, data)` - Create agency contact
- `update_agency_contact(pk, user, data)` - Update agency contact
- `delete_agency_contact(pk, user)` - Delete agency contact
- `list_branch_contacts()` - List branch contacts
- `get_branch_contact(pk)` - Get branch contact
- `create_branch_contact(user, data)` - Create branch contact
- `update_branch_contact(pk, user, data)` - Update branch contact
- `delete_branch_contact(pk, user)` - Delete branch contact
- `list_user_contacts()` - List user contacts
- `get_user_contact(pk)` - Get user contact
- `create_user_contact(user, data)` - Create user contact
- `update_user_contact(pk, user, data)` - Update user contact
- `delete_user_contact(pk, user)` - Delete user contact

## Testing

```bash
poetry run python manage.py test contacts
```

## Usage

```python
from contacts.services import ContactService

# Create address
address = ContactService.create_address(user, {
    'street': '123 Main St',
    'city': 'Perth',
    'state': 'WA',
    'postcode': '6000'
})

# Create agency contact
contact = ContactService.create_agency_contact(user, {
    'name': 'Department of Environment',
    'email': 'contact@environment.gov.au'
})
```

---

**Version**: 1.0.0
