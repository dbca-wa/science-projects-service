"""
Tests for document permissions
"""

from unittest.mock import Mock

from documents.permissions.annual_report_permissions import (
    CanEditAnnualReport,
    CanGenerateAnnualReportPDF,
    CanPublishAnnualReport,
    CanViewAnnualReport,
)
from documents.permissions.document_permissions import (
    CanApproveDocument,
    CanDeleteDocument,
    CanEditDocument,
    CanGeneratePDF,
    CanRecallDocument,
    CanViewDocument,
)

# ============================================================================
# DOCUMENT PERMISSION TESTS
# ============================================================================


class TestCanViewDocument:
    """Tests for CanViewDocument permission"""

    def test_superuser_can_view(self, project_document, user_factory, db):
        """Test superuser can view any document"""
        superuser = user_factory(is_superuser=True)
        request = Mock(user=superuser)

        permission = CanViewDocument()
        assert permission.has_object_permission(request, None, project_document)

    def test_project_member_can_view(self, project_document, user, db):
        """Test project member can view document"""
        request = Mock(user=user)

        permission = CanViewDocument()
        assert permission.has_object_permission(request, None, project_document)

    def test_business_area_leader_can_view(self, project_with_ba_lead, ba_lead, db):
        """Test business area leader can view document"""
        from common.tests.factories import ProjectDocumentFactory

        document = ProjectDocumentFactory(project=project_with_ba_lead)
        request = Mock(user=ba_lead)

        permission = CanViewDocument()
        assert permission.has_object_permission(request, None, document)

    def test_director_can_view(self, project_document, director, db):
        """Test director can view document"""
        # Set director on division
        if project_document.project.business_area.division:
            project_document.project.business_area.division.director = director
            project_document.project.business_area.division.save()

        request = Mock(user=director)

        permission = CanViewDocument()
        assert permission.has_object_permission(request, None, project_document)

    def test_non_member_cannot_view(self, project_document, user_factory, db):
        """Test non-member cannot view document"""
        other_user = user_factory()
        request = Mock(user=other_user)

        permission = CanViewDocument()
        assert not permission.has_object_permission(request, None, project_document)

    def test_non_member_non_leader_cannot_view_when_no_division(
        self, project_document, user_factory, db
    ):
        """Test non-member cannot view when business area has no division"""
        # Remove division from business area
        project_document.project.business_area.division = None
        project_document.project.business_area.save()

        # Create a user who is not a member, not BA leader, and not director
        other_user = user_factory()
        request = Mock(user=other_user)

        permission = CanViewDocument()
        assert not permission.has_object_permission(request, None, project_document)


class TestCanEditDocument:
    """Tests for CanEditDocument permission"""

    def test_superuser_can_edit(self, project_document, user_factory, db):
        """Test superuser can edit any document"""
        superuser = user_factory(is_superuser=True)
        request = Mock(user=superuser)

        permission = CanEditDocument()
        assert permission.has_object_permission(request, None, project_document)

    def test_project_member_can_edit(self, project_document, user, db):
        """Test project member can edit document"""
        request = Mock(user=user)

        permission = CanEditDocument()
        assert permission.has_object_permission(request, None, project_document)

    def test_cannot_edit_approved_document(self, project_document, user, db):
        """Test cannot edit approved document"""
        project_document.status = "approved"
        project_document.save()

        request = Mock(user=user)

        permission = CanEditDocument()
        assert not permission.has_object_permission(request, None, project_document)

    def test_non_member_cannot_edit(self, project_document, user_factory, db):
        """Test non-member cannot edit document"""
        other_user = user_factory()
        request = Mock(user=other_user)

        permission = CanEditDocument()
        assert not permission.has_object_permission(request, None, project_document)


