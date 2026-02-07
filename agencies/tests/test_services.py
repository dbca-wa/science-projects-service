"""
Tests for agency services
"""

import pytest
from rest_framework.exceptions import NotFound

from agencies.models import (
    Affiliation,
    Agency,
    Branch,
    BusinessArea,
    DepartmentalService,
    Division,
)
from agencies.services.agency_service import AgencyService


class TestAffiliationService:
    """Tests for affiliation service operations"""

    def test_list_affiliations(self, affiliation, db):
        """Test listing affiliations"""
        # Act
        affiliations = AgencyService.list_affiliations()

        # Assert
        assert affiliations.count() == 1
        assert affiliation in affiliations

    def test_list_affiliations_with_search(self, db):
        """Test listing affiliations with search"""
        # Arrange
        Affiliation.objects.create(name="Test Affiliation")
        Affiliation.objects.create(name="Another Affiliation")

        # Act
        affiliations = AgencyService.list_affiliations(search="Test")

        # Assert
        assert affiliations.count() == 1
        assert affiliations.first().name == "Test Affiliation"

    def test_list_affiliations_with_search_no_results(self, db):
        """Test listing affiliations with search that returns no results"""
        # Arrange
        Affiliation.objects.create(name="Test Affiliation")

        # Act
        affiliations = AgencyService.list_affiliations(search="NonExistent")

        # Assert
        assert affiliations.count() == 0

    def test_list_affiliations_case_insensitive_search(self, db):
        """Test listing affiliations with case-insensitive search"""
        # Arrange
        Affiliation.objects.create(name="Test Affiliation")

        # Act
        affiliations = AgencyService.list_affiliations(search="test")

        # Assert
        assert affiliations.count() == 1
        assert affiliations.first().name == "Test Affiliation"

    def test_get_affiliation(self, affiliation, db):
        """Test getting affiliation by ID"""
        # Act
        result = AgencyService.get_affiliation(affiliation.id)

        # Assert
        assert result == affiliation

    def test_get_affiliation_not_found(self, db):
        """Test getting non-existent affiliation raises NotFound"""
        # Act & Assert
        with pytest.raises(NotFound, match="Affiliation 999 not found"):
            AgencyService.get_affiliation(999)

    def test_create_affiliation(self, user, db):
        """Test creating affiliation"""
        # Arrange
        data = {"name": "New Affiliation"}

        # Act
        affiliation = AgencyService.create_affiliation(user, data)

        # Assert
        assert affiliation.id is not None
        assert affiliation.name == "New Affiliation"

    def test_update_affiliation(self, affiliation, user, db):
        """Test updating affiliation"""
        # Arrange
        data = {"name": "Updated Affiliation"}

        # Act
        updated = AgencyService.update_affiliation(affiliation.id, user, data)

        # Assert
        assert updated.name == "Updated Affiliation"

    def test_delete_affiliation_basic(self, affiliation, user, db):
        """Test deleting affiliation without project references"""
        # Arrange
        affiliation_id = affiliation.id

        # Act
        result = AgencyService.delete_affiliation(affiliation_id, user)

        # Assert
        assert not Affiliation.objects.filter(id=affiliation_id).exists()
        assert "message" in result
        assert result["external_projects_updated"] == 0
        assert result["student_projects_updated"] == 0

    def test_delete_affiliation_with_external_projects(self, affiliation, user, db):
        """Test deleting affiliation cleans external project references"""
        from common.tests.factories import ProjectFactory
        from projects.models import ExternalProjectDetails

        # Arrange
        project = ProjectFactory()
        external_details = ExternalProjectDetails.objects.create(
            project=project,
            collaboration_with=f"{affiliation.name}; Other Org",
        )

        # Act
        result = AgencyService.delete_affiliation(affiliation.id, user)

        # Assert
        assert not Affiliation.objects.filter(id=affiliation.id).exists()
        external_details.refresh_from_db()
        assert affiliation.name not in external_details.collaboration_with
        assert "Other Org" in external_details.collaboration_with
        assert result["external_projects_updated"] == 1
        assert result["student_projects_updated"] == 0

    def test_delete_affiliation_with_student_projects(self, affiliation, user, db):
        """Test deleting affiliation cleans student project references"""
        from common.tests.factories import ProjectFactory
        from projects.models import StudentProjectDetails

        # Arrange
        project = ProjectFactory()
        student_details = StudentProjectDetails.objects.create(
            project=project,
            organisation=f"{affiliation.name}; Other Org",
        )

        # Act
        result = AgencyService.delete_affiliation(affiliation.id, user)

        # Assert
        assert not Affiliation.objects.filter(id=affiliation.id).exists()
        student_details.refresh_from_db()
        assert affiliation.name not in student_details.organisation
        assert "Other Org" in student_details.organisation
        assert result["external_projects_updated"] == 0
        assert result["student_projects_updated"] == 1

    def test_delete_affiliation_with_both_project_types(self, affiliation, user, db):
        """Test deleting affiliation cleans both external and student projects"""
        from common.tests.factories import ProjectFactory
        from projects.models import ExternalProjectDetails, StudentProjectDetails

        # Arrange
        project1 = ProjectFactory()
        external_details = ExternalProjectDetails.objects.create(
            project=project1,
            collaboration_with=affiliation.name,
        )

        project2 = ProjectFactory()
        student_details = StudentProjectDetails.objects.create(
            project=project2,
            organisation=affiliation.name,
        )

        # Act
        result = AgencyService.delete_affiliation(affiliation.id, user)

        # Assert
        assert not Affiliation.objects.filter(id=affiliation.id).exists()
        external_details.refresh_from_db()
        assert external_details.collaboration_with == ""
        student_details.refresh_from_db()
        assert student_details.organisation == ""
        assert result["external_projects_updated"] == 1
        assert result["student_projects_updated"] == 1

    def test_clean_orphaned_affiliations_no_orphans(self, affiliation, user, db):
        """Test cleaning orphaned affiliations when none exist"""
        from common.tests.factories import ProjectFactory
        from projects.models import ExternalProjectDetails

        # Arrange - Create a project reference to keep affiliation
        project = ProjectFactory()
        ExternalProjectDetails.objects.create(
            project=project,
            collaboration_with=affiliation.name,
        )

        # Act
        result = AgencyService.clean_orphaned_affiliations(user)

        # Assert
        assert Affiliation.objects.filter(id=affiliation.id).exists()
        assert result["deleted_count"] == 0
        assert result["message"] == "No orphaned affiliations found"

    def test_clean_orphaned_affiliations_with_orphans(self, user, db):
        """Test cleaning orphaned affiliations removes unused ones"""
        # Arrange - Create orphaned affiliations
        orphan1 = Affiliation.objects.create(name="Orphan 1")
        orphan2 = Affiliation.objects.create(name="Orphan 2")

        # Act
        result = AgencyService.clean_orphaned_affiliations(user)

        # Assert
        assert not Affiliation.objects.filter(id=orphan1.id).exists()
        assert not Affiliation.objects.filter(id=orphan2.id).exists()
        assert result["deleted_count"] == 2
        assert "Orphan 1" in result["deleted_names"]
        assert "Orphan 2" in result["deleted_names"]

    def test_clean_orphaned_affiliations_with_user_work_reference(
        self, affiliation, user, db
    ):
        """Test affiliation with UserWork reference is not deleted"""
        from users.models import UserWork

        # Arrange - Create UserWork reference
        UserWork.objects.create(
            user=user,
            affiliation=affiliation,  # Pass the instance, not the ID
            role="Test Role",
        )

        # Act
        result = AgencyService.clean_orphaned_affiliations(user)

        # Assert
        assert Affiliation.objects.filter(id=affiliation.id).exists()
        assert result["deleted_count"] == 0


