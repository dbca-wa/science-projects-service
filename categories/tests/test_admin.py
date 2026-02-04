"""
Tests for categories admin
"""
import pytest
from django.contrib.admin.sites import AdminSite

from categories.admin import ProjectCategoryAdmin
from categories.models import ProjectCategory


class TestProjectCategoryAdmin:
    """Tests for ProjectCategoryAdmin"""

    def test_admin_list_display(self, db):
        """Test admin list display configuration"""
        # Arrange
        admin = ProjectCategoryAdmin(ProjectCategory, AdminSite())
        
        # Act
        list_display = admin.list_display
        
        # Assert
        assert 'name' in list_display
        assert 'kind' in list_display

    def test_admin_list_filter(self, db):
        """Test admin list filter configuration"""
        # Arrange
        admin = ProjectCategoryAdmin(ProjectCategory, AdminSite())
        
        # Act
        list_filter = admin.list_filter
        
        # Assert
        assert 'kind' in list_filter

    def test_admin_registered(self, db):
        """Test ProjectCategory is registered with admin"""
        # Arrange
        from django.contrib import admin
        
        # Act
        is_registered = ProjectCategory in admin.site._registry
        
        # Assert
        assert is_registered

    def test_admin_model_admin_class(self, db):
        """Test correct admin class is registered"""
        # Arrange
        from django.contrib import admin
        
        # Act
        admin_class = admin.site._registry[ProjectCategory]
        
        # Assert
        assert isinstance(admin_class, ProjectCategoryAdmin)
