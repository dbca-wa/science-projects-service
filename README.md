# Science Projects Management System (SPMS) Backend

[![Tests](https://github.com/dbca-wa/science-projects-service/actions/workflows/test.yml/badge.svg)](https://github.com/dbca-wa/science-projects-service/actions/workflows/test.yml)
[![Coverage](https://codecov.io/gh/dbca-wa/science-projects-service/graph/badge.svg)](https://codecov.io/gh/dbca-wa/science-projects-service)
[![CodeQL](https://github.com/dbca-wa/science-projects-service/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/dbca-wa/science-projects-service/actions/workflows/github-code-scanning/codeql)
[![Issues](https://img.shields.io/static/v1?label=docs&message=Issues&color=brightgreen)](https://github.com/dbca-wa/science-projects-service/issues)

## What is SPMS?

The Science Projects Management System (SPMS) is a comprehensive web application designed to manage scientific research projects for the Department of Biodiversity, Conservation and Attractions (DBCA) in Western Australia.

SPMS provides a centralised platform for tracking research projects, managing documentation, coordinating team members, and maintaining project records throughout their lifecycle.

## Purpose

SPMS serves as the primary tool for:

**Project Management**: Track scientific research projects from conception through completion, including project proposals, approvals, progress updates, and final reports.

**Document Management**: Store and organise project-related documents, including project plans, concept plans, progress reports, student progress reports, and project closures.

**Annual Report Generation**: Compile data from progress reports and stakeholders to generate a comprehensive annual report for demonstrating scientific achievements and securing further funding.

**Team Collaboration**: Coordinate research teams across multiple business areas and locations, manage team member roles and permissions, and facilitate communication through integrated messaging.

**Resource Tracking**: Monitor project resources, budgets, and timelines to ensure efficient allocation and utilisation of departmental resources.

**Reporting and Analytics**: Generate reports on project status, resource utilisation, and research outcomes to support decision-making and strategic planning.

## Who Uses SPMS?

**Research Scientists**: Create and manage research projects, upload findings and documentation, collaborate with team members, and track project progress.

**Project Leads**: Oversee the project to provide final approval before Business Area Lead review.

**Business Area Leads**: Oversee all projects within their Business Area to provide final approval before Directorate review.

**Directorate Reviewer**: Key stakeholder who manages annual report generation by providing final approval on all documents and editing the Annual Report.

**Administrators / Maintainers**: Assists Directorate Reviewer with project approvals, deletions, user accounts and permissions, maintaining system configuration, and providing user support.

## Key Features

### Project Management
- Create and track research projects with detailed metadata
- Categorise projects by research area, status, and priority
- Link projects to geographic locations with map visualisation
- Track project milestones and deliverables
- Manage project lifecycle from proposal to completion

### Document Management
- Upload and store project documents with metadata
- Support for multiple file types (PDFs, images, data files)
- Version control and document history
- Secure file storage with access controls
- Document search and filtering

### User Management
- Role-based access control (staff, researchers, external users)
- User profiles with employment and education history
- Integration with DBCA IT Assets system for user data
- Caretaker system for managing staff who depart or go on leave
- User search and directory

### Collaboration Features
- Project team management with role assignments
- Comments and discussions on projects
- Notifications for project updates via email
- Shared document access

### Geographic Integration
- Project location mapping with interactive maps
- Geographic search and filtering
- Location-based project visualisation
- Integration with DBCA location database

### Reporting and Analytics
- Project status dashboards
- Resource utilisation reports
- Research output tracking
- Custom report generation
- Data export capabilities

### Staff Profiles
- Integrated sister-app
- Provides public-facing data which is maintained per-user
- Details a user's projects and publications
- Details a user's expertise, about, education and employment history

## System Architecture

### Backend (This Repository)
Django REST Framework API providing:
- RESTful API endpoints for all system functionality
- PostgreSQL database for data persistence
- User authentication and authorisation
- File storage and media management
- Integration with external systems (IT Assets, Library API)
- Background task processing
- Comprehensive test coverage (>80%)

### Frontend
React-based single-page application providing:
- Modern, responsive user interface
- Interactive project management tools
- Document upload and management
- Real-time updates and notifications
- Map-based project visualisation

Repository: https://github.com/dbca-wa/science-projects-client

### Infrastructure
- Kubernetes deployment using Kustomize
- Docker containerisation
- PostgreSQL database
- File storage for media and documents
- CI/CD pipeline with GitHub Actions

## Technology Stack

**Backend**:
- Python
- Django
- Django REST Framework
- PostgreSQL
- Poetry (dependency management)

**Testing**:
- pytest with 80%+ coverage requirement
- Test sharding for fast execution
- Property-based testing for critical paths

**Code Quality**:
- black (code formatting)
- isort (import sorting)
- flake8 (linting)
- bandit (security scanning)
- Pre-commit hooks for automated checks

**Deployment**:
- Docker containers
- Kubernetes with Kustomize
- GitHub Actions CI/CD
- Automated testing and deployment

## Documentation

### Getting Started
- [Getting Started](docs/getting-started.md) - Quick setup guide (< 30 minutes)
- [Local Setup](docs/local-setup.md) - Detailed setup instructions

### Development
- [Feature Development](docs/feature-development.md) - Complete development workflow
- [Code Style](docs/code-style.md) - Python and Django coding standards
- [Architecture](docs/architecture.md) - Application structure and patterns

### Testing and Quality
- [Testing](docs/testing.md) - Testing strategy and guidelines
- [Pre-commit](docs/pre-commit.md) - Code quality automation

### Deployment
- [CI/CD](docs/ci-cd.md) - Continuous integration and deployment
- [Kustomize](docs/kustomize.md) - Kubernetes deployment configuration

### Reference
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions
- [Documentation Index](docs/README.md) - Complete documentation overview

## Contributing

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make changes following our [Code Style](docs/code-style.md)
3. Write tests (maintain >80% coverage)
4. Run pre-commit hooks: `pre-commit run --all-files`
5. Push and create a pull request

See [Feature Development](docs/feature-development.md) for the complete workflow.

## Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=. --cov-report=html

# Run specific app tests
poetry run pytest agencies/tests/

# Run in parallel
poetry run pytest -n auto
```

Coverage reports are available in `htmlcov/index.html` after running tests with coverage.

## Code Quality

Pre-commit hooks automatically run on every commit:

```bash
# Install hooks
poetry run pre-commit install

# Run manually
poetry run pre-commit run --all-files
```

Hooks include:
- black (code formatting)
- isort (import sorting)
- flake8 (linting)
- bandit (security checks)
- django-upgrade (Django best practices)

## History

SPMS was originally developed by Florian Mayer as the Science Directorate Information System (SDIS). The current version represents a completely rewritten modernisation of the system, rebuilt with current technologies and additional features, following an ETL migration step.

Original SDIS: https://github.com/dbca-wa/sdis

The system has evolved to meet the growing needs of DBCA's research programs, incorporating feedback from users and adapting to changing requirements over several years of active use.

## Organisation

**Department of Biodiversity, Conservation and Attractions (DBCA)**

DBCA is the Western Australian government department responsible for managing the state's parks, wildlife, and biodiversity. The department conducts extensive scientific research to support conservation efforts and environmental management.

SPMS supports DBCA's research mission by providing the infrastructure needed to manage complex, long-term research projects across diverse scientific disciplines and geographic locations. The key deliverable is the Annual Report.

## Support and Maintenance

SPMS is actively maintained by Ecoinformatics' development team. The system receives regular updates for:
- Security patches and dependency updates
- New features based on user feedback
- Performance optimisations
- Bug fixes and improvements
- Integration with DBCA systems

## Related Systems

**IT Assets**: DBCA's internal system for managing IT resources and user accounts. SPMS integrates with IT Assets to synchronise user data and authentication under SSO.

**Library System**: DBCA's publication management system. SPMS integrates to link research projects with published outputs.

**Geographic Information Systems**: SPMS integrates with DBCA's GIS infrastructure for location-based project management and visualisation. Current map setup on the frontend utilises a dump of this data.

## License

Copyright (c) Department of Biodiversity, Conservation and Attractions (DBCA), Western Australia.

This software is proprietary and confidential. It is developed and maintained for internal use by DBCA. While the source code is publicly visible for transparency and collaboration with authorised partners, it is not licensed for reproduction, modification, or use by external parties without explicit written permission from DBCA.

Unauthorised copying, distribution, modification, or use of this software is strictly prohibited.

## Support

For issues and questions:
- Check [Troubleshooting](docs/troubleshooting.md)
- Review [Documentation](docs/README.md)
- Create an issue on GitHub