class TestCanApproveDocument:
    """Tests for CanApproveDocument permission"""

    def test_superuser_can_approve(self, project_document, user_factory, db):
        """Test superuser can approve any document"""
        project_document.status = "inapproval"
        project_document.save()

        superuser = user_factory(is_superuser=True)
        request = Mock(user=superuser)

        permission = CanApproveDocument()
        assert permission.has_object_permission(request, None, project_document)

    def test_project_lead_can_approve_stage_1(
        self, project_document, user, project_member, db
    ):
        """Test project lead can approve stage 1"""
        project_document.status = "inapproval"
        project_document.project_lead_approval_granted = False
        project_document.save()

        project_member.is_leader = True
        project_member.save()

        request = Mock(user=user)

        permission = CanApproveDocument()
        assert permission.has_object_permission(request, None, project_document)

    def test_ba_leader_can_approve_stage_2(self, project_with_ba_lead, ba_lead, db):
        """Test business area leader can approve stage 2"""
        from common.tests.factories import ProjectDocumentFactory

        document = ProjectDocumentFactory(project=project_with_ba_lead)
        document.status = "inapproval"
        document.project_lead_approval_granted = True
        document.business_area_lead_approval_granted = False
        document.save()

        request = Mock(user=ba_lead)

        permission = CanApproveDocument()
        assert permission.has_object_permission(request, None, document)

    def test_director_can_approve_stage_3(self, project_document, director, db):
        """Test director can approve stage 3"""
        project_document.status = "inapproval"
        project_document.project_lead_approval_granted = True
        project_document.business_area_lead_approval_granted = True
        project_document.directorate_approval_granted = False
        project_document.save()

        # Set director on division
        if project_document.project.business_area.division:
            project_document.project.business_area.division.director = director
            project_document.project.business_area.division.save()

        request = Mock(user=director)

        permission = CanApproveDocument()
        assert permission.has_object_permission(request, None, project_document)

    def test_cannot_approve_non_approval_status(self, project_document, user, db):
        """Test cannot approve document not in approval status"""
        project_document.status = "new"
        project_document.save()

        request = Mock(user=user)

        permission = CanApproveDocument()
        assert not permission.has_object_permission(request, None, project_document)

    def test_wrong_user_cannot_approve_stage(self, project_document, user_factory, db):
        """Test wrong user cannot approve stage"""
        project_document.status = "inapproval"
        project_document.project_lead_approval_granted = False
        project_document.save()

        other_user = user_factory()
        request = Mock(user=other_user)

        permission = CanApproveDocument()
        assert not permission.has_object_permission(request, None, project_document)

    def test_cannot_approve_stage_3_when_no_division(
        self, project_document, user_factory, db
    ):
        """Test cannot approve stage 3 when business area has no division"""
        project_document.status = "inapproval"
        project_document.project_lead_approval_granted = True
        project_document.business_area_lead_approval_granted = True
        project_document.directorate_approval_granted = False
        project_document.save()

        # Remove division from business area
        project_document.project.business_area.division = None
        project_document.project.business_area.save()

        # Use a non-superuser who would otherwise be able to approve
        other_user = user_factory()
        request = Mock(user=other_user)

        permission = CanApproveDocument()
        assert not permission.has_object_permission(request, None, project_document)


class TestCanRecallDocument:
    """Tests for CanRecallDocument permission"""

    def test_superuser_can_recall(self, project_document, user_factory, db):
        """Test superuser can recall document"""
        project_document.status = "inapproval"
        project_document.save()

        superuser = user_factory(is_superuser=True)
        request = Mock(user=superuser)

        permission = CanRecallDocument()
        assert permission.has_object_permission(request, None, project_document)

    def test_project_lead_can_recall(self, project_document, user, project_member, db):
        """Test project lead can recall document"""
        project_document.status = "inapproval"
        project_document.save()

        project_member.is_leader = True
        project_member.save()

        request = Mock(user=user)

        permission = CanRecallDocument()
        assert permission.has_object_permission(request, None, project_document)

    def test_cannot_recall_non_approval_status(
        self, project_document, user, project_member, db
    ):
        """Test cannot recall document not in approval"""
        project_document.status = "new"
        project_document.save()

        project_member.is_leader = True
        project_member.save()

        request = Mock(user=user)

        permission = CanRecallDocument()
        assert not permission.has_object_permission(request, None, project_document)

    def test_non_lead_cannot_recall(self, project_document, user_factory, db):
        """Test non-lead cannot recall document"""
        project_document.status = "inapproval"
        project_document.save()

        # Create a non-lead user
        non_lead = user_factory()
        request = Mock(user=non_lead)

        permission = CanRecallDocument()
        assert not permission.has_object_permission(request, None, project_document)


