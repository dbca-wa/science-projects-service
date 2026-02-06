"""
Tests for agencies serializers
"""
import pytest
from unittest.mock import Mock

from agencies.serializers import (
    AffiliationSerializer,
    AgencySerializer,
    TinyAgencySerializer,
    BranchSerializer,
    TinyBranchSerializer,
    MiniBranchSerializer,
    BusinessAreaSerializer,
    TinyBusinessAreaSerializer,
    MiniBASerializer,
    DivisionSerializer,
    TinyDivisionSerializer,
    DepartmentalServiceSerializer,
    TinyDepartmentalServiceSerializer,
)


class TestAffiliationSerializer:
    """Tests for AffiliationSerializer"""

    def test_serialization(self, affiliation, db):
        """Test serializing an affiliation"""
        # Arrange & Act
        serializer = AffiliationSerializer(affiliation)
        
        # Assert
        assert serializer.data['id'] == affiliation.id
        assert serializer.data['name'] == affiliation.name
        assert 'created_at' in serializer.data
        assert 'updated_at' in serializer.data

    def test_deserialization_valid(self, db):
        """Test deserializing valid affiliation data"""
        # Arrange
        data = {'name': 'New Affiliation'}
        
        # Act
        serializer = AffiliationSerializer(data=data)
        
        # Assert
        assert serializer.is_valid()
        affiliation = serializer.save()
        assert affiliation.name == 'New Affiliation'

    def test_deserialization_invalid_missing_name(self, db):
        """Test deserializing invalid data (missing name)"""
        # Arrange
        data = {}
        
        # Act
        serializer = AffiliationSerializer(data=data)
        
        # Assert
        assert not serializer.is_valid()
        assert 'name' in serializer.errors


class TestAgencySerializer:
    """Tests for AgencySerializer"""

    def test_serialization(self, agency, db):
        """Test serializing an agency"""
        # Arrange & Act
        serializer = AgencySerializer(agency)
        
        # Assert
        assert serializer.data['id'] == agency.id
        assert serializer.data['name'] == agency.name
        assert serializer.data['is_active'] == agency.is_active
        assert serializer.data['key_stakeholder'] == agency.key_stakeholder.id

    def test_deserialization_valid(self, user, db):
        """Test deserializing valid agency data"""
        # Arrange
        data = {
            'name': 'New Agency',
            'is_active': True,
            'key_stakeholder': user.id,
        }
        
        # Act
        serializer = AgencySerializer(data=data)
        
        # Assert
        assert serializer.is_valid()
        agency = serializer.save()
        assert agency.name == 'New Agency'
        assert agency.is_active is True


class TestTinyAgencySerializer:
    """Tests for TinyAgencySerializer"""

    def test_serialization_without_image(self, agency, db):
        """Test serializing agency without image"""
        # Arrange & Act
        serializer = TinyAgencySerializer(agency)
        
        # Assert
        assert serializer.data['id'] == agency.id
        assert serializer.data['name'] == agency.name
        assert serializer.data['image'] is None

    def test_get_image_with_attribute_error(self, agency, db):
        """Test get_image handles AttributeError gracefully"""
        # Arrange
        serializer = TinyAgencySerializer(agency)
        
        # Act
        result = serializer.get_image(agency)
        
        # Assert
        assert result is None


class TestBranchSerializer:
    """Tests for BranchSerializer"""

    def test_serialization(self, branch, db):
        """Test serializing a branch"""
        # Arrange & Act
        serializer = BranchSerializer(branch)
        
        # Assert
        assert serializer.data['id'] == branch.id
        assert serializer.data['name'] == branch.name
        assert serializer.data['agency'] == branch.agency.id
        assert serializer.data['manager'] == branch.manager.id

    def test_deserialization_valid(self, agency, user, db):
        """Test deserializing valid branch data"""
        # Arrange
        data = {
            'name': 'New Branch',
            'agency': agency.id,
            'manager': user.id,
        }
        
        # Act
        serializer = BranchSerializer(data=data)
        
        # Assert
        assert serializer.is_valid()
        branch = serializer.save()
        assert branch.name == 'New Branch'
        assert branch.agency == agency


