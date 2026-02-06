# Documents App

Django app for managing project documents, annual reports, and approval workflows.

## Architecture

Layered architecture with clear separation of concerns:

```
documents/
├── models.py                    # Data models
├── views/                       # HTTP request/response
│   ├── crud.py                 # Base document CRUD
│   ├── approval.py             # Approval workflows
│   ├── pdf.py                  # PDF generation
│   ├── concept_plan.py         # Concept plans
│   ├── project_plan.py         # Project plans
│   ├── progress_report.py      # Progress reports
│   ├── student_report.py       # Student reports
│   ├── closure.py              # Project closures
│   ├── endorsement.py          # AEC endorsements
│   ├── custom_publication.py   # Custom publications
│   ├── admin.py                # Admin operations
│   ├── annual_report.py        # Annual reports
│   └── __init__.py             # View exports
├── services/                    # Business logic
│   ├── email_service.py        # Email sending abstraction
│   ├── notification_service.py # Notification logic
│   ├── document_service.py     # Document operations
│   ├── approval_service.py     # Approval workflows
│   ├── pdf_service.py          # PDF generation
│   ├── concept_plan_service.py # Concept plan logic
│   ├── project_plan_service.py # Project plan logic
│   ├── progress_report_service.py # Progress report logic
│   ├── closure_service.py      # Closure logic
│   └── __init__.py             # Service exports
├── serializers/                 # Data serialization
│   ├── base.py                 # Base serializers
│   ├── concept_plan.py         # Concept plan serializers
│   ├── project_plan.py         # Project plan serializers
│   ├── progress_report.py      # Progress report serializers
│   ├── student_report.py       # Student report serializers
│   ├── closure.py              # Closure serializers
│   ├── custom_publication.py   # Publication serializers
│   └── __init__.py             # Serializer exports
├── utils/                       # Reusable utilities
│   ├── email_templates.py      # Email template rendering
│   ├── filters.py              # Query filtering
│   ├── validators.py           # Validation logic
│   ├── helpers.py              # Helper functions
│   └── __init__.py             # Utility exports
├── permissions/                 # Authorization
│   ├── document_permissions.py # Document permissions
│   ├── annual_report_permissions.py # Report permissions
│   └── __init__.py             # Permission exports
├── templates/                   # HTML templates
│   ├── email_templates/        # Email templates (13 types)
│   ├── annual_report.html      # Annual report PDF template
│   └── project_document.html   # Project document PDF template
└── assets/                      # Static assets
    ├── *.png, *.jpg            # Images for PDFs
    ├── *.ttf                   # Nimbus Sans fonts
    └── *.css                   # PDF stylesheets
```

## Models

### ProjectDocument
Base document model for all project documents.

**Fields**:
- `kind`: Document type (concept, projectplan, progressreport, studentreport, projectclosure)
- `status`: Document status (new, inreview, inapproval, approved, recalled)
- `project`: Related project
- `creator`, `modifier`: User tracking
- `project_lead_approval_granted`: Stage 1 approval
- `business_area_lead_approval_granted`: Stage 2 approval
- `directorate_approval_granted`: Stage 3 approval
- `pdf_generation_in_progress`: PDF generation flag

### ConceptPlan
Initial project concept document.

**Fields**:
- `document`: Related ProjectDocument
- `project`: Related project
- `aims`: Project aims (HTML)
- `outcome`: Expected outcomes (HTML)
- `collaborations`: Collaboration details (HTML)
- `strategic_context`: Strategic context (HTML)
- `staff_time_allocation`: Staff allocation table (JSON)

### ProjectPlan
Detailed project plan with methodology.

**Fields**:
- `document`: Related ProjectDocument
- `project`: Related project
- `background`: Project background (HTML)
- `aims`: Project aims (HTML)
- `outcome`: Expected outcomes (HTML)
- `knowledge_transfer`: Knowledge transfer plan (HTML)
- `project_tasks`: Project tasks (HTML)
- `methodology`: Methodology details (HTML)
- `endorsements`: Related AEC endorsements

### ProgressReport
Annual progress report for science/core function projects.

**Fields**:
- `document`: Related ProjectDocument
- `project`: Related project
- `report`: Related annual report
- `year`: Report year
- `context`: Project context (HTML)
- `aims`: Project aims (HTML)
- `progress`: Progress made (HTML)
- `implications`: Management implications (HTML)
- `future`: Future directions (HTML)

