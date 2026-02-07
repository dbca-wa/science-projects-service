"""
Tests for agencies models
"""

import pytest
from django.db import IntegrityError

from agencies.models import (
    Affiliation,
    Agency,
    Branch,
    BusinessArea,
    DepartmentalService,
    Division,
)


class TestAffiliation:
    """Tests for Affiliation model"""

    def test_create_affiliation(self, db):
        """Test creating an affiliation"""
        # Arrange & Act
        affiliation = Affiliation.objects.create(name="Test Affiliation")

        # Assert
        assert affiliation.id is not None
        assert affiliation.name == "Test Affiliation"
        assert str(affiliation) == "Test Affiliation"

    def test_affiliation_name_unique(self, db):
        """Test affiliation name must be unique"""
        # Arrange
        Affiliation.objects.create(name="Duplicate Name")

        # Act & Assert
        with pytest.raises(IntegrityError):
            Affiliation.objects.create(name="Duplicate Name")

    def test_affiliation_str_method(self, affiliation, db):
        """Test affiliation string representation"""
        # Act
        result = str(affiliation)

        # Assert
        assert result == affiliation.name

    def test_affiliation_meta_verbose_names(self, db):
        """Test affiliation meta verbose names"""
        # Act
        meta = Affiliation._meta

        # Assert
        assert meta.verbose_name == "Affiliation"
        assert meta.verbose_name_plural == "Affiliations"


class TestAgency:
    """Tests for Agency model"""

    def test_create_agency(self, user, db):
        """Test creating an agency"""
        # Arrange & Act
        agency = Agency.objects.create(
            name="Test Agency",
            key_stakeholder=user,
            is_active=True,
        )

        # Assert
        assert agency.id is not None
        assert agency.name == "Test Agency"
        assert agency.key_stakeholder == user
        assert agency.is_active is True
        assert str(agency) == "Test Agency"

    def test_create_agency_without_stakeholder(self, db):
        """Test creating agency without key stakeholder"""
        # Arrange & Act
        agency = Agency.objects.create(
            name="Test Agency",
            is_active=True,
        )

        # Assert
        assert agency.id is not None
        assert agency.key_stakeholder is None

    def test_agency_default_is_active(self, db):
        """Test agency is_active defaults to True"""
        # Arrange & Act
        agency = Agency.objects.create(name="Test Agency")

        # Assert
        assert agency.is_active is True

    def test_agency_str_method(self, agency, db):
        """Test agency string representation"""
        # Act
        result = str(agency)

        # Assert
        assert result == agency.name

    def test_agency_meta_verbose_names(self, db):
        """Test agency meta verbose names"""
        # Act
        meta = Agency._meta

        # Assert
        assert meta.verbose_name == "Agency"
        assert meta.verbose_name_plural == "Agencies"

    def test_agency_key_stakeholder_set_null_on_delete(self, user, db):
        """Test key_stakeholder is set to null when user is deleted"""
        # Arrange
        agency = Agency.objects.create(
            name="Test Agency",
            key_stakeholder=user,
        )
        user.id

        # Act
        user.delete()
        agency.refresh_from_db()

        # Assert
        assert agency.key_stakeholder is None


class TestBranch:
    """Tests for Branch model"""

    def test_create_branch(self, agency, user, db):
        """Test creating a branch"""
        # Arrange & Act
        branch = Branch.objects.create(
            agency=agency,
            name="Test Branch",
            manager=user,
        )

        # Assert
        assert branch.id is not None
        assert branch.agency == agency
        assert branch.name == "Test Branch"
        assert branch.manager == user
        assert str(branch) == "Test Branch"

    def test_create_branch_without_agency(self, db):
        """Test creating branch without agency"""
        # Arrange & Act
        branch = Branch.objects.create(
            name="Test Branch",
        )

        # Assert
        assert branch.id is not None
        assert branch.agency is None

    def test_create_branch_without_manager(self, agency, db):
        """Test creating branch without manager"""
        # Arrange & Act
        branch = Branch.objects.create(
            agency=agency,
            name="Test Branch",
        )

        # Assert
        assert branch.id is not None
        assert branch.manager is None

    def test_branch_unique_together_agency_name(self, agency, db):
        """Test branch name must be unique per agency"""
        # Arrange
        Branch.objects.create(
            agency=agency,
            name="Duplicate Branch",
        )

        # Act & Assert
        with pytest.raises(IntegrityError):
            Branch.objects.create(
                agency=agency,
                name="Duplicate Branch",
            )

    def test_branch_same_name_different_agency(self, agency, user, db):
        """Test branch can have same name in different agencies"""
        # Arrange
        agency2 = Agency.objects.create(name="Agency 2")
        Branch.objects.create(
            agency=agency,
            name="Same Name",
        )

        # Act
        branch2 = Branch.objects.create(
            agency=agency2,
            name="Same Name",
        )

        # Assert
        assert branch2.id is not None

    def test_branch_str_method(self, branch, db):
        """Test branch string representation"""
        # Act
        result = str(branch)

        # Assert
        assert result == branch.name

    def test_branch_meta_verbose_names(self, db):
        """Test branch meta verbose names"""
        # Act
        meta = Branch._meta

        # Assert
        assert meta.verbose_name == "Branch"
        assert meta.verbose_name_plural == "Branches"

    def test_branch_cascade_delete_with_agency(self, agency, db):
        """Test branch is deleted when agency is deleted"""
        # Arrange
        branch = Branch.objects.create(
            agency=agency,
            name="Test Branch",
        )
        branch_id = branch.id

        # Act
        agency.delete()

        # Assert
        assert not Branch.objects.filter(id=branch_id).exists()


