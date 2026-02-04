"""
Tests for agencies views
"""
import pytest
from rest_framework.test import APIClient
from rest_framework import status

from agencies.models import Affiliation, Agency
from agencies.services.agency_service import AgencyService


@pytest.fixture
def api_client():
    """Provide API client for view tests"""
    return APIClient()


class TestAffiliations:
    """Tests for Affiliations view"""

    def test_list_affiliations(self, api_client, user, affiliation, db):
        """Test listing all affiliations"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get('/api/v1/agencies/affiliations')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['name'] == affiliation.name

    def test_list_affiliations_unauthenticated(self, api_client, db):
        """Test listing affiliations without authentication"""
        # Act
        response = api_client.get('/api/v1/agencies/affiliations')
        
        # Assert
        # DRF returns 403 (Forbidden) when no authentication is provided
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_affiliations_with_search(self, api_client, user, db):
        """Test listing affiliations with search term"""
        # Arrange
        Affiliation.objects.create(name="Test Affiliation")
        Affiliation.objects.create(name="Another Affiliation")
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get('/api/v1/agencies/affiliations?searchTerm=Test')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert 'affiliations' in response.data
        assert 'total_results' in response.data
        assert 'total_pages' in response.data
        assert response.data['total_results'] == 1
        assert response.data['affiliations'][0]['name'] == "Test Affiliation"

    def test_list_affiliations_with_search_pagination(self, api_client, user, db):
        """Test listing affiliations with search and pagination"""
        # Arrange
        for i in range(15):
            Affiliation.objects.create(name=f"Test Affiliation {i}")
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get('/api/v1/agencies/affiliations?searchTerm=Test&page=2')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert 'affiliations' in response.data
        assert response.data['total_results'] == 15

    def test_create_affiliation(self, api_client, user, db):
        """Test creating affiliation"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {"name": "New Affiliation"}
        
        # Act
        response = api_client.post('/api/v1/agencies/affiliations', data, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == "New Affiliation"
        assert Affiliation.objects.filter(name="New Affiliation").exists()

    def test_create_affiliation_invalid_data(self, api_client, user, db):
        """Test creating affiliation with invalid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {}  # Missing required 'name' field
        
        # Act
        response = api_client.post('/api/v1/agencies/affiliations', data, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestAffiliationDetail:
    """Tests for AffiliationDetail view"""

    def test_get_affiliation(self, api_client, user, affiliation, db):
        """Test getting affiliation detail"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(f'/api/v1/agencies/affiliations/{affiliation.id}')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == affiliation.name

    def test_get_affiliation_pk_zero(self, api_client, user, db):
        """Test getting affiliation with pk=0"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get('/api/v1/agencies/affiliations/0')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK

    def test_get_affiliation_not_found(self, api_client, user, db):
        """Test getting non-existent affiliation"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get('/api/v1/agencies/affiliations/999')
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_affiliation(self, api_client, user, affiliation, db):
        """Test updating affiliation"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {"name": "Updated Affiliation"}
        
        # Act
        response = api_client.put(
            f'/api/v1/agencies/affiliations/{affiliation.id}',
            data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data['name'] == "Updated Affiliation"
        affiliation.refresh_from_db()
        assert affiliation.name == "Updated Affiliation"

    def test_update_affiliation_invalid_data(self, api_client, user, affiliation, db):
        """Test updating affiliation with invalid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {"name": ""}  # Empty name
        
        # Act
        response = api_client.put(
            f'/api/v1/agencies/affiliations/{affiliation.id}',
            data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_delete_affiliation(self, api_client, user, affiliation, db):
        """Test deleting affiliation"""
        # Arrange
        api_client.force_authenticate(user=user)
        affiliation_id = affiliation.id
        
        # Act
        response = api_client.delete(f'/api/v1/agencies/affiliations/{affiliation_id}')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data
        assert not Affiliation.objects.filter(id=affiliation_id).exists()


class TestAffiliationsMerge:
    """Tests for AffiliationsMerge view"""

    def test_merge_affiliations(self, api_client, user, db):
        """Test merging affiliations"""
        # Arrange
        from users.models import UserWork
        
        primary = Affiliation.objects.create(name="Primary Affiliation")
        secondary = Affiliation.objects.create(name="Secondary Affiliation")
        
        # Create UserWork with secondary affiliation
        UserWork.objects.create(
            user=user,
            affiliation=secondary,  # Use the object, not the ID
            role="Test Role",
        )
        
        api_client.force_authenticate(user=user)
        data = {
            "primaryAffiliation": {"pk": primary.id},
            "secondaryAffiliations": [{"pk": secondary.id}]
        }
        
        # Act
        response = api_client.post('/api/v1/agencies/affiliations/merge', data, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data['message'] == "Merged!"
        assert not Affiliation.objects.filter(id=secondary.id).exists()


class TestAffiliationsCleanOrphaned:
    """Tests for AffiliationsCleanOrphaned view"""

    def test_clean_orphaned_affiliations(self, api_client, user, db):
        """Test cleaning orphaned affiliations"""
        # Arrange
        Affiliation.objects.create(name="Orphan 1")
        Affiliation.objects.create(name="Orphan 2")
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.post('/api/v1/agencies/affiliations/clean_orphaned')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert 'deleted_count' in response.data
        assert response.data['deleted_count'] == 2


class TestAgencies:
    """Tests for Agencies view"""

    def test_list_agencies(self, api_client, user, agency, db):
        """Test listing all agencies"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get('/api/v1/agencies/')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['name'] == agency.name

    def test_list_agencies_unauthenticated(self, api_client, db):
        """Test listing agencies without authentication"""
        # Act
        response = api_client.get('/api/v1/agencies/')
        
        # Assert
        # DRF returns 403 (Forbidden) when no authentication is provided
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_agency(self, api_client, user, db):
        """Test creating agency"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            "name": "New Agency",
            "key_stakeholder": user.id,
            "is_active": True,
        }
        
        # Act
        response = api_client.post('/api/v1/agencies/', data, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == "New Agency"
        assert Agency.objects.filter(name="New Agency").exists()

    def test_create_agency_invalid_data(self, api_client, user, db):
        """Test creating agency with invalid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {}  # Missing required 'name' field
        
        # Act
        response = api_client.post('/api/v1/agencies/', data, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestAgencyDetail:
    """Tests for AgencyDetail view"""

    def test_get_agency(self, api_client, user, agency, db):
        """Test getting agency detail"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(f'/api/v1/agencies/{agency.id}')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == agency.name

    def test_get_agency_not_found(self, api_client, user, db):
        """Test getting non-existent agency"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get('/api/v1/agencies/999')
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_agency(self, api_client, user, agency, db):
        """Test updating agency"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {"name": "Updated Agency"}
        
        # Act
        response = api_client.put(
            f'/api/v1/agencies/{agency.id}',
            data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data['name'] == "Updated Agency"
        agency.refresh_from_db()
        assert agency.name == "Updated Agency"

    def test_update_agency_invalid_data(self, api_client, user, agency, db):
        """Test updating agency with invalid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {"name": ""}  # Empty name
        
        # Act
        response = api_client.put(
            f'/api/v1/agencies/{agency.id}',
            data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_delete_agency(self, api_client, user, agency, db):
        """Test deleting agency"""
        # Arrange
        api_client.force_authenticate(user=user)
        agency_id = agency.id
        
        # Act
        response = api_client.delete(f'/api/v1/agencies/{agency_id}')
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Agency.objects.filter(id=agency_id).exists()


class TestBranches:
    """Tests for Branches view"""

    def test_list_branches(self, api_client, user, branch, db):
        """Test listing all branches"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get('/api/v1/agencies/branches')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['name'] == branch.name

    def test_list_branches_with_search(self, api_client, user, db):
        """Test listing branches with search term"""
        # Arrange
        from agencies.models import Branch
        Branch.objects.create(name="Test Branch", old_id=1)
        Branch.objects.create(name="Another Branch", old_id=2)
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get('/api/v1/agencies/branches?searchTerm=Test')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert 'branches' in response.data
        assert 'total_results' in response.data
        assert 'total_pages' in response.data
        assert response.data['total_results'] == 1
        assert response.data['branches'][0]['name'] == "Test Branch"

    def test_create_branch(self, api_client, user, agency, db):
        """Test creating branch"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            "name": "New Branch",
            "old_id": 999,
            "agency": agency.id,
        }
        
        # Act
        response = api_client.post('/api/v1/agencies/branches', data, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == "New Branch"

    def test_create_branch_invalid_data(self, api_client, user, db):
        """Test creating branch with invalid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {}  # Missing required fields
        
        # Act
        response = api_client.post('/api/v1/agencies/branches', data, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestBranchDetail:
    """Tests for BranchDetail view"""

    def test_get_branch(self, api_client, user, branch, db):
        """Test getting branch detail"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(f'/api/v1/agencies/branches/{branch.id}')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == branch.name

    def test_get_branch_not_found(self, api_client, user, db):
        """Test getting non-existent branch"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get('/api/v1/agencies/branches/999')
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_branch(self, api_client, user, branch, db):
        """Test updating branch"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {"name": "Updated Branch"}
        
        # Act
        response = api_client.put(
            f'/api/v1/agencies/branches/{branch.id}',
            data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data['name'] == "Updated Branch"
        branch.refresh_from_db()
        assert branch.name == "Updated Branch"

    def test_update_branch_invalid_data(self, api_client, user, branch, db):
        """Test updating branch with invalid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {"name": ""}  # Empty name
        
        # Act
        response = api_client.put(
            f'/api/v1/agencies/branches/{branch.id}',
            data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_delete_branch(self, api_client, user, branch, db):
        """Test deleting branch"""
        # Arrange
        api_client.force_authenticate(user=user)
        branch_id = branch.id
        
        # Act
        response = api_client.delete(f'/api/v1/agencies/branches/{branch_id}')
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        from agencies.models import Branch
        assert not Branch.objects.filter(id=branch_id).exists()


class TestBusinessAreas:
    """Tests for BusinessAreas view"""

    def test_list_business_areas(self, api_client, user, business_area, db):
        """Test listing all business areas"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get('/api/v1/agencies/business_areas')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['name'] == business_area.name

    def test_create_business_area(self, api_client, user, agency, db):
        """Test creating business area"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            "name": "New Business Area",
            "agency": agency.id,
            "focus": "Test focus",
            "introduction": "Test introduction",
        }
        
        # Act
        response = api_client.post('/api/v1/agencies/business_areas', data, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == "New Business Area"

    def test_create_business_area_invalid_data(self, api_client, user, db):
        """Test creating business area with invalid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {}  # Missing required fields
        
        # Act
        response = api_client.post('/api/v1/agencies/business_areas', data, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestBusinessAreaDetail:
    """Tests for BusinessAreaDetail view"""

    def test_get_business_area(self, api_client, user, business_area, db):
        """Test getting business area detail"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(f'/api/v1/agencies/business_areas/{business_area.id}')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == business_area.name

    def test_get_business_area_not_found(self, api_client, user, db):
        """Test getting non-existent business area"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get('/api/v1/agencies/business_areas/999')
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_business_area(self, api_client, user, business_area, db):
        """Test updating business area"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {"name": "Updated Business Area"}
        
        # Act
        response = api_client.put(
            f'/api/v1/agencies/business_areas/{business_area.id}',
            data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data['name'] == "Updated Business Area"
        business_area.refresh_from_db()
        assert business_area.name == "Updated Business Area"

    def test_update_business_area_invalid_data(self, api_client, user, business_area, db):
        """Test updating business area with invalid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {"name": ""}  # Empty name
        
        # Act
        response = api_client.put(
            f'/api/v1/agencies/business_areas/{business_area.id}',
            data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_delete_business_area(self, api_client, user, business_area, db):
        """Test deleting business area"""
        # Arrange
        api_client.force_authenticate(user=user)
        business_area_id = business_area.id
        
        # Act
        response = api_client.delete(f'/api/v1/agencies/business_areas/{business_area_id}')
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        from agencies.models import BusinessArea
        assert not BusinessArea.objects.filter(id=business_area_id).exists()


class TestMyBusinessAreas:
    """Tests for MyBusinessAreas view"""

    def test_get_my_business_areas(self, api_client, user, business_area, db):
        """Test getting business areas led by current user"""
        # Arrange
        business_area.leader = user
        business_area.save()
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get('/api/v1/agencies/business_areas/mine')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['name'] == business_area.name

    def test_get_my_business_areas_empty(self, api_client, user, db):
        """Test getting business areas when user leads none"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get('/api/v1/agencies/business_areas/mine')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0


class TestSetBusinessAreaActive:
    """Tests for SetBusinessAreaActive view"""

    def test_toggle_business_area_active(self, api_client, user, business_area, db):
        """Test toggling business area active status"""
        # Arrange
        api_client.force_authenticate(user=user)
        original_status = business_area.is_active
        
        # Act
        response = api_client.post(f'/api/v1/agencies/business_areas/setactive/{business_area.id}')
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        business_area.refresh_from_db()
        assert business_area.is_active != original_status


class TestDivisions:
    """Tests for Divisions view"""

    def test_list_divisions(self, api_client, user, division, db):
        """Test listing all divisions"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get('/api/v1/agencies/divisions')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['name'] == division.name

    def test_create_division(self, api_client, user, db):
        """Test creating division"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            "name": "New Division",
            "slug": "new-division",
            "old_id": 999,
            "director": user.id,
            "approver": user.id,
        }
        
        # Act
        response = api_client.post('/api/v1/agencies/divisions', data, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == "New Division"

    def test_create_division_invalid_data(self, api_client, user, db):
        """Test creating division with invalid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {}  # Missing required fields
        
        # Act
        response = api_client.post('/api/v1/agencies/divisions', data, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestDivisionDetail:
    """Tests for DivisionDetail view"""

    def test_get_division(self, api_client, user, division, db):
        """Test getting division detail"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(f'/api/v1/agencies/divisions/{division.id}')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == division.name

    def test_get_division_not_found(self, api_client, user, db):
        """Test getting non-existent division"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get('/api/v1/agencies/divisions/999')
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_division(self, api_client, user, division, db):
        """Test updating division"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {"name": "Updated Division"}
        
        # Act
        response = api_client.put(
            f'/api/v1/agencies/divisions/{division.id}',
            data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data['name'] == "Updated Division"
        division.refresh_from_db()
        assert division.name == "Updated Division"

    def test_update_division_invalid_data(self, api_client, user, division, db):
        """Test updating division with invalid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {"name": ""}  # Empty name
        
        # Act
        response = api_client.put(
            f'/api/v1/agencies/divisions/{division.id}',
            data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_delete_division(self, api_client, user, division, db):
        """Test deleting division"""
        # Arrange
        api_client.force_authenticate(user=user)
        division_id = division.id
        
        # Act
        response = api_client.delete(f'/api/v1/agencies/divisions/{division_id}')
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        from agencies.models import Division
        assert not Division.objects.filter(id=division_id).exists()


class TestDivisionEmailList:
    """Tests for DivisionEmailList view"""

    def test_get_division_email_list(self, api_client, user, division, db):
        """Test getting division email list"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(f'/api/v1/agencies/divisions/{division.id}/email_list')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == division.name

    def test_update_division_email_list(self, api_client, user, division, db):
        """Test updating division email list"""
        # Arrange
        from common.tests.factories import UserFactory
        user1 = UserFactory()
        user2 = UserFactory()
        api_client.force_authenticate(user=user)
        data = {"usersList": [user1.id, user2.id]}
        
        # Act
        response = api_client.post(
            f'/api/v1/agencies/divisions/{division.id}/email_list',
            data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        division.refresh_from_db()
        assert division.directorate_email_list.count() == 2

    def test_update_division_email_list_invalid_user(self, api_client, user, division, db):
        """Test updating division email list with invalid user ID"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {"usersList": [999999]}  # Non-existent user
        
        # Act
        response = api_client.post(
            f'/api/v1/agencies/divisions/{division.id}/email_list',
            data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestDepartmentalServices:
    """Tests for DepartmentalServices view"""

    def test_list_services(self, api_client, user, departmental_service, db):
        """Test listing all departmental services"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get('/api/v1/agencies/services')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['name'] == departmental_service.name

    def test_create_service(self, api_client, user, db):
        """Test creating departmental service"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            "name": "New Service",
            "old_id": 999,
        }
        
        # Act
        response = api_client.post('/api/v1/agencies/services', data, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == "New Service"

    def test_create_service_invalid_data(self, api_client, user, db):
        """Test creating departmental service with invalid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {}  # Missing required fields
        
        # Act
        response = api_client.post('/api/v1/agencies/services', data, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestDepartmentalServiceDetail:
    """Tests for DepartmentalServiceDetail view"""

    def test_get_service(self, api_client, user, departmental_service, db):
        """Test getting departmental service detail"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(f'/api/v1/agencies/services/{departmental_service.id}')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == departmental_service.name

    def test_get_service_not_found(self, api_client, user, db):
        """Test getting non-existent departmental service"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get('/api/v1/agencies/services/999')
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_service(self, api_client, user, departmental_service, db):
        """Test updating departmental service"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {"name": "Updated Service"}
        
        # Act
        response = api_client.put(
            f'/api/v1/agencies/services/{departmental_service.id}',
            data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data['name'] == "Updated Service"
        departmental_service.refresh_from_db()
        assert departmental_service.name == "Updated Service"

    def test_update_service_invalid_data(self, api_client, user, departmental_service, db):
        """Test updating departmental service with invalid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {"name": ""}  # Empty name
        
        # Act
        response = api_client.put(
            f'/api/v1/agencies/services/{departmental_service.id}',
            data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_delete_service(self, api_client, user, departmental_service, db):
        """Test deleting departmental service"""
        # Arrange
        api_client.force_authenticate(user=user)
        service_id = departmental_service.id
        
        # Act
        response = api_client.delete(f'/api/v1/agencies/services/{service_id}')
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        from agencies.models import DepartmentalService
        assert not DepartmentalService.objects.filter(id=service_id).exists()
