"""
Tests for document utility functions
"""

import json
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from rest_framework.exceptions import ValidationError

from documents.models import ProjectDocument
from documents.utils.filters import apply_annual_report_filters, apply_document_filters
from documents.utils.helpers import (
    extract_text_content,
    format_document_date,
    get_approval_stage_name,
    get_current_maintainer_id,
    get_document_display_name,
    get_document_status_display,
    get_document_year,
    get_encoded_image,
    get_next_approval_stage,
    is_document_editable,
    sanitize_html_content,
)
from documents.utils.html_tables import (
    HTMLTableTemplates,
    default_external_budget,
    default_internal_budget,
    default_staff_time_allocation,
    json_to_html_table,
)
from documents.utils.validators import (
    validate_annual_report_year,
    validate_approval_stage,
    validate_document_kind,
    validate_document_status_transition,
    validate_endorsement_requirements,
)

# ============================================================================
# FILTER TESTS
# ============================================================================


class TestApplyDocumentFilters:
    """Tests for apply_document_filters"""

    def test_filter_by_search_term(self, project_document):
        """Test filtering by search term"""
        queryset = ProjectDocument.objects.filter(pk=project_document.pk)

        # Search by project title
        filters = {"searchTerm": project_document.project.title[:5]}
        result = apply_document_filters(queryset, filters)

        assert result.count() == 1
        assert result.first() == project_document

    def test_filter_by_kind(self, project_document):
        """Test filtering by document kind"""
        queryset = ProjectDocument.objects.filter(pk=project_document.pk)

        filters = {"kind": project_document.kind}
        result = apply_document_filters(queryset, filters)

        assert result.count() == 1

    def test_filter_by_status(self, project_document):
        """Test filtering by document status"""
        queryset = ProjectDocument.objects.filter(pk=project_document.pk)

        filters = {"status": project_document.status}
        result = apply_document_filters(queryset, filters)

        assert result.count() == 1

    def test_filter_by_project_id(self, project_document):
        """Test filtering by project ID"""
        queryset = ProjectDocument.objects.filter(pk=project_document.pk)

        filters = {"project": project_document.project.pk}
        result = apply_document_filters(queryset, filters)

        assert result.count() == 1

    def test_filter_by_year(self, project_document):
        """Test filtering by project year"""
        queryset = ProjectDocument.objects.filter(pk=project_document.pk)

        filters = {"year": project_document.project.year}
        result = apply_document_filters(queryset, filters)

        assert result.count() == 1

    def test_filter_approved_only(self, project_document):
        """Test filtering approved documents only"""
        project_document.status = "approved"
        project_document.save()

        queryset = ProjectDocument.objects.filter(pk=project_document.pk)
        filters = {"approved_only": True}
        result = apply_document_filters(queryset, filters)

        assert result.count() == 1

    def test_filter_pending_approval(self, project_document):
        """Test filtering pending approval documents"""
        project_document.status = "inapproval"
        project_document.save()

        queryset = ProjectDocument.objects.filter(pk=project_document.pk)
        filters = {"pending_approval": True}
        result = apply_document_filters(queryset, filters)

        assert result.count() == 1


class TestApplyAnnualReportFilters:
    """Tests for apply_annual_report_filters"""

    def test_filter_by_year(self, annual_report):
        """Test filtering by year"""
        from documents.models import AnnualReport

        queryset = AnnualReport.objects.filter(pk=annual_report.pk)
        filters = {"year": annual_report.year}
        result = apply_annual_report_filters(queryset, filters)

        assert result.count() == 1

    def test_filter_published_only(self, annual_report):
        """Test filtering published reports only"""
        from documents.models import AnnualReport

        annual_report.is_published = True
        annual_report.save()

        queryset = AnnualReport.objects.filter(pk=annual_report.pk)
        filters = {"published_only": True}
        result = apply_annual_report_filters(queryset, filters)

        assert result.count() == 1