class TestTinyBranchSerializer:
    """Tests for TinyBranchSerializer"""

    def test_serialization(self, branch, db):
        """Test serializing a branch with tiny serializer"""
        # Arrange & Act
        serializer = TinyBranchSerializer(branch)
        
        # Assert
        assert serializer.data['id'] == branch.id
        assert serializer.data['name'] == branch.name
        assert serializer.data['agency'] == branch.agency.id
        assert serializer.data['manager'] == branch.manager.id


class TestMiniBranchSerializer:
    """Tests for MiniBranchSerializer"""

    def test_serialization(self, branch, db):
        """Test serializing a branch with mini serializer"""
        # Arrange & Act
        serializer = MiniBranchSerializer(branch)
        
        # Assert
        assert serializer.data['id'] == branch.id
        assert serializer.data['name'] == branch.name
        assert 'agency' not in serializer.data
        assert 'manager' not in serializer.data


class TestBusinessAreaSerializer:
    """Tests for BusinessAreaSerializer"""

    def test_serialization(self, business_area, db):
        """Test serializing a business area"""
        # Arrange & Act
        serializer = BusinessAreaSerializer(business_area)
        
        # Assert
        assert serializer.data['id'] == business_area.id
        assert serializer.data['name'] == business_area.name
        assert serializer.data['agency'] == business_area.agency.id
        assert serializer.data['division'] == business_area.division.id

    def test_deserialization_valid(self, agency, division, user, db):
        """Test deserializing valid business area data"""
        # Arrange
        data = {
            'agency': agency.id,
            'name': 'New BA',
            'slug': 'new-ba',
            'division': division.id,
            'leader': user.id,
            'finance_admin': None,
            'data_custodian': None,
        }
        
        # Act
        serializer = BusinessAreaSerializer(data=data)
        
        # Assert
        assert serializer.is_valid()
        ba = serializer.save()
        assert ba.name == 'New BA'
        assert ba.agency == agency


class TestTinyBusinessAreaSerializer:
    """Tests for TinyBusinessAreaSerializer"""

    def test_serialization(self, business_area, db):
        """Test serializing business area with tiny serializer"""
        # Arrange & Act
        serializer = TinyBusinessAreaSerializer(business_area)
        
        # Assert
        assert serializer.data['id'] == business_area.id
        assert serializer.data['name'] == business_area.name
        assert serializer.data['slug'] == business_area.slug
        assert serializer.data['leader'] == business_area.leader.id
        assert 'division' in serializer.data


class TestMiniBASerializer:
    """Tests for MiniBASerializer"""

    def test_serialization(self, business_area, db):
        """Test serializing business area with mini serializer"""
        # Arrange & Act
        serializer = MiniBASerializer(business_area)
        
        # Assert
        assert serializer.data['id'] == business_area.id
        assert serializer.data['name'] == business_area.name
        assert 'leader' in serializer.data
        assert 'caretaker' in serializer.data

    def test_get_image_none(self, business_area, db):
        """Test get_image returns None when no image"""
        # Arrange
        serializer = MiniBASerializer(business_area)
        
        # Act
        result = serializer.get_image(business_area)
        
        # Assert
        assert result is None

    def test_get_project_count(self, business_area, db):
        """Test get_project_count returns count"""
        # Arrange
        serializer = MiniBASerializer(business_area)
        
        # Act
        result = serializer.get_project_count(business_area)
        
        # Assert
        assert result == 0

    def test_get_division(self, business_area, db):
        """Test get_division returns division info"""
        # Arrange
        serializer = MiniBASerializer(business_area)
        
        # Act
        result = serializer.get_division(business_area)
        
        # Assert
        assert result is not None
        assert result['id'] == business_area.division.id
        assert result['name'] == business_area.division.name

    def test_get_division_none(self, agency, db):
        """Test get_division returns None when no division"""
        # Arrange
        from agencies.models import BusinessArea
        ba = BusinessArea.objects.create(
            agency=agency,
            name="No Division BA",
            leader=None,
            finance_admin=None,
            data_custodian=None,
        )
        serializer = MiniBASerializer(ba)
        
        # Act
        result = serializer.get_division(ba)
        
        # Assert
        assert result is None