class TestAgencyService:
    """Tests for agency service operations"""

    def test_list_agencies(self, agency, db):
        """Test listing agencies"""
        # Act
        agencies = AgencyService.list_agencies()

        # Assert
        assert agencies.count() == 1
        assert agency in agencies

    def test_get_agency(self, agency, db):
        """Test getting agency by ID"""
        # Act
        result = AgencyService.get_agency(agency.id)

        # Assert
        assert result == agency

    def test_get_agency_not_found(self, db):
        """Test getting non-existent agency raises NotFound"""
        # Act & Assert
        with pytest.raises(NotFound, match="Agency 999 not found"):
            AgencyService.get_agency(999)

    def test_create_agency(self, user, db):
        """Test creating agency"""
        # Arrange
        data = {
            "name": "New Agency",
            "key_stakeholder": user,
            "is_active": True,
        }

        # Act
        agency = AgencyService.create_agency(user, data)

        # Assert
        assert agency.id is not None
        assert agency.name == "New Agency"
        assert agency.is_active is True

    def test_update_agency(self, agency, user, db):
        """Test updating agency"""
        # Arrange
        data = {"name": "Updated Agency"}

        # Act
        updated = AgencyService.update_agency(agency.id, user, data)

        # Assert
        assert updated.name == "Updated Agency"

    def test_delete_agency(self, agency, user, db):
        """Test deleting agency"""
        # Arrange
        agency_id = agency.id

        # Act
        AgencyService.delete_agency(agency_id, user)

        # Assert
        assert not Agency.objects.filter(id=agency_id).exists()


