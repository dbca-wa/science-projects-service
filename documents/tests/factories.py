"""
Document-specific test data factories.

Provides factories for creating document test data.
"""

import factory
from factory.django import DjangoModelFactory
from common.tests.factories import ProjectFactory, UserFactory


class AnnualReportFactory(DjangoModelFactory):
    """Factory for creating annual report documents"""

    class Meta:
        model = "documents.AnnualReport"
        skip_postgeneration_save = True

    year = factory.Faker("year")
    creator = factory.SubFactory(UserFactory)
    modifier = factory.SubFactory(UserFactory)
    date_open = factory.Faker("date_this_year")
    date_closed = factory.Faker("date_this_year")


class ProjectDocumentFactory(DjangoModelFactory):
    """Factory for creating test project documents"""

    class Meta:
        model = "documents.ProjectDocument"
        skip_postgeneration_save = True

    project = factory.SubFactory(ProjectFactory)
    kind = "concept"
    status = "new"
    creator = factory.SubFactory(UserFactory)
    modifier = factory.SubFactory(UserFactory)

    # Approval fields
    project_lead_approval_granted = False
    business_area_lead_approval_granted = False
    directorate_approval_granted = False


class ConceptPlanFactory(DjangoModelFactory):
    """Factory for creating concept plan documents with details"""

    class Meta:
        model = "documents.ConceptPlan"
        skip_postgeneration_save = True

    document = factory.SubFactory(ProjectDocumentFactory, kind="concept")
    project = factory.SelfAttribute("document.project")
    background = factory.Faker("paragraph")
    aims = factory.Faker("paragraph")
    outcome = factory.Faker("paragraph")
    collaborations = factory.Faker("paragraph")
    strategic_context = factory.Faker("paragraph")


class ProjectPlanFactory(DjangoModelFactory):
    """Factory for creating project plan documents with details"""

    class Meta:
        model = "documents.ProjectPlan"
        skip_postgeneration_save = True

    document = factory.SubFactory(ProjectDocumentFactory, kind="projectplan")
    project = factory.SelfAttribute("document.project")
    background = factory.Faker("paragraph")
    aims = factory.Faker("paragraph")
    outcome = factory.Faker("paragraph")
    knowledge_transfer = factory.Faker("paragraph")
    project_tasks = factory.Faker("paragraph")
    listed_references = factory.Faker("paragraph")
    methodology = factory.Faker("paragraph")


class ProgressReportFactory(DjangoModelFactory):
    """Factory for creating progress report documents with details"""

    class Meta:
        model = "documents.ProgressReport"
        skip_postgeneration_save = True

    document = factory.SubFactory(ProjectDocumentFactory, kind="progressreport")
    report = factory.SubFactory(AnnualReportFactory)
    project = factory.SelfAttribute("document.project")
    year = factory.Faker("year")
    context = factory.Faker("paragraph")
    aims = factory.Faker("paragraph")
    progress = factory.Faker("paragraph")
    implications = factory.Faker("paragraph")
    future = factory.Faker("paragraph")


class StudentReportFactory(DjangoModelFactory):
    """Factory for creating student report documents with details"""

    class Meta:
        model = "documents.StudentReport"
        skip_postgeneration_save = True

    document = factory.SubFactory(ProjectDocumentFactory, kind="studentreport")
    report = factory.SubFactory(AnnualReportFactory)
    project = factory.SelfAttribute("document.project")
    progress_report = factory.Faker("paragraph")
    year = factory.Faker("year")


class ProjectClosureFactory(DjangoModelFactory):
    """Factory for creating project closure documents with details"""

    class Meta:
        model = "documents.ProjectClosure"
        skip_postgeneration_save = True

    document = factory.SubFactory(ProjectDocumentFactory, kind="projectclosure")
    project = factory.SelfAttribute("document.project")
    reason = factory.Faker("paragraph")
    intended_outcome = factory.Faker("paragraph")
    knowledge_transfer = factory.Faker("paragraph")
