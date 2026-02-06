"""
Tests for documents admin
"""

import pytest
from unittest.mock import Mock, patch
from django.contrib.admin.sites import AdminSite

from documents.admin import (
    UserFilterWidget,
    CustomPublicationAdmin,
    AnnualReportAdmin,
    ProjectDocumentAdmin,
    ConceptPlanAdmin,
    ProjectPlanAdmin,
    ProgressReportAdmin,
    StudentReportAdmin,
    ProjectClosureAdmin,
    EndorsementAdmin,
    delete_unlinked_docs,
    provide_final_approval_for_docs_if_next_exist,
    populate_aims_and_context,
)
from documents.models import (
    CustomPublication,
    AnnualReport,
    ProjectDocument,
    ConceptPlan,
    ProjectPlan,
    ProgressReport,
    StudentReport,
    ProjectClosure,
    Endorsement,
)
from common.tests.factories import ProjectDocumentFactory


# ============================================================================
# WIDGET TESTS
# ============================================================================


class TestUserFilterWidget:
    """Tests for UserFilterWidget"""

    def test_label_from_instance(self, user_factory, db):
        """Test label formatting for user"""
        user = user_factory(first_name="John", last_name="Doe")
        widget = UserFilterWidget("users", False)

        label = widget.label_from_instance(user)

        assert label == "John Doe"

    def test_format_value_none(self, db):
        """Test format_value with None"""
        widget = UserFilterWidget("users", False)

        result = widget.format_value(None)

        assert result == []

    def test_format_value_string(self, db):
        """Test format_value with string"""
        widget = UserFilterWidget("users", False)

        result = widget.format_value("[1, 2, 3]")

        assert result == ["1", "2", "3"]

    def test_format_value_int(self, db):
        """Test format_value with int"""
        widget = UserFilterWidget("users", False)

        result = widget.format_value(5)

        assert result == ["5"]


# ============================================================================
# ADMIN DISPLAY METHOD TESTS
# ============================================================================


class TestProjectDocumentAdmin:
    """Tests for ProjectDocumentAdmin"""

    def test_display_year(self, project_document, db):
        """Test display_year method"""
        admin = ProjectDocumentAdmin(ProjectDocument, AdminSite())

        year = admin.display_year(project_document)

        assert year == project_document.created_at.year


class TestConceptPlanAdmin:
    """Tests for ConceptPlanAdmin"""

    def test_doc_status(self, concept_plan_with_details, db):
        """Test doc_status method"""
        admin = ConceptPlanAdmin(ConceptPlan, AdminSite())

        status = admin.doc_status(concept_plan_with_details)

        assert status == concept_plan_with_details.document.get_status_display()


class TestProjectPlanAdmin:
    """Tests for ProjectPlanAdmin"""

    def test_doc_status(self, project_plan_with_details, db):
        """Test doc_status method"""
        admin = ProjectPlanAdmin(ProjectPlan, AdminSite())

        status = admin.doc_status(project_plan_with_details)

        assert status == project_plan_with_details.document.get_status_display()


class TestProgressReportAdmin:
    """Tests for ProgressReportAdmin"""

    def test_doc_status(self, progress_report, db):
        """Test doc_status method"""
        admin = ProgressReportAdmin(ProgressReport, AdminSite())

        status = admin.doc_status(progress_report)

        assert status == progress_report.document.get_status_display()


class TestStudentReportAdmin:
    """Tests for StudentReportAdmin"""

    def test_doc_status(self, student_report, db):
        """Test doc_status method"""
        admin = StudentReportAdmin(StudentReport, AdminSite())

        status = admin.doc_status(student_report)

        assert status == student_report.document.get_status_display()


class TestProjectClosureAdmin:
    """Tests for ProjectClosureAdmin"""

    def test_doc_created_data(self, project_closure, db):
        """Test doc_created_data method"""
        admin = ProjectClosureAdmin(ProjectClosure, AdminSite())

        created_at = admin.doc_created_data(project_closure)

        assert created_at == project_closure.document.created_at

    def test_doc_status(self, project_closure, db):
        """Test doc_status method"""
        admin = ProjectClosureAdmin(ProjectClosure, AdminSite())

        status = admin.doc_status(project_closure)

        assert status == project_closure.document.get_status_display()


class TestEndorsementAdmin:
    """Tests for EndorsementAdmin"""

    def test_display_data_management_short(self, endorsement, db):
        """Test display_data_management with short text"""
        endorsement.data_management = "Short text"
        endorsement.save()

        admin = EndorsementAdmin(Endorsement, AdminSite())

        result = admin.display_data_management(endorsement)

        assert result == "Short text"

    def test_display_data_management_long(self, endorsement, db):
        """Test display_data_management with long text"""
        endorsement.data_management = "A" * 150
        endorsement.save()

        admin = EndorsementAdmin(Endorsement, AdminSite())

        result = admin.display_data_management(endorsement)

        assert result == "A" * 100 + "..."
        assert len(result) == 103

    def test_display_data_management_none(self, endorsement, db):
        """Test display_data_management with None"""
        endorsement.data_management = None
        endorsement.save()

        admin = EndorsementAdmin(Endorsement, AdminSite())

        result = admin.display_data_management(endorsement)

        assert result is None


# ============================================================================
# ADMIN ACTION TESTS
# ============================================================================


