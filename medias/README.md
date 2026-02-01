# Medias App

Media file management for the Science Projects Management System.

## Overview

Handles image and PDF uploads for projects, annual reports, business areas, agencies, and user avatars.

## Architecture

Layered architecture with separation of concerns:
- **views/** - HTTP request/response handling
- **services/** - Business logic and permission checks
- **models.py** - Database models
- **serializers.py** - Data serialization
- **utils/** - Helper functions
- **permissions/** - Authorization logic

## Models

### Project Documents
- **ProjectDocumentPDF** - PDF files for project documents

### Annual Reports
- **AnnualReportPDF** - Current annual report PDFs
- **LegacyAnnualReportPDF** - Historical annual report PDFs (2005-2019)
- **AnnualReportMedia** - Images for annual report sections (cover, charts, chapters)

### Project Media
- **AECEndorsementPDF** - AEC endorsement PDFs
- **ProjectPhoto** - Project cover images
- **ProjectPlanMethodologyPhoto** - Methodology diagram images

### Organization Media
- **BusinessAreaPhoto** - Business area images
- **AgencyImage** - Agency logo/images

### User Media
- **UserAvatar** - User profile pictures

## API Endpoints

### Project Documents
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/medias/project-docs/` | List all project document PDFs |
| POST | `/api/medias/project-docs/` | Create project document PDF |

### Annual Reports
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/medias/annual-report-pdfs/` | List annual report PDFs |
| POST | `/api/medias/annual-report-pdfs/` | Create annual report PDF |
| GET | `/api/medias/annual-report-pdfs/<pk>/` | Get annual report PDF |
| PUT | `/api/medias/annual-report-pdfs/<pk>/` | Update annual report PDF |
| DELETE | `/api/medias/annual-report-pdfs/<pk>/` | Delete annual report PDF |
| GET | `/api/medias/legacy-annual-report-pdfs/` | List legacy PDFs |
| POST | `/api/medias/legacy-annual-report-pdfs/` | Create legacy PDF |
| GET | `/api/medias/legacy-annual-report-pdfs/<pk>/` | Get legacy PDF |
| PUT | `/api/medias/legacy-annual-report-pdfs/<pk>/` | Update legacy PDF |
| DELETE | `/api/medias/legacy-annual-report-pdfs/<pk>/` | Delete legacy PDF |
| GET | `/api/medias/annual-report-media/` | List annual report media |
| POST | `/api/medias/annual-report-media/` | Create annual report media |
| GET | `/api/medias/annual-report-media/<pk>/` | Get annual report media |
| PUT | `/api/medias/annual-report-media/<pk>/` | Update annual report media |
| DELETE | `/api/medias/annual-report-media/<pk>/` | Delete annual report media |
| GET | `/api/medias/latest-report-media/` | Get latest report's media |
| GET | `/api/medias/annual-report-media-upload/<pk>/` | Get report media by report |
| POST | `/api/medias/annual-report-media-upload/<pk>/` | Upload/update report media |
| DELETE | `/api/medias/annual-report-media-delete/<pk>/<section>/` | Delete report media by section |

### Photos
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/medias/business-area-photos/` | List business area photos |
| POST | `/api/medias/business-area-photos/` | Create business area photo |
| GET | `/api/medias/business-area-photos/<pk>/` | Get business area photo |
| PUT | `/api/medias/business-area-photos/<pk>/` | Update business area photo |
| DELETE | `/api/medias/business-area-photos/<pk>/` | Delete business area photo |
| GET | `/api/medias/project-photos/` | List project photos |
| POST | `/api/medias/project-photos/` | Create project photo |
| GET | `/api/medias/project-photos/<pk>/` | Get project photo |
| PUT | `/api/medias/project-photos/<pk>/` | Update project photo |
| DELETE | `/api/medias/project-photos/<pk>/` | Delete project photo |
| GET | `/api/medias/methodology-photos/` | List methodology photos |
| POST | `/api/medias/methodology-photos/` | Create methodology photo |
| GET | `/api/medias/methodology-photos/<pk>/` | Get methodology photo |
| PUT | `/api/medias/methodology-photos/<pk>/` | Update methodology photo |
| DELETE | `/api/medias/methodology-photos/<pk>/` | Delete methodology photo |
| GET | `/api/medias/agency-photos/` | List agency photos |
| POST | `/api/medias/agency-photos/` | Create agency photo |
| GET | `/api/medias/agency-photos/<pk>/` | Get agency photo |
| PUT | `/api/medias/agency-photos/<pk>/` | Update agency photo |
| DELETE | `/api/medias/agency-photos/<pk>/` | Delete agency photo |

### Avatars
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/medias/user-avatars/` | List user avatars |
| POST | `/api/medias/user-avatars/` | Create user avatar |
| GET | `/api/medias/user-avatars/<pk>/` | Get user avatar |
| PUT | `/api/medias/user-avatars/<pk>/` | Update user avatar |
| DELETE | `/api/medias/user-avatars/<pk>/` | Delete user avatar |

## Services

### MediaService

Business logic for media operations.

**Methods:**
```python
# Project documents
list_project_document_pdfs() -> QuerySet
get_project_document_pdf(pk: int) -> ProjectDocumentPDF
delete_project_document_pdf(pk: int, user: User) -> None

# Annual reports
list_annual_report_pdfs() -> QuerySet
get_annual_report_pdf(pk: int) -> AnnualReportPDF
delete_annual_report_pdf(pk: int, user: User) -> None
list_legacy_annual_report_pdfs() -> QuerySet
get_legacy_annual_report_pdf(pk: int) -> LegacyAnnualReportPDF
delete_legacy_annual_report_pdf(pk: int, user: User) -> None
list_annual_report_media() -> QuerySet
get_annual_report_media(pk: int) -> AnnualReportMedia
get_annual_report_media_by_report_and_kind(report_pk: int, kind: str) -> AnnualReportMedia
delete_annual_report_media(pk: int, user: User) -> None
delete_annual_report_media_by_report_and_kind(report_pk: int, kind: str, user: User) -> None

# Photos
list_business_area_photos() -> QuerySet
get_business_area_photo(pk: int) -> BusinessAreaPhoto
delete_business_area_photo(pk: int, user: User) -> None
list_project_photos() -> QuerySet
get_project_photo(pk: int) -> ProjectPhoto
delete_project_photo(pk: int, user: User) -> None
list_methodology_photos() -> QuerySet
get_methodology_photo_by_project_plan(project_plan_pk: int) -> ProjectPlanMethodologyPhoto
delete_methodology_photo(pk: int, user: User) -> None
list_agency_photos() -> QuerySet
get_agency_photo(pk: int) -> AgencyImage
delete_agency_photo(pk: int, user: User) -> None

# Avatars
list_user_avatars() -> QuerySet
get_user_avatar(pk: int) -> UserAvatar
delete_user_avatar(pk: int, user: User) -> None
```

## Permissions

Permission checks are handled in the service layer:
- **Uploader or superuser** - Can update/delete business area photos, project photos, methodology photos
- **Superuser only** - Can update/delete agency photos
- **Owner or superuser** - Can update/delete user avatars

## Testing

Run tests:
```bash
cd backend
poetry run python manage.py test medias
```

## Usage

### Upload Project Photo
```python
from medias.services import MediaService

# In view
photo = MediaService.get_project_photo(photo_id)
if photo.uploader == request.user or request.user.is_superuser:
    photo.file = new_file
    photo.save()
```

### Get Annual Report Media
```python
from medias.services import MediaService

# Get specific media by report and kind
media = MediaService.get_annual_report_media_by_report_and_kind(
    report_pk=report_id,
    kind='cover'
)
```

---

**Version**: 2.0  