class TestBusinessArea:
    """Tests for BusinessArea model"""

    def test_create_business_area(self, agency, division, user, db):
        """Test creating a business area"""
        # Arrange & Act
        ba = BusinessArea.objects.create(
            agency=agency,
            name="Test BA",
            slug="test-ba",
            division=division,
            leader=user,
            finance_admin=user,
            data_custodian=user,
            caretaker=user,
            is_active=True,
            published=False,
        )

        # Assert
        assert ba.id is not None
        assert ba.agency == agency
        assert ba.name == "Test BA"
        assert ba.slug == "test-ba"
        assert ba.division == division
        assert ba.leader == user
        assert ba.finance_admin == user
        assert ba.data_custodian == user
        assert ba.caretaker == user
        assert ba.is_active is True
        assert ba.published is False
        assert str(ba) == "Test BA"

    def test_create_business_area_minimal(self, agency, db):
        """Test creating business area with minimal fields"""
        # Arrange & Act
        ba = BusinessArea.objects.create(
            agency=agency,
            name="Minimal BA",
            leader=None,
            finance_admin=None,
            data_custodian=None,
        )

        # Assert
        assert ba.id is not None
        assert ba.agency == agency
        assert ba.name == "Minimal BA"
        assert ba.division is None
        assert ba.leader is None
        assert ba.finance_admin is None
        assert ba.data_custodian is None
        assert ba.is_active is True
        assert ba.published is False

    def test_business_area_default_values(self, agency, db):
        """Test business area default values"""
        # Arrange & Act
        ba = BusinessArea.objects.create(
            agency=agency,
            name="Test BA",
            leader=None,
            finance_admin=None,
            data_custodian=None,
        )

        # Assert
        assert ba.published is False
        assert ba.is_active is True

    def test_business_area_unique_together_name_agency(self, agency, db):
        """Test business area name must be unique per agency"""
        # Arrange
        BusinessArea.objects.create(
            agency=agency,
            name="Duplicate BA",
        )

        # Act & Assert
        with pytest.raises(IntegrityError):
            BusinessArea.objects.create(
                agency=agency,
                name="Duplicate BA",
            )

    def test_business_area_same_name_different_agency(self, agency, user, db):
        """Test business area can have same name in different agencies"""
        # Arrange
        agency2 = Agency.objects.create(name="Agency 2")
        BusinessArea.objects.create(
            agency=agency,
            name="Same Name",
            leader=None,
            finance_admin=None,
            data_custodian=None,
        )

        # Act
        ba2 = BusinessArea.objects.create(
            agency=agency2,
            name="Same Name",
            leader=None,
            finance_admin=None,
            data_custodian=None,
        )

        # Assert
        assert ba2.id is not None

    def test_business_area_str_method(self, business_area, db):
        """Test business area string representation"""
        # Act
        result = str(business_area)

        # Assert
        assert result == business_area.name

    def test_business_area_meta_verbose_names(self, db):
        """Test business area meta verbose names"""
        # Act
        meta = BusinessArea._meta

        # Assert
        assert meta.verbose_name == "Business Area"
        assert meta.verbose_name_plural == "Business Areas"

    def test_business_area_cascade_delete_with_agency(self, agency, db):
        """Test business area is deleted when agency is deleted"""
        # Arrange
        ba = BusinessArea.objects.create(
            agency=agency,
            name="Test BA",
            leader=None,
            finance_admin=None,
            data_custodian=None,
        )
        ba_id = ba.id

        # Act
        agency.delete()

        # Assert
        assert not BusinessArea.objects.filter(id=ba_id).exists()

    def test_business_area_division_set_null_on_delete(self, agency, division, db):
        """Test division is set to null when division is deleted"""
        # Arrange
        ba = BusinessArea.objects.create(
            agency=agency,
            name="Test BA",
            division=division,
            leader=None,
            finance_admin=None,
            data_custodian=None,
        )

        # Act
        division.delete()
        ba.refresh_from_db()

        # Assert
        assert ba.division is None

    def test_business_area_leader_set_null_on_delete(self, agency, user, db):
        """Test leader is set to null when user is deleted"""
        # Arrange
        ba = BusinessArea.objects.create(
            agency=agency,
            name="Test BA",
            leader=user,
            finance_admin=None,
            data_custodian=None,
        )

        # Act
        user.delete()
        ba.refresh_from_db()

        # Assert
        assert ba.leader is None