### StudentReport
Annual report for student projects.

**Fields**:
- `document`: Related ProjectDocument
- `project`: Related project
- `report`: Related annual report
- `year`: Report year
- `progress_report`: Progress details (HTML)

### ProjectClosure
Project closure document.

**Fields**:
- `document`: Related ProjectDocument
- `project`: Related project
- `reason`: Closure reason (HTML)
- `intended_outcome`: Intended outcome (HTML)
- `knowledge_transfer`: Knowledge transfer details (HTML)
- `hardcopy_location`: Physical document location

### AnnualReport
Annual report for the division.

**Fields**:
- `year`: Report year
- `date_open`: Cycle open date
- `date_closed`: Cycle close date
- `dm`: Director's message (HTML)
- `dm_sign`: Director's signature image
- `service_delivery_intro`: Service delivery introduction (HTML)
- `research_intro`: Research introduction (HTML)
- `student_intro`: Student projects introduction (HTML)
- `publications`: Publications section (HTML)
- `is_published`: Publication status
- `pdf_generation_in_progress`: PDF generation flag

### Endorsement
AEC endorsement for project plans.

**Fields**:
- `project_plan`: Related project plan
- `ae_endorsement_required`: Endorsement required flag
- `ae_endorsement_provided`: Endorsement provided flag
- `endorser`: Endorsing user
- `date_endorsed`: Endorsement date

### CustomPublication
Custom publication entries for annual reports.

**Fields**:
- `title`: Publication title
- `authors`: Publication authors
- `year`: Publication year
- `reference`: Publication reference

## API Endpoints

### Annual Reports

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/documents/reports/` | List all annual reports |
| POST | `/api/documents/reports/` | Create annual report |
| GET | `/api/documents/reports/<id>/` | Get annual report |
| PUT | `/api/documents/reports/<id>/` | Update annual report |
| DELETE | `/api/documents/reports/<id>/` | Delete annual report |
| GET | `/api/documents/reports/latest/` | Get latest report year |
| GET | `/api/documents/reports/completed/` | Get published reports |
| GET | `/api/documents/reports/with-pdfs/` | Reports with PDFs |
| GET | `/api/documents/reports/without-pdfs/` | Reports without PDFs |
| GET | `/api/documents/reports/latest-progress/` | Latest year progress reports |
| GET | `/api/documents/reports/latest-student/` | Latest year student reports |
| GET | `/api/documents/reports/latest-inactive/` | Latest year inactive reports |
| GET | `/api/documents/reports/<id>/full/` | Full report with all data |

### Project Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/documents/` | List all documents |
| POST | `/api/documents/` | Create document |
| GET | `/api/documents/<id>/` | Get document |
| PUT | `/api/documents/<id>/` | Update document |
| DELETE | `/api/documents/<id>/` | Delete document |
| GET | `/api/documents/pending/` | Documents pending my action |
| GET | `/api/documents/pending-all/` | All pending documents (admin) |
| GET | `/api/documents/<id>/comments/` | Get document comments |

### Concept Plans

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/documents/concept-plans/` | List concept plans |
| POST | `/api/documents/concept-plans/` | Create concept plan |
| GET | `/api/documents/concept-plans/<id>/` | Get concept plan |
| PUT | `/api/documents/concept-plans/<id>/` | Update concept plan |
| GET | `/api/documents/concept-plans/data/` | Get concept plan data |

### Project Plans

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/documents/project-plans/` | List project plans |
| POST | `/api/documents/project-plans/` | Create project plan |
| GET | `/api/documents/project-plans/<id>/` | Get project plan |
| PUT | `/api/documents/project-plans/<id>/` | Update project plan |

### Progress Reports

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/documents/progress-reports/` | List progress reports |
| POST | `/api/documents/progress-reports/` | Create progress report |
| GET | `/api/documents/progress-reports/<id>/` | Get progress report |
| PUT | `/api/documents/progress-reports/<id>/` | Update progress report |
| GET | `/api/documents/progress-reports/year/<year>/` | Get by year |

### Student Reports

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/documents/student-reports/` | List student reports |
| POST | `/api/documents/student-reports/` | Create student report |
| GET | `/api/documents/student-reports/<id>/` | Get student report |
| PUT | `/api/documents/student-reports/<id>/` | Update student report |
| GET | `/api/documents/student-reports/year/<year>/` | Get by year |