# ============================================================================
# VALIDATOR TESTS
# ============================================================================


class TestValidateDocumentStatusTransition:
    """Tests for validate_document_status_transition"""

    def test_valid_transition_new_to_revising(self):
        """Test valid transition from new to revising"""
        validate_document_status_transition("new", "revising")

    def test_valid_transition_new_to_inreview(self):
        """Test valid transition from new to inreview"""
        validate_document_status_transition("new", "inreview")

    def test_invalid_transition_approved_to_revising(self):
        """Test invalid transition from approved"""
        with pytest.raises(ValidationError):
            validate_document_status_transition("approved", "revising")

    def test_invalid_current_status(self):
        """Test invalid current status"""
        with pytest.raises(ValidationError):
            validate_document_status_transition("invalid", "new")


class TestValidateApprovalStage:
    """Tests for validate_approval_stage"""

    def test_valid_approval_stage(self, project_document):
        """Test valid approval stage"""
        project_document.status = "inreview"

        with patch.object(
            project_document, "has_project_document_data", return_value=True
        ):
            validate_approval_stage(project_document)

    def test_invalid_status_for_approval(self, project_document):
        """Test invalid status for approval"""
        project_document.status = "new"

        with pytest.raises(ValidationError, match="must be in review"):
            validate_approval_stage(project_document)

    def test_missing_document_data(self, project_document):
        """Test missing document data"""
        project_document.status = "inreview"

        with patch.object(
            project_document, "has_project_document_data", return_value=False
        ):
            with pytest.raises(ValidationError, match="must have details"):
                validate_approval_stage(project_document)


class TestValidateDocumentKind:
    """Tests for validate_document_kind"""

    def test_valid_document_kind(self):
        """Test valid document kind"""
        validate_document_kind("concept")

    def test_invalid_document_kind(self):
        """Test invalid document kind"""
        with pytest.raises(ValidationError, match="Invalid document kind"):
            validate_document_kind("invalid_kind")


class TestValidateAnnualReportYear:
    """Tests for validate_annual_report_year"""

    def test_valid_year(self):
        """Test valid year"""
        validate_annual_report_year(2023)

    def test_year_too_early(self):
        """Test year before 2013"""
        with pytest.raises(ValidationError, match="must be 2013 or later"):
            validate_annual_report_year(2012)

    def test_year_too_far_future(self):
        """Test year too far in future"""
        current_year = datetime.now().year
        with pytest.raises(ValidationError, match="cannot be more than one year"):
            validate_annual_report_year(current_year + 2)


class TestValidateEndorsementRequirements:
    """Tests for validate_endorsement_requirements"""

    def test_no_endorsements(self):
        """Test project plan with no endorsements"""
        project_plan = Mock()
        project_plan.endorsements.all.return_value = []

        validate_endorsement_requirements(project_plan)

    def test_endorsement_required_and_provided(self):
        """Test endorsement required and provided"""
        endorsement = Mock()
        endorsement.ae_endorsement_required = True
        endorsement.ae_endorsement_provided = True

        project_plan = Mock()
        project_plan.endorsements.all.return_value = [endorsement]

        validate_endorsement_requirements(project_plan)

    def test_endorsement_required_but_not_provided(self):
        """Test endorsement required but not provided"""
        endorsement = Mock()
        endorsement.ae_endorsement_required = True
        endorsement.ae_endorsement_provided = False

        project_plan = Mock()
        project_plan.endorsements.all.return_value = [endorsement]

        with pytest.raises(ValidationError, match="Animal Ethics"):
            validate_endorsement_requirements(project_plan)


# ============================================================================
# HELPER TESTS
# ============================================================================


