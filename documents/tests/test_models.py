"""
Tests for document models
"""

import pytest
from datetime import datetime

from documents.models import (
    AnnualReport,
    ProjectDocument,
    ConceptPlan,
    ProjectPlan,
    ProgressReport,
    StudentReport,
    ProjectClosure,
    Endorsement,
    CustomPublication,
)


class TestAnnualReport:
    """Tests for AnnualReport model"""

    def test_save_sets_default_dm_sign(self, db):
        """Test that save() sets default dm_sign if not provided"""
        # Arrange
        report = AnnualReport(
            year=2024,
            date_open=datetime(2024, 1, 1),
            date_closed=datetime(2024, 12, 31),
        )

        # Act
        report.save()

        # Assert
        assert report.dm_sign is not None
        assert "Dr Margaret Byrne" in report.dm_sign
        assert "October 2024" in report.dm_sign

    def test_str_representation(self, annual_report, db):
        """Test string representation of AnnualReport"""
        # Act
        result = str(annual_report)

        # Assert
        assert f"ARAR - {annual_report.year}" in result
        assert f"ID: {annual_report.pk}" in result


class TestProjectDocument:
    """Tests for ProjectDocument model"""

    def test_get_serializer_class(self, project_document, db):
        """Test get_serializer_class method"""
        # Arrange
        from documents.models import ProjectDocument as Model

        # Act
        serializer_class = project_document.get_serializer_class(Model)

        # Assert
        assert serializer_class is not None
        assert hasattr(serializer_class, "Meta")
        assert serializer_class.Meta.model == Model

    def test_has_project_document_data_concept_plan(
        self, concept_plan_with_details, db
    ):
        """Test has_project_document_data for concept plan"""
        # Arrange
        document = concept_plan_with_details.document

        # Act
        result = document.has_project_document_data()

        # Assert
        assert result is True

    def test_has_project_document_data_project_plan(self, db, project_with_lead):
        """Test has_project_document_data for project plan"""
        # Arrange
        from common.tests.factories import ProjectDocumentFactory

        document = ProjectDocumentFactory(
            project=project_with_lead,
            kind="projectplan",
        )
        ProjectPlan.objects.create(
            document=document,
            project=project_with_lead,
        )

        # Act
        result = document.has_project_document_data()

        # Assert
        assert result is True

    def test_has_project_document_data_progress_report(
        self, progress_report_with_details, db
    ):
        """Test has_project_document_data for progress report"""
        # Arrange
        document = progress_report_with_details.document

        # Act
        result = document.has_project_document_data()

        # Assert
        assert result is True

    def test_has_project_document_data_student_report(
        self, student_report_with_details, db
    ):
        """Test has_project_document_data for student report"""
        # Arrange
        document = student_report_with_details.document

        # Act
        result = document.has_project_document_data()

        # Assert
        assert result is True

    def test_has_project_document_data_project_closure(self, project_closure, db):
        """Test has_project_document_data for project closure"""
        # Arrange
        document = project_closure.document

        # Act
        result = document.has_project_document_data()

        # Assert
        assert result is True

    def test_str_representation(self, project_document, db):
        """Test string representation of ProjectDocument"""
        # Act
        result = str(project_document)

        # Assert
        assert str(project_document.pk) in result
        assert project_document.kind.capitalize() in result


class TestConceptPlan:
    """Tests for ConceptPlan model"""

    def test_extract_inner_text(self, concept_plan_with_details, db):
        """Test extract_inner_text method"""
        # Arrange
        html = "<p>Test <strong>content</strong> here</p>"

        # Act
        result = concept_plan_with_details.extract_inner_text(html)

        # Assert
        assert result == "Test content here"

    def test_str_representation(self, concept_plan_with_details, db):
        """Test string representation of ConceptPlan"""
        # Act
        result = str(concept_plan_with_details)

        # Assert
        assert "(CONCEPT PLAN)" in result