### Project Closures

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/documents/closures/` | List project closures |
| POST | `/api/documents/closures/` | Create project closure |
| GET | `/api/documents/closures/<id>/` | Get project closure |
| PUT | `/api/documents/closures/<id>/` | Update project closure |

### Endorsements

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/documents/endorsements/` | List endorsements |
| POST | `/api/documents/endorsements/` | Create endorsement |
| GET | `/api/documents/endorsements/<id>/` | Get endorsement |
| PUT | `/api/documents/endorsements/<id>/` | Update endorsement |
| DELETE | `/api/documents/endorsements/<id>/` | Delete endorsement |
| GET | `/api/documents/endorsements/pending/` | Pending my action |
| POST | `/api/documents/endorsements/<id>/seek/` | Seek endorsement |

### Custom Publications

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/documents/publications/` | List custom publications |
| POST | `/api/documents/publications/` | Create custom publication |
| GET | `/api/documents/publications/<id>/` | Get custom publication |
| PUT | `/api/documents/publications/<id>/` | Update custom publication |
| DELETE | `/api/documents/publications/<id>/` | Delete custom publication |

### Approval Workflow

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/documents/<id>/request-approval/` | Request approval |
| POST | `/api/documents/<id>/approve-stage-one/` | Project lead approval |
| POST | `/api/documents/<id>/approve-stage-two/` | Business area approval |
| POST | `/api/documents/<id>/approve-stage-three/` | Directorate approval |
| POST | `/api/documents/<id>/send-back/` | Send back for revision |
| POST | `/api/documents/<id>/recall/` | Recall document |
| POST | `/api/documents/batch-approve/` | Batch approve documents |
| POST | `/api/documents/batch-approve-old/` | Legacy batch approve |
| POST | `/api/documents/<id>/final-approval/` | Final approval (admin) |

### PDF Generation

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/documents/<id>/download/` | Download document PDF |
| POST | `/api/documents/<id>/generate-pdf/` | Generate document PDF |
| POST | `/api/documents/<id>/cancel-pdf/` | Cancel PDF generation |
| GET | `/api/documents/reports/<id>/download/` | Download report PDF |
| POST | `/api/documents/reports/<id>/generate-pdf/` | Generate report PDF |
| POST | `/api/documents/reports/<id>/cancel-pdf/` | Cancel report PDF |

### Admin Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/documents/spawn/` | Spawn document (admin) |
| GET | `/api/documents/previous-reports/` | Get previous reports data |
| POST | `/api/projects/<id>/reopen/` | Reopen closed project |
| POST | `/api/documents/new-cycle/` | Open new reporting cycle |
| POST | `/api/documents/send-bump-emails/` | Send reminder emails |
| POST | `/api/documents/send-mention/` | Send mention notification |

## Services

### EmailService
Low-level email sending abstraction.

**Methods**:
- `send_template_email(template_name, recipient_email, subject, context, from_email)`: Send templated email
- `send_document_notification(notification_type, document, recipients, actioning_user, additional_context)`: Send document notification

**Email Templates**:
- `document_approved_email.html`
- `document_recalled_email.html`
- `document_sent_back_email.html`
- `feedback_received_email.html`
- `new_cycle_open_email.html`
- `project_closed_email.html`
- `project_reopened_email.html`
- `review_document_email.html`

### NotificationService
Business logic for document notifications.

**Methods**:
- `notify_document_approved(document, approver)`: Document approved notification
- `notify_document_approved_directorate(document, approver)`: Directorate approval notification
- `notify_document_recalled(document, recaller, reason)`: Document recalled notification
- `notify_document_sent_back(document, sender, reason)`: Document sent back notification
- `notify_document_ready(document, submitter)`: Document ready notification
- `notify_feedback_received(document, feedback_provider, feedback_text)`: Feedback notification
- `notify_review_request(document, requester)`: Review request notification
- `send_bump_emails(documents, reminder_type)`: Reminder emails
- `notify_comment_mention(document, comment, mentioned_user, commenter)`: Mention notification
- `notify_new_cycle_open(cycle, projects)`: New cycle notification
- `notify_project_closed(project, closer)`: Project closed notification
- `notify_project_reopened(project, reopener)`: Project reopened notification
- `send_spms_invite(user, inviter, invite_link)`: SPMS invite notification