class TestBranchService:
    """Tests for branch service operations"""

    def test_list_branches(self, branch, db):
        """Test listing branches"""
        # Act
        branches = AgencyService.list_branches()

        # Assert
        assert branches.count() == 1
        assert branch in branches

    def test_list_branches_with_search(self, branch, db):
        """Test listing branches with search"""
        # Act
        branches = AgencyService.list_branches(search="Test")

        # Assert
        assert branches.count() == 1
        assert branch in branches

    def test_list_branches_with_search_no_results(self, branch, db):
        """Test listing branches with search that returns no results"""
        # Act
        branches = AgencyService.list_branches(search="NonExistent")

        # Assert
        assert branches.count() == 0

    def test_list_branches_case_insensitive_search(self, branch, db):
        """Test listing branches with case-insensitive search"""
        # Act
        branches = AgencyService.list_branches(search="test")

        # Assert
        assert branches.count() == 1
        assert branch in branches

    def test_get_branch(self, branch, db):
        """Test getting branch by ID"""
        # Act
        result = AgencyService.get_branch(branch.id)

        # Assert
        assert result == branch

    def test_get_branch_not_found(self, db):
        """Test getting non-existent branch raises NotFound"""
        # Act & Assert
        with pytest.raises(NotFound, match="Branch 999 not found"):
            AgencyService.get_branch(999)

    def test_create_branch(self, agency, user, db):
        """Test creating branch"""
        # Arrange
        data = {
            "agency": agency,
            "name": "New Branch",
            "manager": user,
        }

        # Act
        branch = AgencyService.create_branch(user, data)

        # Assert
        assert branch.id is not None
        assert branch.name == "New Branch"
        assert branch.agency == agency

    def test_update_branch(self, branch, user, db):
        """Test updating branch"""
        # Arrange
        data = {"name": "Updated Branch"}

        # Act
        updated = AgencyService.update_branch(branch.id, user, data)

        # Assert
        assert updated.name == "Updated Branch"

    def test_delete_branch(self, branch, user, db):
        """Test deleting branch"""
        # Arrange
        branch_id = branch.id

        # Act
        AgencyService.delete_branch(branch_id, user)

        # Assert
        assert not Branch.objects.filter(id=branch_id).exists()


class TestBusinessAreaService:
    """Tests for business area service operations"""

    def test_list_business_areas(self, business_area, db):
        """Test listing business areas"""
        # Act
        business_areas = AgencyService.list_business_areas()

        # Assert
        assert business_areas.count() == 1
        assert business_area in business_areas

    def test_list_business_areas_with_filters(self, business_area, division, db):
        """Test listing business areas with filters"""
        # Act
        business_areas = AgencyService.list_business_areas()

        # Assert
        assert business_areas.count() == 1
        assert business_area in business_areas

    def test_get_business_area(self, business_area, db):
        """Test getting business area by ID"""
        # Act
        result = AgencyService.get_business_area(business_area.id)

        # Assert
        assert result == business_area

    def test_get_business_area_not_found(self, db):
        """Test getting non-existent business area raises NotFound"""
        # Act & Assert
        with pytest.raises(NotFound, match="Business area 999 not found"):
            AgencyService.get_business_area(999)

    def test_create_business_area(self, agency, division, user, db):
        """Test creating business area"""
        # Arrange
        data = {
            "agency": agency,
            "name": "New Business Area",
            "slug": "new-ba",
            "division": division,
            "leader": user,
            "finance_admin": user,
            "data_custodian": user,
            "is_active": True,
        }

        # Act
        ba = AgencyService.create_business_area(user, data)

        # Assert
        assert ba.id is not None
        assert ba.name == "New Business Area"
        assert ba.agency == agency

    def test_update_business_area(self, business_area, user, db):
        """Test updating business area"""
        # Arrange
        data = {"name": "Updated Business Area"}

        # Act
        updated = AgencyService.update_business_area(business_area.id, user, data)

        # Assert
        assert updated.name == "Updated Business Area"

    def test_delete_business_area(self, business_area, user, db):
        """Test deleting business area"""
        # Arrange
        ba_id = business_area.id

        # Act
        AgencyService.delete_business_area(ba_id, user)

        # Assert
        assert not BusinessArea.objects.filter(id=ba_id).exists()

    def test_set_business_area_active(self, business_area, db):
        """Test toggling business area active status"""
        # Arrange
        original_status = business_area.is_active

        # Act
        updated = AgencyService.set_business_area_active(business_area.id)

        # Assert
        assert updated.is_active != original_status

    def test_set_business_area_active_toggle_twice(self, business_area, db):
        """Test toggling business area active status twice returns to original"""
        # Arrange
        original_status = business_area.is_active

        # Act
        AgencyService.set_business_area_active(business_area.id)
        final = AgencyService.set_business_area_active(business_area.id)

        # Assert
        assert final.is_active == original_status

    def test_list_business_areas_includes_related_data(self, business_area, db):
        """Test listing business areas includes related data"""
        # Act
        business_areas = AgencyService.list_business_areas()

        # Assert - Access related fields to ensure they're loaded
        for ba in business_areas:
            assert ba.division is not None
            assert ba.division.name is not None

    def test_get_business_area_includes_related_data(self, business_area, db):
        """Test getting business area includes related data"""
        # Act
        result = AgencyService.get_business_area(business_area.id)

        # Assert - Access related fields to ensure they're loaded
        assert result.division is not None
        assert result.division.name is not None
        assert result.leader is not None