class TestGetDocumentDisplayName:
    """Tests for get_document_display_name"""

    def test_concept_plan_display_name(self, project_document):
        """Test concept plan display name"""
        project_document.kind = "concept"
        result = get_document_display_name(project_document)

        assert "Concept Plan" in result
        assert project_document.project.title in result

    def test_project_plan_display_name(self, project_document):
        """Test project plan display name"""
        project_document.kind = "projectplan"
        result = get_document_display_name(project_document)

        assert "Project Plan" in result


class TestGetApprovalStageName:
    """Tests for get_approval_stage_name"""

    def test_stage_1_name(self):
        """Test stage 1 name"""
        assert get_approval_stage_name(1) == "Project Lead Approval"

    def test_stage_2_name(self):
        """Test stage 2 name"""
        assert get_approval_stage_name(2) == "Business Area Lead Approval"

    def test_stage_3_name(self):
        """Test stage 3 name"""
        assert get_approval_stage_name(3) == "Directorate Approval"

    def test_unknown_stage(self):
        """Test unknown stage"""
        assert "Stage 99" in get_approval_stage_name(99)


class TestGetDocumentStatusDisplay:
    """Tests for get_document_status_display"""

    def test_new_status(self):
        """Test new status display"""
        assert get_document_status_display("new") == "New Document"

    def test_approved_status(self):
        """Test approved status display"""
        assert get_document_status_display("approved") == "Approved"


class TestIsDocumentEditable:
    """Tests for is_document_editable"""

    def test_approved_document_not_editable(self, project_document, user):
        """Test approved document is not editable"""
        project_document.status = "approved"

        assert not is_document_editable(project_document, user)

    def test_non_member_cannot_edit(self, project_document, user_factory):
        """Test non-member cannot edit"""
        other_user = user_factory()

        assert not is_document_editable(project_document, other_user)

    def test_member_can_edit_new_document(self, project_document, user):
        """Test member can edit new document"""
        project_document.status = "new"

        assert is_document_editable(project_document, user)

    def test_only_leader_can_edit_in_approval(
        self, project_document, user, project_member
    ):
        """Test only leader can edit document in approval"""
        project_document.status = "inapproval"
        project_member.is_leader = True
        project_member.save()

        assert is_document_editable(project_document, user)


class TestGetNextApprovalStage:
    """Tests for get_next_approval_stage"""

    def test_next_stage_is_1(self, project_document):
        """Test next stage is 1"""
        project_document.project_lead_approval_granted = False

        assert get_next_approval_stage(project_document) == 1

    def test_next_stage_is_2(self, project_document):
        """Test next stage is 2"""
        project_document.project_lead_approval_granted = True
        project_document.business_area_lead_approval_granted = False

        assert get_next_approval_stage(project_document) == 2

    def test_next_stage_is_3(self, project_document):
        """Test next stage is 3"""
        project_document.project_lead_approval_granted = True
        project_document.business_area_lead_approval_granted = True
        project_document.directorate_approval_granted = False

        assert get_next_approval_stage(project_document) == 3

    def test_all_stages_complete(self, project_document):
        """Test all stages complete"""
        project_document.project_lead_approval_granted = True
        project_document.business_area_lead_approval_granted = True
        project_document.directorate_approval_granted = True

        assert get_next_approval_stage(project_document) is None


class TestFormatDocumentDate:
    """Tests for format_document_date"""

    def test_format_date(self):
        """Test date formatting"""
        date = datetime(2023, 12, 25)
        result = format_document_date(date)

        assert result == "25 December 2023"

    def test_none_date(self):
        """Test None date"""
        assert format_document_date(None) == ""


class TestGetDocumentYear:
    """Tests for get_document_year"""

    def test_get_year_from_project(self, project_document):
        """Test getting year from project"""
        result = get_document_year(project_document)

        assert result == project_document.project.year