### DocumentService
Base document operations with N+1 optimization.

**Methods**:
- `list_documents(user, filters)`: List documents with filtering
- `get_document(pk)`: Get document by ID
- `create_document(user, data)`: Create document
- `update_document(pk, user, data)`: Update document
- `delete_document(pk, user)`: Delete document
- `get_pending_documents(user, stage)`: Get pending documents for user

### ApprovalService
3-stage approval workflow logic.

**Methods**:
- `request_approval(document, user)`: Request approval (move to inreview)
- `approve_stage_one(document, user)`: Project lead approval
- `approve_stage_two(document, user)`: Business area approval
- `approve_stage_three(document, user)`: Directorate approval
- `send_back(document, user, reason)`: Send back for revision
- `recall_document(document, user, reason)`: Recall document
- `batch_approve(documents, user, stage)`: Batch approve multiple documents
- `final_approval(document, user)`: Final approval (admin)

**Approval Stages**:
1. **Stage 1**: Project lead approval
2. **Stage 2**: Business area lead approval
3. **Stage 3**: Directorate approval

### PDFService
PDF generation using Prince XML.

**Methods**:
- `generate_document_pdf(document)`: Generate project document PDF
- `generate_annual_report_pdf(report, genkind)`: Generate annual report PDF
- `cancel_pdf_generation(document)`: Cancel PDF generation
- `get_pdf_context(document)`: Build PDF template context

**PDF Templates**:
- `templates/project_document.html`: Project documents
- `templates/annual_report.html`: Annual reports

**Assets**:
- Fonts: Nimbus Sans (Regular, Bold, Italic, Bold Italic)
- Images: Chapter images, logos, DBCA branding
- Stylesheets: PDF-specific CSS

### ConceptPlanService
Concept plan operations.

**Methods**:
- `list_concept_plans(user, filters)`: List concept plans
- `get_concept_plan(pk)`: Get concept plan
- `create_concept_plan(user, project_id, data)`: Create concept plan
- `update_concept_plan(pk, user, data)`: Update concept plan
- `get_concept_plan_data(project_id)`: Get data for concept plan form

### ProjectPlanService
Project plan operations.

**Methods**:
- `list_project_plans(user, filters)`: List project plans
- `get_project_plan(pk)`: Get project plan
- `create_project_plan(user, project_id, data)`: Create project plan
- `update_project_plan(pk, user, data)`: Update project plan

### ProgressReportService
Progress report operations.

**Methods**:
- `list_progress_reports(user, filters)`: List progress reports
- `get_progress_report(pk)`: Get progress report
- `create_progress_report(user, project_id, year, data)`: Create progress report
- `update_progress_report(pk, user, data)`: Update progress report
- `get_reports_by_year(year)`: Get all reports for a year

### ClosureService
Project closure operations.

**Methods**:
- `list_closures(user, filters)`: List project closures
- `get_closure(pk)`: Get project closure
- `create_closure(user, project_id, data)`: Create project closure
- `update_closure(pk, user, data)`: Update project closure
- `close_project(project_id, user, reason)`: Close project

## Permissions

### Document Permissions

- `CanViewDocument`: View document (project team, business area, directorate)
- `CanEditDocument`: Edit document (project lead, creator)
- `CanApproveDocument`: Approve document (based on stage)
- `CanRecallDocument`: Recall document (approvers, admin)
- `CanDeleteDocument`: Delete document (creator, admin)
- `CanGeneratePDF`: Generate PDF (project team, admin)

### Annual Report Permissions

- `CanViewAnnualReport`: View report (all authenticated users)
- `CanEditAnnualReport`: Edit report (admin, directorate)
- `CanPublishAnnualReport`: Publish report (admin, director)
- `CanGenerateAnnualReportPDF`: Generate report PDF (admin, directorate)

## Email Workflows

The documents app uses a centralized email service layer with 13 notification types:

1. **Document Approved**: Notify project team when document approved
2. **Document Approved (Directorate)**: Notify directorate when approved at stage 3
3. **Document Recalled**: Notify project team when document recalled
4. **Document Sent Back**: Notify creator when sent back for revision
5. **Document Ready**: Notify approvers when document ready for review
6. **Feedback Received**: Notify creator when feedback added
7. **Review Requested**: Notify reviewer when review requested
8. **Bump Email**: Remind users of pending actions
9. **Mention Notification**: Notify user when mentioned in comment
10. **New Cycle Open**: Notify business area leaders of new reporting cycle
11. **Project Closed**: Notify project team when project closed
12. **Project Reopened**: Notify project team when project reopened
13. **SPMS Invite**: Invite user to SPMS

**Email Template Location**: `templates/email_templates/`

**Email Service Pattern**:
```python
# All email sending goes through NotificationService
NotificationService.notify_document_approved(document, approver)

# NotificationService delegates to EmailService
EmailService.send_document_notification(
    notification_type='approved',
    document=document,
    recipients=recipients,
    actioning_user=approver
)
```

## PDF Generation

The app uses Prince XML for PDF generation with asynchronous processing:

**Process**:
1. User requests PDF generation
2. `pdf_generation_in_progress` flag set to True
3. Prince XML generates PDF from HTML template
4. PDF saved to document/report
5. Flag set to False
6. User can download PDF

**Templates**:
- `templates/project_document.html`: Project documents (concept plans, project plans, progress reports, student reports, closures)
- `templates/annual_report.html`: Annual reports with all sections

**Assets**:
- `assets/NimbusSans-*.ttf`: Fonts for PDFs
- `assets/*.png, *.jpg`: Images for PDFs
- `assets/*.css`: PDF-specific stylesheets

**PDF Context**:
- Document/report data
- Project data
- User data
- Business area data
- Endorsements (for project plans)
- Progress/student reports (for annual reports)

## Testing

Run tests:
```bash
cd backend
poetry run python manage.py test documents
```

## Usage Examples

### Create Concept Plan
```python
from documents.services.concept_plan_service import ConceptPlanService

concept_plan = ConceptPlanService.create_concept_plan(
    user=request.user,
    project_id=1,
    data={
        'aims': '<p>Project aims</p>',
        'outcome': '<p>Expected outcomes</p>',
        'collaborations': '<p>Collaborations</p>',
        'strategic_context': '<p>Strategic context</p>',
    }
)
```

### Request Approval
```python
from documents.services.approval_service import ApprovalService

# Request approval (move to inreview)
ApprovalService.request_approval(
    document=document,
    user=request.user
)

# Approve at stage 1 (project lead)
ApprovalService.approve_stage_one(
    document=document,
    user=request.user
)

# Approve at stage 2 (business area lead)
ApprovalService.approve_stage_two(
    document=document,
    user=request.user
)

# Approve at stage 3 (directorate)
ApprovalService.approve_stage_three(
    document=document,
    user=request.user
)
```

### Generate PDF
```python
from documents.services.pdf_service import PDFService

# Generate project document PDF
pdf_file = PDFService.generate_document_pdf(document)

# Generate annual report PDF
pdf_file = PDFService.generate_annual_report_pdf(
    report=report,
    genkind='full'  # or 'progress', 'student', 'inactive'
)
```

### Send Notification
```python
from documents.services.notification_service import NotificationService

# Document approved
NotificationService.notify_document_approved(
    document=document,
    approver=request.user
)

# Document recalled
NotificationService.notify_document_recalled(
    document=document,
    recaller=request.user,
    reason='Needs revision'
)

# Document sent back
NotificationService.notify_document_sent_back(
    document=document,
    sender=request.user,
    reason='Missing information'
)
```

### List Documents with Filters
```python
from documents.services.document_service import DocumentService

documents = DocumentService.list_documents(
    user=request.user,
    filters={
        'kind': 'concept',
        'status': 'approved',
        'project_id': 1,
    }
)
```

## Notes

- All views delegate business logic to services
- All email sending goes through NotificationService
- PDF generation is asynchronous with progress tracking
- 3-stage approval workflow for science projects
- Simplified approval for non-science projects
- Annual reports aggregate progress/student reports
- HTML content sanitized before saving
- N+1 queries optimized with select_related/prefetch_related
- All services use @transaction.atomic for data integrity

---

**Version**: 1.0  
**Last Updated**: February 1, 2026
