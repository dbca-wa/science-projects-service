"""
Tests for contact services
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound

from contacts.services.contact_service import ContactService
from contacts.models import Address, UserContact, AgencyContact, BranchContact

User = get_user_model()


class TestAddressService:
    """Tests for Address service operations"""

    def test_list_addresses(self, address_for_agency, db):
        """Test listing all addresses"""
        # Act
        addresses = ContactService.list_addresses()
        
        # Assert
        assert addresses.count() == 1
        assert address_for_agency in addresses

    def test_get_address(self, address_for_agency, db):
        """Test getting address by ID"""
        # Act
        address = ContactService.get_address(address_for_agency.id)
        
        # Assert
        assert address.id == address_for_agency.id
        assert address.street == '123 Test St'

    def test_get_address_not_found(self, db):
        """Test getting non-existent address raises NotFound"""
        # Act & Assert
        with pytest.raises(NotFound, match="Address 999 not found"):
            ContactService.get_address(999)

    def test_create_address_for_agency(self, user, agency, db):
        """Test creating an address for an agency"""
        # Arrange
        data = {
            'agency': agency,
            'street': '789 New St',
            'suburb': 'New Suburb',
            'city': 'New City',
            'zipcode': 11111,
            'state': 'New State',
            'country': 'New Country',
        }
        
        # Act
        address = ContactService.create_address(user, data)
        
        # Assert
        assert address.id is not None
        assert address.street == '789 New St'
        assert address.agency == agency
        assert address.branch is None

    def test_create_address_for_branch(self, user, branch, db):
        """Test creating an address for a branch"""
        # Arrange
        data = {
            'branch': branch,
            'street': '321 Branch St',
            'city': 'Branch City',
            'zipcode': 22222,
            'state': 'Branch State',
            'country': 'Branch Country',
        }
        
        # Act
        address = ContactService.create_address(user, data)
        
        # Assert
        assert address.id is not None
        assert address.street == '321 Branch St'
        assert address.branch == branch
        assert address.agency is None

    def test_update_address(self, address_for_agency, user, db):
        """Test updating an address"""
        # Arrange
        data = {'street': 'Updated Street'}
        
        # Act
        updated = ContactService.update_address(address_for_agency.id, user, data)
        
        # Assert
        assert updated.id == address_for_agency.id
        assert updated.street == 'Updated Street'

    def test_delete_address(self, address_for_agency, user, db):
        """Test deleting an address"""
        # Arrange
        address_id = address_for_agency.id
        
        # Act
        ContactService.delete_address(address_id, user)
        
        # Assert
        assert not Address.objects.filter(id=address_id).exists()


class TestAddressValidation:
    """Tests for Address model validation"""

    def test_address_requires_agency_or_branch(self, db):
        """Test address must have either agency or branch"""
        # Arrange
        address = Address(
            street='Test St',
            city='Test City',
            zipcode=12345,
            state='Test State',
            country='Test Country',
        )
        
        # Act & Assert
        with pytest.raises(Exception):  # ValidationError
            address.save()

    def test_address_cannot_have_both(self, agency, branch, db):
        """Test address cannot have both agency and branch"""
        # Arrange
        address = Address(
            agency=agency,
            branch=branch,
            street='Test St',
            city='Test City',
            zipcode=12345,
            state='Test State',
            country='Test Country',
        )
        
        # Act & Assert
        with pytest.raises(Exception):  # ValidationError
            address.save()

    def test_address_with_agency_valid(self, agency, db):
        """Test address with agency is valid"""
        # Arrange
        address = Address(
            agency=agency,
            street='Test St',
            city='Test City',
            zipcode=12345,
            state='Test State',
            country='Test Country',
        )
        
        # Act
        address.save()
        
        # Assert
        assert address.id is not None
        assert address.agency == agency
        assert address.branch is None

    def test_address_with_branch_valid(self, branch, db):
        """Test address with branch is valid"""
        # Arrange
        address = Address(
            branch=branch,
            street='Test St',
            city='Test City',
            zipcode=12345,
            state='Test State',
            country='Test Country',
        )
        
        # Act
        address.save()
        
        # Assert
        assert address.id is not None
        assert address.branch == branch
        assert address.agency is None


class TestAgencyContactService:
    """Tests for AgencyContact service operations"""

    def test_list_agency_contacts(self, agency_contact, db):
        """Test listing all agency contacts"""
        # Act
        contacts = ContactService.list_agency_contacts()
        
        # Assert
        assert contacts.count() == 1
        assert agency_contact in contacts

    def test_get_agency_contact(self, agency_contact, db):
        """Test getting agency contact by ID"""
        # Act
        contact = ContactService.get_agency_contact(agency_contact.id)
        
        # Assert
        assert contact.id == agency_contact.id
        assert contact.email == 'agency@example.com'

    def test_get_agency_contact_not_found(self, db):
        """Test getting non-existent agency contact raises NotFound"""
        # Act & Assert
        with pytest.raises(NotFound, match="Agency contact 999 not found"):
            ContactService.get_agency_contact(999)

    def test_create_agency_contact(self, user, agency, address_for_agency, db):
        """Test creating an agency contact"""
        # Arrange
        data = {
            'agency': agency,
            'email': 'newagency@example.com',
            'phone': '1111111111',
            'address': address_for_agency,
        }
        
        # Act
        contact = ContactService.create_agency_contact(user, data)
        
        # Assert
        assert contact.id is not None
        assert contact.email == 'newagency@example.com'
        assert contact.agency == agency

    def test_update_agency_contact(self, agency_contact, user, db):
        """Test updating an agency contact"""
        # Arrange
        data = {'email': 'updated@example.com'}
        
        # Act
        updated = ContactService.update_agency_contact(agency_contact.id, user, data)
        
        # Assert
        assert updated.id == agency_contact.id
        assert updated.email == 'updated@example.com'

    def test_delete_agency_contact(self, agency_contact, user, db):
        """Test deleting an agency contact"""
        # Arrange
        contact_id = agency_contact.id
        
        # Act
        ContactService.delete_agency_contact(contact_id, user)
        
        # Assert
        assert not AgencyContact.objects.filter(id=contact_id).exists()


class TestBranchContactService:
    """Tests for BranchContact service operations"""

    def test_list_branch_contacts(self, branch_contact, db):
        """Test listing all branch contacts"""
        # Act
        contacts = ContactService.list_branch_contacts()
        
        # Assert
        assert contacts.count() == 1
        assert branch_contact in contacts

    def test_get_branch_contact(self, branch_contact, db):
        """Test getting branch contact by ID"""
        # Act
        contact = ContactService.get_branch_contact(branch_contact.id)
        
        # Assert
        assert contact.id == branch_contact.id
        assert contact.email == 'branch@example.com'

    def test_get_branch_contact_not_found(self, db):
        """Test getting non-existent branch contact raises NotFound"""
        # Act & Assert
        with pytest.raises(NotFound, match="Branch contact 999 not found"):
            ContactService.get_branch_contact(999)

    def test_create_branch_contact(self, user, branch, address_for_branch, db):
        """Test creating a branch contact"""
        # Arrange
        data = {
            'branch': branch,
            'email': 'newbranch@example.com',
            'phone': '2222222222',
            'address': address_for_branch,
        }
        
        # Act
        contact = ContactService.create_branch_contact(user, data)
        
        # Assert
        assert contact.id is not None
        assert contact.email == 'newbranch@example.com'
        assert contact.branch == branch

    def test_update_branch_contact(self, branch_contact, user, db):
        """Test updating a branch contact"""
        # Arrange
        data = {'email': 'updatedbranch@example.com'}
        
        # Act
        updated = ContactService.update_branch_contact(branch_contact.id, user, data)
        
        # Assert
        assert updated.id == branch_contact.id
        assert updated.email == 'updatedbranch@example.com'

    def test_delete_branch_contact(self, branch_contact, user, db):
        """Test deleting a branch contact"""
        # Arrange
        contact_id = branch_contact.id
        
        # Act
        ContactService.delete_branch_contact(contact_id, user)
        
        # Assert
        assert not BranchContact.objects.filter(id=contact_id).exists()


class TestUserContactService:
    """Tests for UserContact service operations"""

    def test_list_user_contacts(self, user_contact, db):
        """Test listing all user contacts"""
        # Act
        contacts = ContactService.list_user_contacts()
        
        # Assert
        assert contacts.count() == 1
        assert user_contact in contacts

    def test_get_user_contact(self, user_contact, db):
        """Test getting user contact by ID"""
        # Act
        contact = ContactService.get_user_contact(user_contact.id)
        
        # Assert
        assert contact.id == user_contact.id
        assert contact.email == 'user@example.com'

    def test_get_user_contact_not_found(self, db):
        """Test getting non-existent user contact raises NotFound"""
        # Act & Assert
        with pytest.raises(NotFound, match="User contact 999 not found"):
            ContactService.get_user_contact(999)

    def test_create_user_contact(self, user, user_factory, db):
        """Test creating a user contact"""
        # Arrange
        new_user = user_factory(username='newuser', email='newuser@example.com')
        data = {
            'user': new_user,
            'email': 'newcontact@example.com',
            'phone': '3333333333',
        }
        
        # Act
        contact = ContactService.create_user_contact(user, data)
        
        # Assert
        assert contact.id is not None
        assert contact.email == 'newcontact@example.com'
        assert contact.user == new_user

    def test_update_user_contact(self, user_contact, user, db):
        """Test updating a user contact"""
        # Arrange
        data = {'email': 'updateduser@example.com'}
        
        # Act
        updated = ContactService.update_user_contact(user_contact.id, user, data)
        
        # Assert
        assert updated.id == user_contact.id
        assert updated.email == 'updateduser@example.com'

    def test_delete_user_contact(self, user_contact, user, db):
        """Test deleting a user contact"""
        # Arrange
        contact_id = user_contact.id
        
        # Act
        ContactService.delete_user_contact(contact_id, user)
        
        # Assert
        assert not UserContact.objects.filter(id=contact_id).exists()