class TestProjectPlan:
    """Tests for ProjectPlan model"""

    def test_extract_inner_text(self, db, project_with_lead):
        """Test extract_inner_text method"""
        # Arrange
        from common.tests.factories import ProjectDocumentFactory

        document = ProjectDocumentFactory(
            project=project_with_lead,
            kind="projectplan",
        )
        project_plan = ProjectPlan.objects.create(
            document=document,
            project=project_with_lead,
        )
        html = "<p>Test <strong>content</strong> here</p>"

        # Act
        result = project_plan.extract_inner_text(html)

        # Assert
        assert result == "Test content here"

    def test_str_representation(self, db, project_with_lead):
        """Test string representation of ProjectPlan"""
        # Arrange
        from common.tests.factories import ProjectDocumentFactory

        document = ProjectDocumentFactory(
            project=project_with_lead,
            kind="projectplan",
        )
        project_plan = ProjectPlan.objects.create(
            document=document,
            project=project_with_lead,
        )

        # Act
        result = str(project_plan)

        # Assert
        assert "(PROJECT PLAN)" in result


class TestProgressReport:
    """Tests for ProgressReport model"""

    def test_extract_inner_text(self, progress_report_with_details, db):
        """Test extract_inner_text method"""
        # Arrange
        html = "<p>Test <strong>content</strong> here</p>"

        # Act
        result = progress_report_with_details.extract_inner_text(html)

        # Assert
        assert result == "Test content here"

    def test_str_representation(self, progress_report_with_details, db):
        """Test string representation of ProgressReport"""
        # Act
        result = str(progress_report_with_details)

        # Assert
        assert "PROGRESS REPORT" in result
        assert str(progress_report_with_details.year) in result


class TestStudentReport:
    """Tests for StudentReport model"""

    def test_extract_inner_text(self, student_report_with_details, db):
        """Test extract_inner_text method"""
        # Arrange
        html = "<p>Test <strong>content</strong> here</p>"

        # Act
        result = student_report_with_details.extract_inner_text(html)

        # Assert
        assert result == "Test content here"

    def test_str_representation(self, student_report_with_details, db):
        """Test string representation of StudentReport"""
        # Act
        result = str(student_report_with_details)

        # Assert
        assert "STUDENT REPORT" in result
        assert str(student_report_with_details.year) in result


class TestProjectClosure:
    """Tests for ProjectClosure model"""

    def test_extract_inner_text(self, project_closure, db):
        """Test extract_inner_text method"""
        # Arrange
        html = "<p>Test <strong>content</strong> here</p>"

        # Act
        result = project_closure.extract_inner_text(html)

        # Assert
        assert result == "Test content here"

    def test_str_representation(self, project_closure, db):
        """Test string representation of ProjectClosure"""
        # Act
        result = str(project_closure)

        # Assert
        assert "(PROJECT CLOSURE)" in result


class TestEndorsement:
    """Tests for Endorsement model"""

    def test_str_representation(self, db, project_with_lead):
        """Test string representation of Endorsement"""
        # Arrange
        from common.tests.factories import ProjectDocumentFactory

        document = ProjectDocumentFactory(
            project=project_with_lead,
            kind="projectplan",
        )
        project_plan = ProjectPlan.objects.create(
            document=document,
            project=project_with_lead,
        )
        endorsement = Endorsement.objects.create(
            project_plan=project_plan,
        )

        # Act
        result = str(endorsement)

        # Assert
        assert "ENDORSEMENTS" in result


class TestCustomPublication:
    """Tests for CustomPublication model"""

    def test_str_representation(self, db, user):
        """Test string representation of CustomPublication"""
        # Arrange
        from users.models import PublicStaffProfile

        profile = PublicStaffProfile.objects.create(
            user=user,
            employee_id="12345",
        )
        publication = CustomPublication.objects.create(
            public_profile=profile,
            year=2024,
            title="Test Publication",
        )

        # Act
        result = str(publication)

        # Assert
        assert result == "Test Publication"