class TestSanitizeHtmlContent:
    """Tests for sanitize_html_content"""

    def test_remove_script_tags(self):
        """Test removing script tags"""
        html = '<p>Hello</p><script>alert("xss")</script>'
        result = sanitize_html_content(html)

        assert "<script>" not in result
        assert "<p>Hello</p>" in result

    def test_remove_style_tags(self):
        """Test removing style tags"""
        html = "<p>Hello</p><style>body { color: red; }</style>"
        result = sanitize_html_content(html)

        assert "<style>" not in result
        assert "<p>Hello</p>" in result

    def test_empty_content(self):
        """Test empty content"""
        assert sanitize_html_content("") == ""
        assert sanitize_html_content(None) == ""


class TestExtractTextContent:
    """Tests for extract_text_content"""

    def test_extract_text(self):
        """Test extracting text from HTML"""
        html = "<p>Hello <strong>World</strong></p>"
        result = extract_text_content(html)

        assert result == "Hello World"

    def test_empty_content(self):
        """Test empty content"""
        assert extract_text_content("") == ""
        assert extract_text_content(None) == ""


class TestGetCurrentMaintainerId:
    """Tests for get_current_maintainer_id"""

    @patch("django.conf.settings")
    def test_get_from_settings(self, mock_settings):
        """Test getting maintainer ID from settings"""
        mock_settings.MAINTAINER_USER_ID = 123

        result = get_current_maintainer_id()

        assert result == 123

    @patch("django.conf.settings")
    def test_fallback_to_superuser(self, mock_settings, user_factory, db):
        """Test fallback to superuser"""
        mock_settings.MAINTAINER_USER_ID = None
        superuser = user_factory(is_superuser=True)

        result = get_current_maintainer_id()

        assert result == superuser.pk


class TestGetEncodedImage:
    """Tests for get_encoded_image"""

    @patch("builtins.open")
    @patch("os.path.join")
    def test_get_encoded_image_success(self, mock_join, mock_open):
        """Test successful image encoding"""
        mock_join.return_value = "/path/to/image.jpg"
        mock_open.return_value.__enter__.return_value.read.return_value = (
            b"fake_image_data"
        )

        result = get_encoded_image()

        assert result.startswith("data:image/jpeg;base64,")

    @patch("builtins.open", side_effect=FileNotFoundError)
    @patch("os.path.join")
    def test_get_encoded_image_not_found(self, mock_join, mock_open):
        """Test image not found"""
        result = get_encoded_image()

        assert result == ""


# ============================================================================
# HTML TABLE TESTS
# ============================================================================


class TestHTMLTableTemplates:
    """Tests for HTMLTableTemplates"""

    def test_get_staff_time_allocation_template(self):
        """Test getting staff time allocation template"""
        result = HTMLTableTemplates.get_staff_time_allocation_template()

        assert "<table" in result
        assert "Staff Time Allocation" in result or "table" in result.lower()

    def test_get_internal_budget_template(self):
        """Test getting internal budget template"""
        result = HTMLTableTemplates.get_internal_budget_template()

        assert "<table" in result

    def test_get_external_budget_template(self):
        """Test getting external budget template"""
        result = HTMLTableTemplates.get_external_budget_template()

        assert "<table" in result


class TestDefaultFunctions:
    """Tests for default callable functions"""

    def test_default_staff_time_allocation(self):
        """Test default staff time allocation callable"""
        result = default_staff_time_allocation()

        assert "<table" in result

    def test_default_internal_budget(self):
        """Test default internal budget callable"""
        result = default_internal_budget()

        assert "<table" in result

    def test_default_external_budget(self):
        """Test default external budget callable"""
        result = default_external_budget()

        assert "<table" in result


class TestConvenienceFunctions:
    """Tests for convenience wrapper functions"""

    def test_get_staff_time_allocation_template_function(self):
        """Test convenience function for staff time allocation"""
        from documents.utils.html_tables import get_staff_time_allocation_template

        result = get_staff_time_allocation_template()

        assert "<table" in result

    def test_get_internal_budget_template_function(self):
        """Test convenience function for internal budget"""
        from documents.utils.html_tables import get_internal_budget_template

        result = get_internal_budget_template()

        assert "<table" in result

    def test_get_external_budget_template_function(self):
        """Test convenience function for external budget"""
        from documents.utils.html_tables import get_external_budget_template

        result = get_external_budget_template()

        assert "<table" in result