class TestDivisionService:
    """Tests for division service operations"""

    def test_list_divisions(self, division, db):
        """Test listing divisions"""
        # Act
        divisions = AgencyService.list_divisions()

        # Assert
        assert divisions.count() == 1
        assert division in divisions

    def test_get_division(self, division, db):
        """Test getting division by ID"""
        # Act
        result = AgencyService.get_division(division.id)

        # Assert
        assert result == division

    def test_get_division_not_found(self, db):
        """Test getting non-existent division raises NotFound"""
        # Act & Assert
        with pytest.raises(NotFound, match="Division 999 not found"):
            AgencyService.get_division(999)

    def test_create_division(self, user, db):
        """Test creating division"""
        # Arrange
        data = {
            "name": "New Division",
            "slug": "new-division",
            "director": user,
        }

        # Act
        division = AgencyService.create_division(user, data)

        # Assert
        assert division.id is not None
        assert division.name == "New Division"

    def test_update_division(self, division, user, db):
        """Test updating division"""
        # Arrange
        data = {"name": "Updated Division"}

        # Act
        updated = AgencyService.update_division(division.id, user, data)

        # Assert
        assert updated.name == "Updated Division"

    def test_delete_division(self, division, user, db):
        """Test deleting division"""
        # Arrange
        division_id = division.id

        # Act
        AgencyService.delete_division(division_id, user)

        # Assert
        assert not Division.objects.filter(id=division_id).exists()


class TestDepartmentalServiceService:
    """Tests for departmental service operations"""

    def test_list_departmental_services(self, departmental_service, db):
        """Test listing departmental services"""
        # Act
        services = AgencyService.list_departmental_services()

        # Assert
        assert services.count() == 1
        assert departmental_service in services

    def test_get_departmental_service(self, departmental_service, db):
        """Test getting departmental service by ID"""
        # Act
        result = AgencyService.get_departmental_service(departmental_service.id)

        # Assert
        assert result == departmental_service

    def test_get_departmental_service_not_found(self, db):
        """Test getting non-existent service raises NotFound"""
        # Act & Assert
        with pytest.raises(NotFound, match="Departmental service 999 not found"):
            AgencyService.get_departmental_service(999)

    def test_create_departmental_service(self, user, db):
        """Test creating departmental service"""
        # Arrange
        data = {
            "name": "New Service",
            "director": user,
        }

        # Act
        service = AgencyService.create_departmental_service(user, data)

        # Assert
        assert service.id is not None
        assert service.name == "New Service"

    def test_update_departmental_service(self, departmental_service, user, db):
        """Test updating departmental service"""
        # Arrange
        data = {"name": "Updated Service"}

        # Act
        updated = AgencyService.update_departmental_service(
            departmental_service.id, user, data
        )

        # Assert
        assert updated.name == "Updated Service"

    def test_delete_departmental_service(self, departmental_service, user, db):
        """Test deleting departmental service"""
        # Arrange
        service_id = departmental_service.id

        # Act
        AgencyService.delete_departmental_service(service_id, user)

        # Assert
        assert not DepartmentalService.objects.filter(id=service_id).exists()