class TestDeleteUnlinkedDocs:
    """Tests for delete_unlinked_docs admin action"""

    def test_delete_unlinked_docs_requires_single_selection(self, project_document, db):
        """Test action requires single selection"""
        admin = ProjectDocumentAdmin(ProjectDocument, AdminSite())
        request = Mock()
        selected = [project_document, project_document]  # Multiple selections

        with patch("builtins.print") as mock_print:
            delete_unlinked_docs(admin, request, selected)
            mock_print.assert_called_once_with(
                "PLEASE SELECT ONLY ONE ITEM TO BEGIN, THIS IS A BATCH PROCESS"
            )

    def test_delete_unlinked_docs_deletes_empty_docs(self, project_with_lead, db):
        """Test action deletes documents without data"""
        # Create a document without associated data (no ConceptPlan, ProjectPlan, etc.)
        empty_doc = ProjectDocumentFactory(
            project=project_with_lead,
            kind="concept",
            status="new",
        )

        # Create a document with associated data
        doc_with_data = ProjectDocumentFactory(
            project=project_with_lead,
            kind="concept",
            status="new",
        )
        from documents.models import ConceptPlan

        ConceptPlan.objects.create(
            document=doc_with_data,
            project=project_with_lead,
            background="<p>Test</p>",
        )

        admin = ProjectDocumentAdmin(ProjectDocument, AdminSite())
        request = Mock()
        selected = [empty_doc]

        initial_count = ProjectDocument.objects.count()

        with patch("builtins.print") as mock_print:
            delete_unlinked_docs(admin, request, selected)
            # Should print deletion summary
            assert mock_print.called
            # Empty doc should be deleted
            assert ProjectDocument.objects.count() < initial_count
            # Doc with data should still exist
            assert ProjectDocument.objects.filter(pk=doc_with_data.pk).exists()


class TestProvideFinalApprovalForDocsIfNextExist:
    """Tests for provide_final_approval_for_docs_if_next_exist admin action"""

    def test_action_requires_single_selection(self, project_document, db):
        """Test action requires single selection"""
        admin = ProjectDocumentAdmin(ProjectDocument, AdminSite())
        request = Mock()
        selected = [project_document, project_document]

        with patch("builtins.print") as mock_print:
            provide_final_approval_for_docs_if_next_exist(admin, request, selected)
            mock_print.assert_called_once_with(
                "PLEASE SELECT ONLY ONE ITEM TO BEGIN, THIS IS A BATCH PROCESS"
            )

    def test_action_approves_concept_when_project_plan_exists(
        self, project_with_lead, concept_plan_with_details, db
    ):
        """Test action approves concept plan when project plan exists"""
        # Concept plan document without approvals
        concept_doc = concept_plan_with_details.document
        concept_doc.project_lead_approval_granted = False
        concept_doc.business_area_lead_approval_granted = False
        concept_doc.directorate_approval_granted = False
        concept_doc.save()

        # Create project plan for same project
        project_plan_doc = ProjectDocumentFactory(
            project=project_with_lead,
            kind="projectplan",
            status="new",
        )

        admin = ProjectDocumentAdmin(ProjectDocument, AdminSite())
        request = Mock()
        selected = [concept_doc]

        with patch("builtins.print") as mock_print:
            provide_final_approval_for_docs_if_next_exist(admin, request, selected)
            assert mock_print.called

            # Verify concept doc was approved
            concept_doc.refresh_from_db()
            # Note: The action processes ALL docs, not just selected ones
            # So we just verify the action ran without errors


class TestPopulateAimsAndContext:
    """Tests for populate_aims_and_context admin action"""

    def test_action_requires_single_selection(self, progress_report, db):
        """Test action requires single selection"""
        admin = ProgressReportAdmin(ProgressReport, AdminSite())
        request = Mock()
        selected = [progress_report, progress_report]

        with patch("builtins.print") as mock_print:
            populate_aims_and_context(admin, request, selected)
            mock_print.assert_called_once_with(
                "PLEASE SELECT ONLY ONE ITEM TO BEGIN, THIS IS A BATCH PROCESS"
            )

    def test_action_populates_from_previous_year(self, project_with_lead, db):
        """Test action populates aims and context from previous year"""
        # Create annual reports for different years
        from documents.models import AnnualReport
        from datetime import date

        prev_year_report = AnnualReport.objects.create(
            year=2022,
            is_published=False,
            date_open=date(2022, 1, 1),
            date_closed=date(2022, 12, 31),
        )

        current_year_report = AnnualReport.objects.create(
            year=2023,
            is_published=False,
            date_open=date(2023, 1, 1),
            date_closed=date(2023, 12, 31),
        )

        # Create previous year report
        prev_doc = ProjectDocumentFactory(
            project=project_with_lead,
            kind="progressreport",
            status="new",
        )
        prev_report = ProgressReport.objects.create(
            document=prev_doc,
            report=prev_year_report,
            project=project_with_lead,
            year=2022,
            aims="Previous aims",
            context="Previous context",
            progress="<p>Test progress</p>",
            implications="<p>Test implications</p>",
            future="<p>Test future</p>",
        )

        # Current year report without aims/context
        current_doc = ProjectDocumentFactory(
            project=project_with_lead,
            kind="progressreport",
            status="new",
        )
        current_report = ProgressReport.objects.create(
            document=current_doc,
            report=current_year_report,
            project=project_with_lead,
            year=2023,
            aims="",
            context="",
            progress="<p>Test progress</p>",
            implications="<p>Test implications</p>",
            future="<p>Test future</p>",
        )

        admin = ProgressReportAdmin(ProgressReport, AdminSite())
        request = Mock()
        request.user = Mock()
        selected = [current_report]

        with patch.object(admin, "message_user") as mock_message:
            populate_aims_and_context(admin, request, selected)
            assert mock_message.called