class TestJsonToHtmlTable:
    """Tests for json_to_html_table"""

    def test_convert_simple_table(self):
        """Test converting simple JSON table"""
        data = [["Header1", "Header2"], ["Row1Col1", "Row1Col2"]]
        json_string = json.dumps(data)

        result = json_to_html_table(json_string)

        assert "<table" in result
        assert "Header1" in result
        assert "Row1Col1" in result

    def test_invalid_json(self):
        """Test invalid JSON returns original string"""
        invalid_json = "not valid json"

        result = json_to_html_table(invalid_json)

        assert result == invalid_json

    def test_empty_data(self):
        """Test empty data returns original string"""
        json_string = json.dumps([])

        result = json_to_html_table(json_string)

        assert result == json_string

    def test_non_list_data(self):
        """Test non-list data returns original string"""
        json_string = json.dumps({"key": "value"})

        result = json_to_html_table(json_string)

        assert result == json_string

    def test_table_with_multiple_rows(self):
        """Test table with multiple rows generates correct HTML structure"""
        data = [
            ["Header1", "Header2", "Header3"],
            ["Row1Col1", "Row1Col2", "Row1Col3"],
            ["Row2Col1", "Row2Col2", "Row2Col3"],
        ]
        json_string = json.dumps(data)

        result = json_to_html_table(json_string)

        # Check for header cells (first row and first column)
        assert "<th" in result
        assert "<td" in result
        # Check all data is present
        assert "Row2Col3" in result

    def test_none_input(self):
        """Test None input returns original"""
        result = json_to_html_table(None)

        assert result is None


# ============================================================================
# EMAIL TEMPLATE TESTS
# ============================================================================


class TestEmailTemplateRenderer:
    """Tests for EmailTemplateRenderer"""

    @patch("documents.utils.email_templates.render_to_string")
    def test_render_template(self, mock_render):
        """Test rendering email template"""
        from documents.utils.email_templates import EmailTemplateRenderer

        mock_render.return_value = "<html>Test</html>"

        result = EmailTemplateRenderer.render("test.html", {"key": "value"})

        assert result == "<html>Test</html>"
        mock_render.assert_called_once_with(
            "./email_templates/test.html", {"key": "value"}
        )

    @patch("documents.utils.email_templates.render_to_string")
    def test_render_document_email_approved(self, mock_render, project_document, user):
        """Test rendering approved document email"""
        from documents.utils.email_templates import EmailTemplateRenderer

        mock_render.return_value = "<html>Approved</html>"

        recipient = {"name": "John Doe", "email": "john@example.com"}
        subject, html = EmailTemplateRenderer.render_document_email(
            "approved", project_document, recipient, user
        )

        assert subject == "Document Approved"
        assert html == "<html>Approved</html>"

    @patch("documents.utils.email_templates.render_to_string")
    def test_render_document_email_recalled(self, mock_render, project_document, user):
        """Test rendering recalled document email"""
        from documents.utils.email_templates import EmailTemplateRenderer

        mock_render.return_value = "<html>Recalled</html>"

        recipient = {"name": "Jane Doe", "email": "jane@example.com"}
        subject, html = EmailTemplateRenderer.render_document_email(
            "recalled", project_document, recipient, user
        )

        assert subject == "Document Recalled"
        assert html == "<html>Recalled</html>"

    @patch("documents.utils.email_templates.render_to_string")
    def test_render_document_email_unknown_type(
        self, mock_render, project_document, user
    ):
        """Test rendering unknown email type falls back to default"""
        from documents.utils.email_templates import EmailTemplateRenderer

        mock_render.return_value = "<html>Default</html>"

        recipient = {"name": "Test User", "email": "test@example.com"}
        subject, html = EmailTemplateRenderer.render_document_email(
            "unknown_type", project_document, recipient, user
        )

        assert subject == "Notification"
        assert html == "<html>Default</html>"

    def test_get_template_context_basic(self, project_document, user):
        """Test building basic template context"""
        from documents.utils.email_templates import EmailTemplateRenderer

        context = EmailTemplateRenderer.get_template_context(
            document=project_document, recipient_name="John Doe", actioning_user=user
        )

        assert context["document"] == project_document
        assert context["recipient_name"] == "John Doe"
        assert context["actioning_user"] == user
        assert context["actioning_user_email"] == user.email

    def test_get_template_context_with_kwargs(self, project_document):
        """Test building template context with additional kwargs"""
        from documents.utils.email_templates import EmailTemplateRenderer

        context = EmailTemplateRenderer.get_template_context(
            document=project_document,
            recipient_name="Jane Doe",
            custom_field="custom_value",
            another_field=123,
        )

        assert context["custom_field"] == "custom_value"
        assert context["another_field"] == 123

    def test_get_template_context_no_actioning_user(self, project_document):
        """Test building template context without actioning user"""
        from documents.utils.email_templates import EmailTemplateRenderer

        context = EmailTemplateRenderer.get_template_context(
            document=project_document, recipient_name="Test User", actioning_user=None
        )

        assert context["actioning_user"] is None
        assert context["actioning_user_email"] is None


