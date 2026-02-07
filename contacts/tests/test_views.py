"""
Tests for contact views
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from common.tests.test_helpers import contacts_urls
from contacts.models import Address, AgencyContact, BranchContact, UserContact

User = get_user_model()


@pytest.fixture
def api_client():
    """Provide API client for view tests"""
    return APIClient()


class TestAddressViews:
    """Tests for Address views"""

    def test_list_addresses_authenticated(
        self, api_client, user, address_for_agency, db
    ):
        """Test listing addresses as authenticated user"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(contacts_urls.path("addresses"))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == address_for_agency.id

    def test_list_addresses_unauthenticated(self, api_client, db):
        """Test listing addresses without authentication"""
        # Act
        response = api_client.get(contacts_urls.path("addresses"))

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_address_valid_data(self, api_client, user, agency, db):
        """Test creating address with valid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            "agency": agency.id,
            "street": "789 New St",
            "suburb": "New Suburb",
            "city": "New City",
            "zipcode": 11111,
            "state": "New State",
            "country": "New Country",
        }

        # Act
        response = api_client.post(contacts_urls.path("addresses"), data, format="json")

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["street"] == "789 New St"
        assert Address.objects.filter(street="789 New St").exists()

    def test_create_address_invalid_data(self, api_client, user, db):
        """Test creating address with invalid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            "street": "789 New St",
            # Missing required fields
        }

        # Act
        response = api_client.post(contacts_urls.path("addresses"), data, format="json")

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_address_detail(self, api_client, user, address_for_agency, db):
        """Test getting address detail"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(
            contacts_urls.path(f"addresses/{address_for_agency.id}")
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == address_for_agency.id
        assert response.data["street"] == "123 Test St"

    def test_get_address_not_found(self, api_client, user, db):
        """Test getting non-existent address"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(contacts_urls.path("addresses/999"))

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_address(self, api_client, user, address_for_agency, db):
        """Test updating address"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {"street": "Updated Street"}

        # Act
        response = api_client.put(
            contacts_urls.path(f"addresses/{address_for_agency.id}"),
            data,
            format="json",
        )

        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data["street"] == "Updated Street"
        address_for_agency.refresh_from_db()
        assert address_for_agency.street == "Updated Street"

    def test_delete_address(self, api_client, user, address_for_agency, db):
        """Test deleting address"""
        # Arrange
        api_client.force_authenticate(user=user)
        address_id = address_for_agency.id

        # Act
        response = api_client.delete(contacts_urls.path(f"addresses/{address_id}"))

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Address.objects.filter(id=address_id).exists()


class TestAgencyContactViews:
    """Tests for AgencyContact views"""

    def test_list_agency_contacts_authenticated(
        self, api_client, user, agency_contact, db
    ):
        """Test listing agency contacts as authenticated user"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(contacts_urls.path("agencies"))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == agency_contact.id

    def test_list_agency_contacts_unauthenticated(self, api_client, db):
        """Test listing agency contacts without authentication"""
        # Act
        response = api_client.get(contacts_urls.path("agencies"))

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_agency_contact_valid_data(
        self, api_client, user, agency, address_for_agency, db
    ):
        """Test creating agency contact with valid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            "agency": agency.id,
            "email": "newagency@example.com",
            "phone": "1111111111",
            "address": address_for_agency.id,
        }

        # Act
        response = api_client.post(contacts_urls.path("agencies"), data, format="json")

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["email"] == "newagency@example.com"
        assert AgencyContact.objects.filter(email="newagency@example.com").exists()

    def test_create_agency_contact_invalid_data(self, api_client, user, db):
        """Test creating agency contact with invalid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            "email": "invalid@example.com",
            # Missing required agency field
        }

        # Act
        response = api_client.post(contacts_urls.path("agencies"), data, format="json")

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_agency_contact_detail(self, api_client, user, agency_contact, db):
        """Test getting agency contact detail"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(contacts_urls.path(f"agencies/{agency_contact.id}"))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == agency_contact.id
        assert response.data["email"] == "agency@example.com"

    def test_get_agency_contact_not_found(self, api_client, user, db):
        """Test getting non-existent agency contact"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(contacts_urls.path("agencies/999"))

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_agency_contact(self, api_client, user, agency_contact, db):
        """Test updating agency contact"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {"email": "updated@example.com"}

        # Act
        response = api_client.put(
            contacts_urls.path(f"agencies/{agency_contact.id}"), data, format="json"
        )

        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data["email"] == "updated@example.com"
        agency_contact.refresh_from_db()
        assert agency_contact.email == "updated@example.com"

    def test_delete_agency_contact(self, api_client, user, agency_contact, db):
        """Test deleting agency contact"""
        # Arrange
        api_client.force_authenticate(user=user)
        contact_id = agency_contact.id

        # Act
        response = api_client.delete(contacts_urls.path(f"agencies/{contact_id}"))

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not AgencyContact.objects.filter(id=contact_id).exists()


class TestBranchContactViews:
    """Tests for BranchContact views"""

    def test_list_branch_contacts_authenticated(
        self, api_client, user, branch_contact, db
    ):
        """Test listing branch contacts as authenticated user"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(contacts_urls.path("branches"))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == branch_contact.id

    def test_list_branch_contacts_unauthenticated(self, api_client, db):
        """Test listing branch contacts without authentication"""
        # Act
        response = api_client.get(contacts_urls.path("branches"))

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_branch_contact_valid_data(
        self, api_client, user, branch, address_for_branch, db
    ):
        """Test creating branch contact with valid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            "branch": branch.id,
            "email": "newbranch@example.com",
            "phone": "2222222222",
            "address": address_for_branch.id,
        }

        # Act
        response = api_client.post(contacts_urls.path("branches"), data, format="json")

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["email"] == "newbranch@example.com"
        assert BranchContact.objects.filter(email="newbranch@example.com").exists()

    def test_create_branch_contact_invalid_data(self, api_client, user, db):
        """Test creating branch contact with invalid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            "email": "invalid@example.com",
            # Missing required branch field
        }

        # Act
        response = api_client.post(contacts_urls.path("branches"), data, format="json")

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_branch_contact_detail(self, api_client, user, branch_contact, db):
        """Test getting branch contact detail"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(contacts_urls.path(f"branches/{branch_contact.id}"))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == branch_contact.id
        assert response.data["email"] == "branch@example.com"

    def test_get_branch_contact_not_found(self, api_client, user, db):
        """Test getting non-existent branch contact"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(contacts_urls.path("branches/999"))

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_branch_contact(self, api_client, user, branch_contact, db):
        """Test updating branch contact"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {"email": "updatedbranch@example.com"}

        # Act
        response = api_client.put(
            contacts_urls.path(f"branches/{branch_contact.id}"), data, format="json"
        )

        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data["email"] == "updatedbranch@example.com"
        branch_contact.refresh_from_db()
        assert branch_contact.email == "updatedbranch@example.com"

    def test_delete_branch_contact(self, api_client, user, branch_contact, db):
        """Test deleting branch contact"""
        # Arrange
        api_client.force_authenticate(user=user)
        contact_id = branch_contact.id

        # Act
        response = api_client.delete(contacts_urls.path(f"branches/{contact_id}"))

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not BranchContact.objects.filter(id=contact_id).exists()


class TestUserContactViews:
    """Tests for UserContact views"""

    def test_list_user_contacts_authenticated(self, api_client, user, user_contact, db):
        """Test listing user contacts as authenticated user"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(contacts_urls.path("users"))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == user_contact.id

    def test_list_user_contacts_unauthenticated(self, api_client, db):
        """Test listing user contacts without authentication"""
        # Act
        response = api_client.get(contacts_urls.path("users"))

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_user_contact_valid_data(self, api_client, user, user_factory, db):
        """Test creating user contact with valid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        new_user = user_factory(username="newuser", email="newuser@example.com")
        data = {
            "user": new_user.id,
            "email": "newcontact@example.com",
            "phone": "3333333333",
        }

        # Act
        response = api_client.post(contacts_urls.path("users"), data, format="json")

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["email"] == "newcontact@example.com"
        assert UserContact.objects.filter(email="newcontact@example.com").exists()

    def test_create_user_contact_invalid_data(self, api_client, user, db):
        """Test creating user contact with invalid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            "email": "invalid@example.com",
            # Missing required user field
        }

        # Act
        response = api_client.post(contacts_urls.path("users"), data, format="json")

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_user_contact_detail(self, api_client, user, user_contact, db):
        """Test getting user contact detail"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(contacts_urls.path(f"users/{user_contact.id}"))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == user_contact.id
        assert response.data["email"] == "user@example.com"

    def test_get_user_contact_not_found(self, api_client, user, db):
        """Test getting non-existent user contact"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(contacts_urls.path("users/999"))

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_user_contact(self, api_client, user, user_contact, db):
        """Test updating user contact"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {"email": "updateduser@example.com"}

        # Act
        response = api_client.put(
            contacts_urls.path(f"users/{user_contact.id}"), data, format="json"
        )

        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data["email"] == "updateduser@example.com"
        user_contact.refresh_from_db()
        assert user_contact.email == "updateduser@example.com"

    def test_delete_user_contact(self, api_client, user, user_contact, db):
        """Test deleting user contact"""
        # Arrange
        api_client.force_authenticate(user=user)
        contact_id = user_contact.id

        # Act
        response = api_client.delete(contacts_urls.path(f"users/{contact_id}"))

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not UserContact.objects.filter(id=contact_id).exists()


class TestUserContactDetailPermissions:
    """Tests for UserContactDetail permissions"""

    def test_get_user_contact_detail_unauthenticated(
        self, api_client, user_contact, db
    ):
        """Test getting user contact detail without authentication"""
        # Act
        response = api_client.get(contacts_urls.path(f"users/{user_contact.id}"))

        # Assert
        # Note: UserContactDetail is missing IsAuthenticated permission class
        # This test documents the current behavior
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_user_contact_unauthenticated(self, api_client, user_contact, db):
        """Test updating user contact without authentication"""
        # Arrange
        data = {"email": "hacker@example.com"}

        # Act
        response = api_client.put(
            contacts_urls.path(f"users/{user_contact.id}"), data, format="json"
        )

        # Assert
        # Note: UserContactDetail is missing IsAuthenticated permission class
        # This test documents the current behavior (should be 401)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_user_contact_unauthenticated(self, api_client, user_contact, db):
        """Test deleting user contact without authentication"""
        # Act
        response = api_client.delete(contacts_urls.path(f"users/{user_contact.id}"))

        # Assert
        # Note: UserContactDetail is missing IsAuthenticated permission class
        # This test documents the current behavior (should be 401)
        assert response.status_code == status.HTTP_403_FORBIDDEN