class TestCanDeleteDocument:
    """Tests for CanDeleteDocument permission"""

    def test_superuser_can_delete(self, project_document, user_factory, db):
        """Test superuser can delete any document"""
        superuser = user_factory(is_superuser=True)
        request = Mock(user=superuser)

        permission = CanDeleteDocument()
        assert permission.has_object_permission(request, None, project_document)

    def test_project_lead_can_delete(self, project_document, user, project_member, db):
        """Test project lead can delete document"""
        project_member.is_leader = True
        project_member.save()

        request = Mock(user=user)

        permission = CanDeleteDocument()
        assert permission.has_object_permission(request, None, project_document)

    def test_cannot_delete_approved_document(
        self, project_document, user, project_member, db
    ):
        """Test cannot delete approved document"""
        project_document.status = "approved"
        project_document.save()

        project_member.is_leader = True
        project_member.save()

        request = Mock(user=user)

        permission = CanDeleteDocument()
        assert not permission.has_object_permission(request, None, project_document)

    def test_non_lead_cannot_delete(self, project_document, user_factory, db):
        """Test non-lead cannot delete document"""
        # Create a non-lead user
        non_lead = user_factory()
        request = Mock(user=non_lead)

        permission = CanDeleteDocument()
        assert not permission.has_object_permission(request, None, project_document)


class TestCanGeneratePDF:
    """Tests for CanGeneratePDF permission"""

    def test_superuser_can_generate_pdf(self, project_document, user_factory, db):
        """Test superuser can generate PDF"""
        project_document.status = "approved"
        project_document.save()

        superuser = user_factory(is_superuser=True)
        request = Mock(user=superuser)

        permission = CanGeneratePDF()
        assert permission.has_object_permission(request, None, project_document)

    def test_project_member_can_generate_pdf(self, project_document, user, db):
        """Test project member can generate PDF for approved document"""
        project_document.status = "approved"
        project_document.save()

        request = Mock(user=user)

        permission = CanGeneratePDF()
        assert permission.has_object_permission(request, None, project_document)

    def test_ba_leader_can_generate_pdf(self, project_with_ba_lead, ba_lead, db):
        """Test business area leader can generate PDF"""
        from common.tests.factories import ProjectDocumentFactory

        document = ProjectDocumentFactory(project=project_with_ba_lead)
        document.status = "approved"
        document.save()

        request = Mock(user=ba_lead)

        permission = CanGeneratePDF()
        assert permission.has_object_permission(request, None, document)

    def test_cannot_generate_pdf_for_non_approved(self, project_document, user, db):
        """Test cannot generate PDF for non-approved document"""
        project_document.status = "new"
        project_document.save()

        request = Mock(user=user)

        permission = CanGeneratePDF()
        assert not permission.has_object_permission(request, None, project_document)

    def test_non_member_cannot_generate_pdf(self, project_document, user_factory, db):
        """Test non-member cannot generate PDF"""
        project_document.status = "approved"
        project_document.save()

        other_user = user_factory()
        request = Mock(user=other_user)

        permission = CanGeneratePDF()
        assert not permission.has_object_permission(request, None, project_document)


# ============================================================================
# ANNUAL REPORT PERMISSION TESTS
# ============================================================================