class TestDivision:
    """Tests for Division model"""

    def test_create_division(self, user, db):
        """Test creating a division"""
        # Arrange & Act
        division = Division.objects.create(
            name="Test Division",
            slug="test-division",
            director=user,
            approver=user,
        )

        # Assert
        assert division.id is not None
        assert division.name == "Test Division"
        assert division.slug == "test-division"
        assert division.director == user
        assert division.approver == user
        assert str(division) == "Test Division"

    def test_create_division_minimal(self, db):
        """Test creating division with minimal fields"""
        # Arrange & Act
        division = Division.objects.create(
            name="Minimal Division",
            slug="minimal-division",
        )

        # Assert
        assert division.id is not None
        assert division.director is None
        assert division.approver is None

    def test_division_str_method(self, division, db):
        """Test division string representation"""
        # Act
        result = str(division)

        # Assert
        assert result == division.name

    def test_division_meta_verbose_names(self, db):
        """Test division meta verbose names"""
        # Act
        meta = Division._meta

        # Assert
        assert meta.verbose_name == "Department Division"
        assert meta.verbose_name_plural == "Department Divisions"

    def test_division_director_set_null_on_delete(self, user, db):
        """Test director is set to null when user is deleted"""
        # Arrange
        division = Division.objects.create(
            name="Test Division",
            slug="test-division",
            director=user,
        )

        # Act
        user.delete()
        division.refresh_from_db()

        # Assert
        assert division.director is None

    def test_division_email_list_many_to_many(self, division, user, db):
        """Test division email list many-to-many relationship"""
        # Arrange
        from common.tests.factories import UserFactory

        user1 = UserFactory()
        user2 = UserFactory()

        # Act
        division.directorate_email_list.add(user1, user2)

        # Assert
        assert division.directorate_email_list.count() == 2
        assert user1 in division.directorate_email_list.all()
        assert user2 in division.directorate_email_list.all()


class TestDepartmentalService:
    """Tests for DepartmentalService model"""

    def test_create_departmental_service(self, user, db):
        """Test creating a departmental service"""
        # Arrange & Act
        service = DepartmentalService.objects.create(
            name="Test Service",
            director=user,
        )

        # Assert
        assert service.id is not None
        assert service.name == "Test Service"
        assert service.director == user
        assert str(service) == "Dept. Service: Test Service"

    def test_create_departmental_service_without_director(self, db):
        """Test creating departmental service without director"""
        # Arrange & Act
        service = DepartmentalService.objects.create(
            name="Test Service",
        )

        # Assert
        assert service.id is not None
        assert service.director is None

    def test_departmental_service_str_method(self, departmental_service, db):
        """Test departmental service string representation"""
        # Act
        result = str(departmental_service)

        # Assert
        assert result == f"Dept. Service: {departmental_service.name}"

    def test_departmental_service_meta_verbose_names(self, db):
        """Test departmental service meta verbose names"""
        # Act
        meta = DepartmentalService._meta

        # Assert
        assert meta.verbose_name == "Departmental Service"
        assert meta.verbose_name_plural == "Departmental Services"

    def test_departmental_service_director_set_null_on_delete(self, user, db):
        """Test director is set to null when user is deleted"""
        # Arrange
        service = DepartmentalService.objects.create(
            name="Test Service",
            director=user,
        )

        # Act
        user.delete()
        service.refresh_from_db()

        # Assert
        assert service.director is None
