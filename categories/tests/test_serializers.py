"""
Tests for categories serializers
"""
import pytest

from categories.models import ProjectCategory
from categories.serializers import ProjectCategorySerializer


class TestProjectCategorySerializer:
    """Tests for ProjectCategorySerializer"""

    def test_serialize_category(self, project_category, db):
        """Test serializing category to JSON"""
        # Arrange
        serializer = ProjectCategorySerializer(project_category)
        
        # Act
        data = serializer.data
        
        # Assert
        assert data['id'] == project_category.id
        assert data['name'] == project_category.name
        assert data['kind'] == project_category.kind

    def test_serialize_multiple_categories(self, project_category, student_category, db):
        """Test serializing multiple categories"""
        # Arrange
        categories = [project_category, student_category]
        serializer = ProjectCategorySerializer(categories, many=True)
        
        # Act
        data = serializer.data
        
        # Assert
        assert len(data) == 2
        assert data[0]['id'] == project_category.id
        assert data[1]['id'] == student_category.id

    def test_deserialize_valid_data(self, db):
        """Test deserializing valid JSON to category"""
        # Arrange
        data = {
            'name': 'New Category',
            'kind': 'science',
        }
        serializer = ProjectCategorySerializer(data=data)
        
        # Act
        is_valid = serializer.is_valid()
        
        # Assert
        assert is_valid
        category = serializer.save()
        assert category.name == 'New Category'
        assert category.kind == 'science'

    def test_deserialize_missing_name(self, db):
        """Test deserializing with missing name"""
        # Arrange
        data = {
            'kind': 'science',
        }
        serializer = ProjectCategorySerializer(data=data)
        
        # Act
        is_valid = serializer.is_valid()
        
        # Assert
        assert not is_valid
        assert 'name' in serializer.errors

    def test_deserialize_missing_kind(self, db):
        """Test deserializing with missing kind"""
        # Arrange
        data = {
            'name': 'New Category',
        }
        serializer = ProjectCategorySerializer(data=data)
        
        # Act
        is_valid = serializer.is_valid()
        
        # Assert
        assert not is_valid
        assert 'kind' in serializer.errors

    def test_deserialize_invalid_kind(self, db):
        """Test deserializing with invalid kind"""
        # Arrange
        data = {
            'name': 'New Category',
            'kind': 'invalid_kind',
        }
        serializer = ProjectCategorySerializer(data=data)
        
        # Act
        is_valid = serializer.is_valid()
        
        # Assert
        assert not is_valid
        assert 'kind' in serializer.errors

    def test_deserialize_empty_name(self, db):
        """Test deserializing with empty name"""
        # Arrange
        data = {
            'name': '',
            'kind': 'science',
        }
        serializer = ProjectCategorySerializer(data=data)
        
        # Act
        is_valid = serializer.is_valid()
        
        # Assert
        assert not is_valid
        assert 'name' in serializer.errors

    def test_update_category(self, project_category, db):
        """Test updating category via serializer"""
        # Arrange
        data = {
            'name': 'Updated Biodiversity',
            'kind': 'science',
        }
        serializer = ProjectCategorySerializer(project_category, data=data)
        
        # Act
        is_valid = serializer.is_valid()
        
        # Assert
        assert is_valid
        updated_category = serializer.save()
        assert updated_category.name == 'Updated Biodiversity'
        assert updated_category.id == project_category.id

    def test_partial_update_category(self, project_category, db):
        """Test partial update of category via serializer"""
        # Arrange
        data = {
            'name': 'Partially Updated',
        }
        serializer = ProjectCategorySerializer(project_category, data=data, partial=True)
        
        # Act
        is_valid = serializer.is_valid()
        
        # Assert
        assert is_valid
        updated_category = serializer.save()
        assert updated_category.name == 'Partially Updated'
        assert updated_category.kind == project_category.kind  # Unchanged

    def test_serializer_fields(self, db):
        """Test serializer includes correct fields"""
        # Arrange
        serializer = ProjectCategorySerializer()
        
        # Act
        fields = serializer.fields.keys()
        
        # Assert
        assert 'id' in fields
        assert 'name' in fields
        assert 'kind' in fields
        assert len(fields) == 3

    def test_serialize_all_kind_choices(self, project_category, student_category, external_category, core_function_category, db):
        """Test serializing categories with all kind choices"""
        # Arrange
        categories = [project_category, student_category, external_category, core_function_category]
        serializer = ProjectCategorySerializer(categories, many=True)
        
        # Act
        data = serializer.data
        
        # Assert
        assert len(data) == 4
        kinds = [item['kind'] for item in data]
        assert 'science' in kinds
        assert 'student' in kinds
        assert 'external' in kinds
        assert 'core_function' in kinds