class TestCanViewAnnualReport:
    """Tests for CanViewAnnualReport permission"""

    def test_authenticated_user_can_view(self, user_factory, db):
        """Test authenticated user can view annual reports"""
        user = user_factory()
        request = Mock(user=user)
        # User objects have is_authenticated as a property that returns True
        # No need to set it - it's already True for real User objects

        permission = CanViewAnnualReport()
        assert permission.has_permission(request, None)

    def test_unauthenticated_user_cannot_view(self, db):
        """Test unauthenticated user cannot view annual reports"""
        user = Mock()
        user.is_authenticated = False
        request = Mock(user=user)

        permission = CanViewAnnualReport()
        assert not permission.has_permission(request, None)


class TestCanEditAnnualReport:
    """Tests for CanEditAnnualReport permission"""

    def test_superuser_can_edit(self, user_factory, db):
        """Test superuser can edit annual reports"""
        superuser = user_factory(is_superuser=True)
        request = Mock(user=superuser)

        permission = CanEditAnnualReport()
        assert permission.has_permission(request, None)

    def test_staff_can_edit(self, user_factory, db):
        """Test staff can edit annual reports"""
        staff_user = user_factory(is_staff=True)
        request = Mock(user=staff_user)

        permission = CanEditAnnualReport()
        assert permission.has_permission(request, None)

    def test_regular_user_cannot_edit(self, user_factory, db):
        """Test regular user cannot edit annual reports"""
        user = user_factory()
        request = Mock(user=user)

        permission = CanEditAnnualReport()
        assert not permission.has_permission(request, None)


class TestCanPublishAnnualReport:
    """Tests for CanPublishAnnualReport permission"""

    def test_superuser_can_publish(self, user_factory, db):
        """Test superuser can publish annual reports"""
        superuser = user_factory(is_superuser=True)
        request = Mock(user=superuser)

        permission = CanPublishAnnualReport()
        assert permission.has_permission(request, None)

    def test_director_can_publish(self, director, db):
        """Test director can publish annual reports"""
        from agencies.models import Division

        # Create a division with director
        Division.objects.create(
            name="Test Division",
            director=director,
        )

        request = Mock(user=director)

        permission = CanPublishAnnualReport()
        assert permission.has_permission(request, None)

    def test_regular_user_cannot_publish(self, user_factory, db):
        """Test regular user cannot publish annual reports"""
        user = user_factory()
        request = Mock(user=user)

        permission = CanPublishAnnualReport()
        assert not permission.has_permission(request, None)

    def test_user_without_director_of_cannot_publish(self, user_factory, db):
        """Test user without director_of attribute cannot publish"""
        user = user_factory()
        # Ensure user doesn't have director_of attribute
        if hasattr(user, "director_of"):
            delattr(user, "director_of")

        request = Mock(user=user)

        permission = CanPublishAnnualReport()
        assert not permission.has_permission(request, None)


class TestCanGenerateAnnualReportPDF:
    """Tests for CanGenerateAnnualReportPDF permission"""

    def test_superuser_can_generate(self, user_factory, db):
        """Test superuser can generate annual report PDFs"""
        superuser = user_factory(is_superuser=True)
        request = Mock(user=superuser)

        permission = CanGenerateAnnualReportPDF()
        assert permission.has_permission(request, None)

    def test_staff_can_generate(self, user_factory, db):
        """Test staff can generate annual report PDFs"""
        staff_user = user_factory(is_staff=True)
        request = Mock(user=staff_user)

        permission = CanGenerateAnnualReportPDF()
        assert permission.has_permission(request, None)

    def test_regular_user_cannot_generate(self, user_factory, db):
        """Test regular user cannot generate annual report PDFs"""
        user = user_factory()
        request = Mock(user=user)

        permission = CanGenerateAnnualReportPDF()
        assert not permission.has_permission(request, None)
