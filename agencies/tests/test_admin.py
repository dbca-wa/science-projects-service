"""
Tests for agencies admin
"""

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model

from agencies.admin import (
    AffiliationAdmin,
    AgencyAdmin,
    BranchAdmin,
    BusinessAreaAdmin,
    DepartmentalServiceAdmin,
    DivisionAdmin,
)
from agencies.models import (
    Affiliation,
    Agency,
    Branch,
    BusinessArea,
    DepartmentalService,
    Division,
)

User = get_user_model()


class TestAffiliationAdmin:
    """Tests for AffiliationAdmin"""

    def test_list_display(self, db):
        """Test list_display configuration"""
        # Arrange
        admin = AffiliationAdmin(Affiliation, AdminSite())

        # Act & Assert
        assert "name" in admin.list_display
        assert "created_at" in admin.list_display
        assert "updated_at" in admin.list_display

    def test_ordering(self, db):
        """Test ordering configuration"""
        # Arrange
        admin = AffiliationAdmin(Affiliation, AdminSite())

        # Act & Assert
        assert admin.ordering == ["name"]

    def test_actions_configured(self, db):
        """Test admin actions are configured"""
        # Arrange
        admin = AffiliationAdmin(Affiliation, AdminSite())

        # Act & Assert
        assert len(admin.actions) > 0
        # Check that our custom actions are present
        action_names = [
            action.__name__ if callable(action) else action for action in admin.actions
        ]
        assert any(
            "export" in str(name).lower()
            or "fix" in str(name).lower()
            or "clean" in str(name).lower()
            or "migrate" in str(name).lower()
            for name in action_names
        )


class TestAgencyAdmin:
    """Tests for AgencyAdmin"""

    def test_list_display(self, db):
        """Test list_display configuration"""
        # Arrange
        admin = AgencyAdmin(Agency, AdminSite())

        # Act & Assert
        assert "name" in admin.list_display
        assert "key_stakeholder" in admin.list_display

    def test_search_fields(self, db):
        """Test search_fields configuration"""
        # Arrange
        admin = AgencyAdmin(Agency, AdminSite())

        # Act & Assert
        assert "name" in admin.search_fields


class TestBranchAdmin:
    """Tests for BranchAdmin"""

    def test_list_display(self, db):
        """Test list_display configuration"""
        # Arrange
        admin = BranchAdmin(Branch, AdminSite())

        # Act & Assert
        assert "name" in admin.list_display
        assert "agency" in admin.list_display
        assert "manager" in admin.list_display

    def test_search_fields(self, db):
        """Test search_fields configuration"""
        # Arrange
        admin = BranchAdmin(Branch, AdminSite())

        # Act & Assert
        assert "name" in admin.search_fields

    def test_ordering(self, db):
        """Test ordering configuration"""
        # Arrange
        admin = BranchAdmin(Branch, AdminSite())

        # Act & Assert
        assert admin.ordering == ["name"]


class TestBusinessAreaAdmin:
    """Tests for BusinessAreaAdmin"""

    def test_list_display(self, db):
        """Test list_display configuration"""
        # Arrange
        admin = BusinessAreaAdmin(BusinessArea, AdminSite())

        # Act & Assert
        assert "name" in admin.list_display
        assert "division" in admin.list_display
        assert "focus" in admin.list_display
        assert "leader" in admin.list_display

    def test_search_fields(self, db):
        """Test search_fields configuration"""
        # Arrange
        admin = BusinessAreaAdmin(BusinessArea, AdminSite())

        # Act & Assert
        assert "name" in admin.search_fields
        assert "focus" in admin.search_fields
        assert "leader" in admin.search_fields

    def test_ordering(self, db):
        """Test ordering configuration"""
        # Arrange
        admin = BusinessAreaAdmin(BusinessArea, AdminSite())

        # Act & Assert
        assert admin.ordering == ["name"]


class TestDivisionAdmin:
    """Tests for DivisionAdmin"""

    def test_list_display(self, db):
        """Test list_display configuration"""
        # Arrange
        admin = DivisionAdmin(Division, AdminSite())

        # Act & Assert
        assert "name" in admin.list_display
        assert "approver" in admin.list_display
        assert "director" in admin.list_display

    def test_list_filter(self, db):
        """Test list_filter configuration"""
        # Arrange
        admin = DivisionAdmin(Division, AdminSite())

        # Act & Assert
        assert "approver" in admin.list_filter
        assert "director" in admin.list_filter

    def test_search_fields(self, db):
        """Test search_fields configuration"""
        # Arrange
        admin = DivisionAdmin(Division, AdminSite())

        # Act & Assert
        assert "name" in admin.search_fields

    def test_ordering(self, db):
        """Test ordering configuration"""
        # Arrange
        admin = DivisionAdmin(Division, AdminSite())

        # Act & Assert
        assert admin.ordering == ["name"]


class TestDepartmentalServiceAdmin:
    """Tests for DepartmentalServiceAdmin"""

    def test_list_display(self, db):
        """Test list_display configuration"""
        # Arrange
        admin = DepartmentalServiceAdmin(DepartmentalService, AdminSite())

        # Act & Assert
        assert "name" in admin.list_display
        assert "director" in admin.list_display

    def test_list_filter(self, db):
        """Test list_filter configuration"""
        # Arrange
        admin = DepartmentalServiceAdmin(DepartmentalService, AdminSite())

        # Act & Assert
        assert "director" in admin.list_filter

    def test_search_fields(self, db):
        """Test search_fields configuration"""
        # Arrange
        admin = DepartmentalServiceAdmin(DepartmentalService, AdminSite())

        # Act & Assert
        assert "name" in admin.search_fields

    def test_ordering(self, db):
        """Test ordering configuration"""
        # Arrange
        admin = DepartmentalServiceAdmin(DepartmentalService, AdminSite())

        # Act & Assert
        assert admin.ordering == ["name"]
