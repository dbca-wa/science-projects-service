"""
Tests for contact serializers
"""

from contacts.models import AgencyContact, BranchContact
from contacts.serializers import (
    AddressSerializer,
    AgencyContactSerializer,
    BranchContactSerializer,
    TinyAddressSerializer,
    TinyAgencyContactSerializer,
    TinyBranchContactSerializer,
    TinyUserContactSerializer,
    UserContactSerializer,
)


class TestTinyAddressSerializer:
    """Tests for TinyAddressSerializer"""

    def test_serialization(self, address_for_agency, db):
        """Test serializing address with nested agency"""
        # Act
        serializer = TinyAddressSerializer(address_for_agency)
        data = serializer.data

        # Assert
        assert data["id"] == address_for_agency.id
        assert data["street"] == "123 Test St"
        assert data["city"] == "Test City"
        assert data["state"] == "Test State"
        assert data["country"] == "Test Country"
        assert data["zipcode"] == 12345
        assert data["agency"]["id"] == address_for_agency.agency.id
        assert data["agency"]["name"] == "Test Agency"
        assert data["branch"] is None

    def test_serialization_with_branch(self, address_for_branch, db):
        """Test serializing address with nested branch"""
        # Act
        serializer = TinyAddressSerializer(address_for_branch)
        data = serializer.data

        # Assert
        assert data["id"] == address_for_branch.id
        assert data["street"] == "456 Branch St"
        assert data["branch"]["id"] == address_for_branch.branch.id
        assert data["branch"]["name"] == "Test Branch"
        assert data["agency"] is None


class TestAddressSerializer:
    """Tests for AddressSerializer"""

    def test_serialization(self, address_for_agency, db):
        """Test serializing address"""
        # Act
        serializer = AddressSerializer(address_for_agency)
        data = serializer.data

        # Assert
        assert data["id"] == address_for_agency.id
        assert data["street"] == "123 Test St"
        assert data["city"] == "Test City"
        assert data["agency"] == address_for_agency.agency.id

    def test_deserialization_with_agency(self, agency, db):
        """Test deserializing address with agency"""
        # Arrange
        data = {
            "agency": agency.id,
            "street": "999 New St",
            "city": "New City",
            "zipcode": 99999,
            "state": "New State",
            "country": "New Country",
        }

        # Act
        serializer = AddressSerializer(data=data)

        # Assert
        assert serializer.is_valid()
        address = serializer.save()
        assert address.street == "999 New St"
        assert address.agency == agency
        assert address.branch is None

    def test_deserialization_with_branch(self, branch, db):
        """Test deserializing address with branch"""
        # Arrange
        data = {
            "branch": branch.id,
            "street": "888 Branch St",
            "city": "Branch City",
            "zipcode": 88888,
            "state": "Branch State",
            "country": "Branch Country",
        }

        # Act
        serializer = AddressSerializer(data=data)

        # Assert
        assert serializer.is_valid()
        address = serializer.save()
        assert address.street == "888 Branch St"
        assert address.branch == branch
        assert address.agency is None

    def test_validation_branch_uniqueness(self, branch, address_for_branch, db):
        """Test validation prevents duplicate branch addresses"""
        # Arrange - address_for_branch already exists for this branch
        data = {
            "branch": branch.id,
            "street": "Another St",
            "city": "Another City",
            "zipcode": 11111,
            "state": "Another State",
            "country": "Another Country",
        }

        # Act
        serializer = AddressSerializer(data=data)

        # Assert
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors
        assert "An address with the same branch already exists" in str(
            serializer.errors
        )

    def test_validation_allows_update_same_branch(self, address_for_branch, db):
        """Test validation allows updating existing address for same branch"""
        # Arrange - updating existing address
        data = {
            "branch": address_for_branch.branch.id,
            "street": "Updated St",
            "city": "Updated City",
            "zipcode": 11111,
            "state": "Updated State",
            "country": "Updated Country",
        }

        # Act
        serializer = AddressSerializer(address_for_branch, data=data)

        # Assert
        assert serializer.is_valid()
        address = serializer.save()
        assert address.street == "Updated St"

    def test_get_agency_method(self, address_for_agency, db):
        """Test get_agency method returns agency data"""
        # Arrange
        serializer = AddressSerializer(address_for_agency)

        # Act
        agency_data = serializer.get_agency(address_for_agency)

        # Assert
        assert agency_data is not None
        assert agency_data["id"] == address_for_agency.agency.id
        assert agency_data["name"] == "Test Agency"
        # key_stakeholder is the User object, not ID
        assert (
            agency_data["key_stakeholder"] == address_for_agency.agency.key_stakeholder
        )
        assert agency_data["is_active"] is True

    def test_get_agency_method_none(self, address_for_branch, db):
        """Test get_agency method returns None when no agency"""
        # Arrange
        serializer = AddressSerializer(address_for_branch)

        # Act
        agency_data = serializer.get_agency(address_for_branch)

        # Assert
        assert agency_data is None

    def test_get_branch_method(self, address_for_branch, db):
        """Test get_branch method returns branch data"""
        # Arrange
        serializer = AddressSerializer(address_for_branch)

        # Act
        branch_data = serializer.get_branch(address_for_branch)

        # Assert
        assert branch_data is not None
        assert branch_data["id"] == address_for_branch.branch.id
        assert branch_data["name"] == "Test Branch"
        assert branch_data["agency"] == address_for_branch.branch.agency.id

    def test_get_branch_method_none(self, address_for_agency, db):
        """Test get_branch method returns None when no branch"""
        # Arrange
        serializer = AddressSerializer(address_for_agency)

        # Act
        branch_data = serializer.get_branch(address_for_agency)

        # Assert
        assert branch_data is None


