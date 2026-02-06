"""
Tests for categories models
"""
import pytest
from django.db import IntegrityError

from categories.models import ProjectCategory


class TestProjectCategoryModel:
    """Tests for ProjectCategory model"""

    def test_create_category_valid_data(self, db):
        """Test creating category with valid data"""
        # Arrange & Act
        category = ProjectCategory.objects.create(
            name='Biodiversity',
            kind=ProjectCategory.CategoryKindChoices.SCIENCE,
        )
        
        # Assert
        assert category.id is not None
        assert category.name == 'Biodiversity'
        assert category.kind == ProjectCategory.CategoryKindChoices.SCIENCE

    def test_category_str_method(self, project_category, db):
        """Test ProjectCategory __str__ method"""
        # Act
        result = str(project_category)
        
        # Assert
        assert result == 'Biodiversity'

    def test_category_kind_choices_science(self, db):
        """Test creating category with science kind"""
        # Arrange & Act
        category = ProjectCategory.objects.create(
            name='Marine Science',
            kind=ProjectCategory.CategoryKindChoices.SCIENCE,
        )
        
        # Assert
        assert category.kind == 'science'

    def test_category_kind_choices_student(self, db):
        """Test creating category with student kind"""
        # Arrange & Act
        category = ProjectCategory.objects.create(
            name='Student Project',
            kind=ProjectCategory.CategoryKindChoices.STUDENT,
        )
        
        # Assert
        assert category.kind == 'student'

    def test_category_kind_choices_external(self, db):
        """Test creating category with external kind"""
        # Arrange & Act
        category = ProjectCategory.objects.create(
            name='External Partnership',
            kind=ProjectCategory.CategoryKindChoices.EXTERNAL,
        )
        
        # Assert
        assert category.kind == 'external'

    def test_category_kind_choices_core_function(self, db):
        """Test creating category with core function kind"""
        # Arrange & Act
        category = ProjectCategory.objects.create(
            name='Core Operations',
            kind=ProjectCategory.CategoryKindChoices.COREFUNCTION,
        )
        
        # Assert
        assert category.kind == 'core_function'

    def test_category_verbose_name(self, db):
        """Test model verbose name"""
        # Act
        verbose_name = ProjectCategory._meta.verbose_name
        
        # Assert
        assert verbose_name == 'Project Category'

    def test_category_verbose_name_plural(self, db):
        """Test model verbose name plural"""
        # Act
        verbose_name_plural = ProjectCategory._meta.verbose_name_plural
        
        # Assert
        assert verbose_name_plural == 'Project Categories'

    def test_category_name_max_length(self, db):
        """Test category name max length"""
        # Act
        max_length = ProjectCategory._meta.get_field('name').max_length
        
        # Assert
        assert max_length == 50

    def test_category_kind_max_length(self, db):
        """Test category kind max length"""
        # Act
        max_length = ProjectCategory._meta.get_field('kind').max_length
        
        # Assert
        assert max_length == 15

    def test_category_inherits_common_model(self, project_category, db):
        """Test category inherits CommonModel fields"""
        # Assert - CommonModel provides created_at and updated_at
        assert hasattr(project_category, 'created_at')
        assert hasattr(project_category, 'updated_at')
        assert project_category.created_at is not None
        assert project_category.updated_at is not None

    def test_category_update(self, project_category, db):
        """Test updating category"""
        # Arrange
        original_name = project_category.name
        
        # Act
        project_category.name = 'Updated Biodiversity'
        project_category.save()
        
        # Assert
        project_category.refresh_from_db()
        assert project_category.name == 'Updated Biodiversity'
        assert project_category.name != original_name

    def test_category_delete(self, project_category, db):
        """Test deleting category"""
        # Arrange
        category_id = project_category.id
        
        # Act
        project_category.delete()
        
        # Assert
        assert not ProjectCategory.objects.filter(id=category_id).exists()

    def test_multiple_categories_same_kind(self, db):
        """Test creating multiple categories with same kind"""
        # Arrange & Act
        category1 = ProjectCategory.objects.create(
            name='Biodiversity',
            kind=ProjectCategory.CategoryKindChoices.SCIENCE,
        )
        category2 = ProjectCategory.objects.create(
            name='Marine Science',
            kind=ProjectCategory.CategoryKindChoices.SCIENCE,
        )
        
        # Assert
        assert category1.kind == category2.kind
        assert category1.name != category2.name
        assert ProjectCategory.objects.filter(kind='science').count() == 2