# ============================================================================
# ADDITIONAL FILTER TESTS
# ============================================================================


class TestApplyDocumentFiltersEdgeCases:
    """Additional tests for apply_document_filters edge cases"""

    def test_filter_by_business_area(self, project_document):
        """Test filtering by business area"""
        queryset = ProjectDocument.objects.filter(pk=project_document.pk)

        filters = {"business_area": project_document.project.business_area.pk}
        result = apply_document_filters(queryset, filters)

        assert result.count() == 1

    def test_filter_business_area_all(self, project_document):
        """Test business area filter with 'All' value"""
        queryset = ProjectDocument.objects.filter(pk=project_document.pk)

        filters = {"business_area": "All"}
        result = apply_document_filters(queryset, filters)

        # Should not filter when 'All' is specified
        assert result.count() == 1


class TestApplyAnnualReportFiltersEdgeCases:
    """Additional tests for apply_annual_report_filters edge cases"""

    def test_filter_by_date_range(self, annual_report):
        """Test filtering by date range"""
        from datetime import date

        from documents.models import AnnualReport

        queryset = AnnualReport.objects.filter(pk=annual_report.pk)

        # Set dates on annual report
        annual_report.date_open = date(2023, 1, 1)
        annual_report.date_closed = date(2023, 12, 31)
        annual_report.save()

        filters = {"date_from": date(2023, 1, 1), "date_to": date(2023, 12, 31)}
        result = apply_annual_report_filters(queryset, filters)

        assert result.count() == 1


# ============================================================================
# ADDITIONAL HELPER TESTS
# ============================================================================


class TestGetDocumentYearEdgeCases:
    """Additional tests for get_document_year edge cases"""

    def test_get_year_fallback_to_creation_year(self, project_document):
        """Test getting year falls back to creation year when no details exist"""
        # Document has no progress/student report details
        result = get_document_year(project_document)

        # Should fall back to project year or creation year
        assert result in [
            project_document.project.year,
            project_document.created_at.year,
        ]


# ============================================================================
# ADDITIONAL VALIDATOR TESTS
# ============================================================================


class TestValidateEndorsementRequirementsEdgeCases:
    """Additional tests for validate_endorsement_requirements edge cases"""

    def test_no_endorsements_attribute(self):
        """Test project plan without endorsements attribute"""
        project_plan = Mock(spec=[])  # No endorsements attribute

        # Should not raise error
        validate_endorsement_requirements(project_plan)