class TestDivisionSerializer:
    """Tests for DivisionSerializer"""

    def test_serialization(self, division, db):
        """Test serializing a division"""
        # Arrange & Act
        serializer = DivisionSerializer(division)
        
        # Assert
        assert serializer.data['id'] == division.id
        assert serializer.data['name'] == division.name
        assert serializer.data['slug'] == division.slug
        assert serializer.data['director'] == division.director.id

    def test_deserialization_valid(self, user, db):
        """Test deserializing valid division data"""
        # Arrange
        data = {
            'name': 'New Division',
            'slug': 'new-division',
            'director': user.id,
            'approver': user.id,
            # Note: directorate_email_list is ManyToMany, set after creation
        }
        
        # Act
        serializer = DivisionSerializer(data=data)
        
        # Assert
        assert serializer.is_valid(), f"Serializer errors: {serializer.errors}"
        division = serializer.save()
        assert division.name == 'New Division'
        assert division.slug == 'new-division'


class TestTinyDivisionSerializer:
    """Tests for TinyDivisionSerializer"""

    def test_serialization(self, division, db):
        """Test serializing division with tiny serializer"""
        # Arrange & Act
        serializer = TinyDivisionSerializer(division)
        
        # Assert
        assert serializer.data['id'] == division.id
        assert serializer.data['name'] == division.name
        assert serializer.data['slug'] == division.slug

    def test_get_directorate_email_list_empty(self, division, db):
        """Test get_directorate_email_list with no users"""
        # Arrange
        serializer = TinyDivisionSerializer(division)
        
        # Act
        result = serializer.get_directorate_email_list(division)
        
        # Assert
        assert result == []

    def test_get_directorate_email_list_with_users(self, division, user, db):
        """Test get_directorate_email_list with users"""
        # Arrange
        from common.tests.factories import UserFactory
        user1 = UserFactory()
        division.directorate_email_list.add(user1)
        serializer = TinyDivisionSerializer(division)
        
        # Act
        result = serializer.get_directorate_email_list(division)
        
        # Assert
        assert len(result) == 1
        assert result[0]['id'] == user1.id
        assert result[0]['email'] == user1.email


class TestDepartmentalServiceSerializer:
    """Tests for DepartmentalServiceSerializer"""

    def test_serialization(self, departmental_service, db):
        """Test serializing a departmental service"""
        # Arrange & Act
        serializer = DepartmentalServiceSerializer(departmental_service)
        
        # Assert
        assert serializer.data['id'] == departmental_service.id
        assert serializer.data['name'] == departmental_service.name
        assert serializer.data['director'] == departmental_service.director.id

    def test_deserialization_valid(self, user, db):
        """Test deserializing valid departmental service data"""
        # Arrange
        data = {
            'name': 'New Service',
            'director': user.id,
        }
        
        # Act
        serializer = DepartmentalServiceSerializer(data=data)
        
        # Assert
        assert serializer.is_valid()
        service = serializer.save()
        assert service.name == 'New Service'
        assert service.director == user


class TestTinyDepartmentalServiceSerializer:
    """Tests for TinyDepartmentalServiceSerializer"""

    def test_serialization(self, departmental_service, db):
        """Test serializing departmental service with tiny serializer"""
        # Arrange & Act
        serializer = TinyDepartmentalServiceSerializer(departmental_service)
        
        # Assert
        assert serializer.data['id'] == departmental_service.id
        assert serializer.data['name'] == departmental_service.name
        assert serializer.data['director'] == departmental_service.director.id