class TestTinyUserContactSerializer:
    """Tests for TinyUserContactSerializer"""

    def test_serialization(self, user_contact, db):
        """Test serializing user contact with nested user"""
        # Act
        serializer = TinyUserContactSerializer(user_contact)
        data = serializer.data

        # Assert
        assert data["id"] == user_contact.id
        assert data["user"]["id"] == user_contact.user.id
        assert data["user"]["username"] == "testuser"
        assert data["user"]["email"] == "test@example.com"


class TestUserContactSerializer:
    """Tests for UserContactSerializer"""

    def test_serialization(self, user_contact, db):
        """Test serializing user contact"""
        # Act
        serializer = UserContactSerializer(user_contact)
        data = serializer.data

        # Assert
        assert data["id"] == user_contact.id
        assert data["user"]["id"] == user_contact.user.id
        assert data["user"]["username"] == "testuser"
        assert data["email"] == "user@example.com"
        assert data["phone"] == "1234567890"
        assert data["alt_phone"] == "0987654321"
        assert data["fax"] == "1112223333"

    def test_serialization_all_fields(self, user_contact, db):
        """Test all fields are serialized"""
        # Act
        serializer = UserContactSerializer(user_contact)
        data = serializer.data

        # Assert
        assert "id" in data
        assert "user" in data
        assert "email" in data
        assert "phone" in data
        assert "alt_phone" in data
        assert "fax" in data
        assert "created_at" in data
        assert "updated_at" in data


class TestTinyAgencyContactSerializer:
    """Tests for TinyAgencyContactSerializer"""

    def test_serialization(self, agency_contact, db):
        """Test serializing agency contact with nested agency and address"""
        # Act
        serializer = TinyAgencyContactSerializer(agency_contact)
        data = serializer.data

        # Assert
        assert data["id"] == agency_contact.id
        assert data["agency"]["id"] == agency_contact.agency.id
        assert data["agency"]["name"] == "Test Agency"
        assert data["email"] == "agency@example.com"
        assert data["address"]["id"] == agency_contact.address.id
        assert data["address"]["street"] == "123 Test St"

    def test_serialization_without_address(self, agency, db):
        """Test serializing agency contact without address"""
        # Arrange
        contact = AgencyContact.objects.create(
            agency=agency,
            email="noaddress@example.com",
        )

        # Act
        serializer = TinyAgencyContactSerializer(contact)
        data = serializer.data

        # Assert
        assert data["id"] == contact.id
        assert data["address"] is None


class TestAgencyContactSerializer:
    """Tests for AgencyContactSerializer"""

    def test_serialization(self, agency_contact, db):
        """Test serializing agency contact"""
        # Act
        serializer = AgencyContactSerializer(agency_contact)
        data = serializer.data

        # Assert
        assert data["id"] == agency_contact.id
        assert data["agency"]["id"] == agency_contact.agency.id
        assert data["email"] == "agency@example.com"
        assert data["phone"] == "1234567890"
        assert data["alt_phone"] == "0987654321"
        assert data["fax"] == "1112223333"
        assert data["address"]["id"] == agency_contact.address.id

    def test_serialization_all_fields(self, agency_contact, db):
        """Test all fields are serialized"""
        # Act
        serializer = AgencyContactSerializer(agency_contact)
        data = serializer.data

        # Assert
        assert "id" in data
        assert "agency" in data
        assert "email" in data
        assert "phone" in data
        assert "alt_phone" in data
        assert "fax" in data
        assert "address" in data
        assert "created_at" in data
        assert "updated_at" in data


class TestTinyBranchContactSerializer:
    """Tests for TinyBranchContactSerializer"""

    def test_serialization(self, branch_contact, db):
        """Test serializing branch contact with nested branch and address"""
        # Act
        serializer = TinyBranchContactSerializer(branch_contact)
        data = serializer.data

        # Assert
        assert data["id"] == branch_contact.id
        assert data["branch"]["id"] == branch_contact.branch.id
        assert data["branch"]["name"] == "Test Branch"
        assert data["email"] == "branch@example.com"
        assert data["address"]["id"] == branch_contact.address.id
        assert data["address"]["street"] == "456 Branch St"

    def test_serialization_without_address(self, branch, db):
        """Test serializing branch contact without address"""
        # Arrange
        contact = BranchContact.objects.create(
            branch=branch,
            email="noaddress@example.com",
        )

        # Act
        serializer = TinyBranchContactSerializer(contact)
        data = serializer.data

        # Assert
        assert data["id"] == contact.id
        assert data["address"] is None


class TestBranchContactSerializer:
    """Tests for BranchContactSerializer"""

    def test_serialization(self, branch_contact, db):
        """Test serializing branch contact"""
        # Act
        serializer = BranchContactSerializer(branch_contact)
        data = serializer.data

        # Assert
        assert data["id"] == branch_contact.id
        assert data["branch"]["id"] == branch_contact.branch.id
        assert data["email"] == "branch@example.com"
        assert data["phone"] == "1234567890"
        assert data["alt_phone"] == "0987654321"
        assert data["fax"] == "1112223333"
        assert data["address"]["id"] == branch_contact.address.id

    def test_serialization_all_fields(self, branch_contact, db):
        """Test all fields are serialized"""
        # Act
        serializer = BranchContactSerializer(branch_contact)
        data = serializer.data

        # Assert
        assert "id" in data
        assert "branch" in data
        assert "email" in data
        assert "phone" in data
        assert "alt_phone" in data
        assert "fax" in data
        assert "address" in data
        assert "created_at" in data
        assert "updated_at" in data
