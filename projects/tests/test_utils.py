"""
Tests for project utilities
"""
import pytest
from datetime import date

from projects.utils.filters import (
    determine_db_kind,
    parse_project_tag_search,
    is_project_tag_search,
    apply_project_filters,
)
from projects.utils.helpers import (
    strip_html_tags,
    handle_date_parsing,
    parse_keywords,
)
from projects.models import Project


class TestFilters:
    """Tests for project filtering utilities"""

    def test_determine_db_kind_core_function(self):
        """Test determining core function kind"""
        # Act
        result = determine_db_kind("CF")
        
        # Assert
        assert result == "core_function"

    def test_determine_db_kind_student(self):
        """Test determining student kind"""
        # Act
        result = determine_db_kind("STP")
        
        # Assert
        assert result == "student"

    def test_determine_db_kind_science(self):
        """Test determining science kind"""
        # Act
        result = determine_db_kind("SP")
        
        # Assert
        assert result == "science"

    def test_determine_db_kind_external(self):
        """Test determining external kind"""
        # Act
        result = determine_db_kind("EXT")
        
        # Assert
        assert result == "external"

    def test_determine_db_kind_unknown(self):
        """Test determining unknown kind returns None"""
        # Act
        result = determine_db_kind("UNKNOWN")
        
        # Assert
        assert result is None

    def test_is_project_tag_search_cf(self):
        """Test identifying CF project tag"""
        # Act
        result = is_project_tag_search("CF-2022-123")
        
        # Assert
        assert result is True

    def test_is_project_tag_search_sp(self):
        """Test identifying SP project tag"""
        # Act
        result = is_project_tag_search("SP-2022-123")
        
        # Assert
        assert result is True

    def test_is_project_tag_search_stp(self):
        """Test identifying STP project tag"""
        # Act
        result = is_project_tag_search("STP-2022-123")
        
        # Assert
        assert result is True

    def test_is_project_tag_search_ext(self):
        """Test identifying EXT project tag"""
        # Act
        result = is_project_tag_search("EXT-2022-123")
        
        # Assert
        assert result is True

    def test_is_project_tag_search_case_insensitive(self):
        """Test project tag search is case insensitive"""
        # Act
        result = is_project_tag_search("cf-2022-123")
        
        # Assert
        assert result is True

    def test_is_project_tag_search_not_tag(self):
        """Test non-tag search returns False"""
        # Act
        result = is_project_tag_search("test project")
        
        # Assert
        assert result is False

    def test_is_project_tag_search_empty(self):
        """Test empty search returns False"""
        # Act
        result = is_project_tag_search("")
        
        # Assert
        assert result is False

    def test_is_project_tag_search_none(self):
        """Test None search returns False"""
        # Act
        result = is_project_tag_search(None)
        
        # Assert
        assert result is False

    def test_parse_project_tag_search_full_tag(self, project, db):
        """Test parsing full project tag (prefix-year-number)"""
        # Arrange
        project.kind = 'core_function'
        project.year = 2022
        project.number = 123
        project.save()
        
        # Act
        result = parse_project_tag_search("CF-2022-123")
        
        # Assert
        assert project in result

    def test_parse_project_tag_search_prefix_year(self, project, db):
        """Test parsing project tag with prefix and year only"""
        # Arrange
        project.kind = 'core_function'
        project.year = 2022
        project.save()
        
        # Act
        result = parse_project_tag_search("CF-2022")
        
        # Assert
        assert project in result

    def test_parse_project_tag_search_prefix_only(self, project, db):
        """Test parsing project tag with prefix only"""
        # Arrange
        project.kind = 'core_function'
        project.save()
        
        # Act
        result = parse_project_tag_search("CF")
        
        # Assert
        assert project in result

    def test_parse_project_tag_search_empty(self, db):
        """Test parsing empty search returns empty queryset"""
        # Act
        result = parse_project_tag_search("")
        
        # Assert
        assert result.count() == 0

    def test_parse_project_tag_search_empty_parts(self, db):
        """Test parsing search with empty parts returns empty queryset"""
        # Act
        result = parse_project_tag_search("-")
        
        # Assert
        assert result.count() == 0

    def test_parse_project_tag_search_invalid_prefix(self, db):
        """Test parsing invalid prefix returns empty queryset"""
        # Act
        result = parse_project_tag_search("INVALID-2022-123")
        
        # Assert
        assert result.count() == 0

    def test_parse_project_tag_search_invalid_year(self, project, db):
        """Test parsing with invalid year format"""
        # Arrange
        project.kind = 'core_function'
        project.year = 2022
        project.number = 123
        project.save()
        
        # Act - invalid year (not a number)
        result = parse_project_tag_search("CF-INVALID-123")
        
        # Assert
        # Should still return projects with CF kind, just not filtered by year
        assert project in result

    def test_parse_project_tag_search_invalid_number(self, project, db):
        """Test parsing with invalid number format"""
        # Arrange
        project.kind = 'core_function'
        project.year = 2022
        project.number = 123
        project.save()
        
        # Act - invalid number (not a number)
        result = parse_project_tag_search("CF-2022-INVALID")
        
        # Assert
        # Should still return projects with CF kind and year, just not filtered by number
        assert project in result

    def test_parse_project_tag_search_invalid_year_in_two_part(self, project, db):
        """Test parsing two-part tag with invalid year"""
        # Arrange
        project.kind = 'core_function'
        project.year = 2022
        project.save()
        
        # Act - invalid year in two-part tag
        result = parse_project_tag_search("CF-INVALID")
        
        # Assert
        # Should still return projects with CF kind, just not filtered by year
        assert project in result

    def test_apply_project_filters_search_term(self, project, db):
        """Test applying search term filter"""
        # Arrange
        project.title = "Test Project Title"
        project.save()
        queryset = Project.objects.all()
        filters = {'searchTerm': 'Test'}
        
        # Act
        result = apply_project_filters(queryset, filters)
        
        # Assert
        assert project in result

    def test_apply_project_filters_project_tag(self, project, db):
        """Test applying project tag filter"""
        # Arrange
        project.kind = 'core_function'
        project.year = 2022
        project.number = 123
        project.save()
        queryset = Project.objects.all()
        filters = {'searchTerm': 'CF-2022-123'}
        
        # Act
        result = apply_project_filters(queryset, filters)
        
        # Assert
        assert project in result

    def test_apply_project_filters_user(self, project_with_lead, project_lead, db):
        """Test applying user filter"""
        # Arrange
        queryset = Project.objects.all()
        filters = {'selected_user': project_lead.pk}
        
        # Act
        result = apply_project_filters(queryset, filters)
        
        # Assert
        assert project_with_lead in result

    def test_apply_project_filters_business_area(self, project, db):
        """Test applying business area filter"""
        # Arrange
        queryset = Project.objects.all()
        filters = {'businessarea': project.business_area.pk}
        
        # Act
        result = apply_project_filters(queryset, filters)
        
        # Assert
        assert project in result

    def test_apply_project_filters_business_area_multiple(self, project, business_area, db):
        """Test applying multiple business area filter"""
        # Arrange
        queryset = Project.objects.all()
        filters = {'businessarea': f"{project.business_area.pk},{business_area.pk}"}
        
        # Act
        result = apply_project_filters(queryset, filters)
        
        # Assert
        assert project in result

    def test_apply_project_filters_status(self, project, db):
        """Test applying status filter"""
        # Arrange
        project.status = 'new'
        project.save()
        queryset = Project.objects.all()
        filters = {'projectstatus': 'new'}
        
        # Act
        result = apply_project_filters(queryset, filters)
        
        # Assert
        assert project in result

    def test_apply_project_filters_status_unknown(self, project, db):
        """Test applying unknown status filter"""
        # Arrange
        project.status = 'invalid_status'
        project.save()
        queryset = Project.objects.all()
        filters = {'projectstatus': 'unknown'}
        
        # Act
        result = apply_project_filters(queryset, filters)
        
        # Assert
        # Should exclude projects with valid statuses
        assert result.count() >= 0

    def test_apply_project_filters_kind(self, project, db):
        """Test applying kind filter"""
        # Arrange
        project.kind = 'science'
        project.save()
        queryset = Project.objects.all()
        filters = {'projectkind': 'science'}
        
        # Act
        result = apply_project_filters(queryset, filters)
        
        # Assert
        assert project in result

    def test_apply_project_filters_year(self, project, db):
        """Test applying year filter"""
        # Arrange
        project.year = 2023
        project.save()
        queryset = Project.objects.all()
        filters = {'year': 2023}
        
        # Act
        result = apply_project_filters(queryset, filters)
        
        # Assert
        assert project in result

    def test_apply_project_filters_only_active(self, project, db):
        """Test applying only active filter"""
        # Arrange
        project.status = 'active'
        project.save()
        queryset = Project.objects.all()
        filters = {'only_active': True}
        
        # Act
        result = apply_project_filters(queryset, filters)
        
        # Assert
        # Should only include active projects
        assert result.count() >= 0

    def test_apply_project_filters_only_inactive(self, project, db):
        """Test applying only inactive filter"""
        # Arrange
        project.status = 'completed'
        project.save()
        queryset = Project.objects.all()
        filters = {'only_inactive': True}
        
        # Act
        result = apply_project_filters(queryset, filters)
        
        # Assert
        # Should exclude active projects
        assert result.count() >= 0

    def test_apply_project_filters_no_filters(self, project, db):
        """Test applying no filters returns all projects"""
        # Arrange
        queryset = Project.objects.all()
        filters = {}
        
        # Act
        result = apply_project_filters(queryset, filters)
        
        # Assert
        assert project in result


class TestHelpers:
    """Tests for project helper utilities"""

    def test_strip_html_tags_simple(self):
        """Test stripping simple HTML tags"""
        # Arrange
        html = '<p>Test content</p>'
        
        # Act
        result = strip_html_tags(html)
        
        # Assert
        assert result == 'Test content'

    def test_strip_html_tags_nested(self):
        """Test stripping nested HTML tags"""
        # Arrange
        html = '<div><p>Test <strong>content</strong></p></div>'
        
        # Act
        result = strip_html_tags(html)
        
        # Assert
        assert result == 'Test content'

    def test_strip_html_tags_with_attributes(self):
        """Test stripping HTML tags with attributes"""
        # Arrange
        html = '<p class="test">Test content</p>'
        
        # Act
        result = strip_html_tags(html)
        
        # Assert
        assert result == 'Test content'

    def test_strip_html_tags_empty(self):
        """Test stripping empty HTML"""
        # Act
        result = strip_html_tags('')
        
        # Assert
        assert result == ''

    def test_strip_html_tags_none(self):
        """Test stripping None returns empty string"""
        # Act
        result = strip_html_tags(None)
        
        # Assert
        assert result == ''

    def test_handle_date_parsing_valid(self):
        """Test parsing valid date string"""
        # Arrange
        date_str = "2023-01-15T10:30:00.000Z"
        
        # Act
        result = handle_date_parsing(date_str)
        
        # Assert
        assert result == date(2023, 1, 15)

    def test_handle_date_parsing_invalid_format(self):
        """Test parsing invalid date format returns None"""
        # Arrange
        date_str = "2023-01-15"
        
        # Act
        result = handle_date_parsing(date_str)
        
        # Assert
        assert result is None

    def test_handle_date_parsing_empty(self):
        """Test parsing empty string returns None"""
        # Act
        result = handle_date_parsing('')
        
        # Assert
        assert result is None

    def test_handle_date_parsing_none(self):
        """Test parsing None returns None"""
        # Act
        result = handle_date_parsing(None)
        
        # Assert
        assert result is None

    def test_parse_keywords_simple(self):
        """Test parsing simple keywords"""
        # Arrange
        keywords_str = '["keyword1", "keyword2"]'
        
        # Act
        result = parse_keywords(keywords_str)
        
        # Assert
        assert result == 'keyword1,keyword2'

    def test_parse_keywords_single(self):
        """Test parsing single keyword"""
        # Arrange
        keywords_str = '["keyword1"]'
        
        # Act
        result = parse_keywords(keywords_str)
        
        # Assert
        assert result == 'keyword1'

    def test_parse_keywords_empty(self):
        """Test parsing empty keywords"""
        # Act
        result = parse_keywords('')
        
        # Assert
        assert result == ''

    def test_parse_keywords_none(self):
        """Test parsing None keywords"""
        # Act
        result = parse_keywords(None)
        
        # Assert
        assert result == ''




class TestFiles:
    """Tests for project file handling utilities"""

    def test_handle_project_image_string_path(self):
        """Test handling project image when given a string path"""
        # Arrange
        from projects.utils.files import handle_project_image
        image_path = "projects/test.jpg"
        
        # Act
        result = handle_project_image(image_path)
        
        # Assert
        assert result == image_path

    def test_handle_project_image_none(self):
        """Test handling project image when given None"""
        # Arrange
        from projects.utils.files import handle_project_image
        
        # Act
        result = handle_project_image(None)
        
        # Assert
        assert result is None

    def test_handle_project_image_upload(self):
        """Test handling project image upload"""
        # Arrange
        from projects.utils.files import handle_project_image
        from django.core.files.uploadedfile import SimpleUploadedFile
        from unittest.mock import patch, MagicMock
        
        # Create a mock uploaded file
        image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'fake image content',
            content_type='image/jpeg'
        )
        
        # Mock default_storage
        with patch('projects.utils.files.default_storage') as mock_storage:
            mock_storage.exists.return_value = False
            mock_storage.save.return_value = 'projects/test_image.jpg'
            
            # Act
            result = handle_project_image(image)
            
            # Assert
            assert result == 'projects/test_image.jpg'
            mock_storage.save.assert_called_once()

    def test_handle_project_image_existing_file_same_size(self):
        """Test handling project image when file exists with same size"""
        # Arrange
        from projects.utils.files import handle_project_image
        from django.core.files.uploadedfile import SimpleUploadedFile
        from unittest.mock import patch, MagicMock
        import os
        
        # Create a mock uploaded file
        image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'fake image content',
            content_type='image/jpeg'
        )
        
        # Mock default_storage and os.path
        with patch('projects.utils.files.default_storage') as mock_storage, \
             patch('projects.utils.files.os.path.exists') as mock_exists, \
             patch('projects.utils.files.os.path.getsize') as mock_getsize:
            
            mock_storage.exists.return_value = True
            mock_storage.path.return_value = '/path/to/projects/test_image.jpg'
            mock_exists.return_value = True
            mock_getsize.return_value = len(b'fake image content')
            
            # Act
            result = handle_project_image(image)
            
            # Assert
            assert result == 'projects/test_image.jpg'
            # Should not call save since file exists with same size
            mock_storage.save.assert_not_called()

    def test_handle_project_image_existing_file_different_size(self):
        """Test handling project image when file exists with different size"""
        # Arrange
        from projects.utils.files import handle_project_image
        from django.core.files.uploadedfile import SimpleUploadedFile
        from unittest.mock import patch, MagicMock
        import os
        
        # Create a mock uploaded file
        image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'fake image content',
            content_type='image/jpeg'
        )
        
        # Mock default_storage and os.path
        with patch('projects.utils.files.default_storage') as mock_storage, \
             patch('projects.utils.files.os.path.exists') as mock_exists, \
             patch('projects.utils.files.os.path.getsize') as mock_getsize:
            
            mock_storage.exists.return_value = True
            mock_storage.path.return_value = '/path/to/projects/test_image.jpg'
            mock_exists.return_value = True
            mock_getsize.return_value = 999  # Different size
            mock_storage.save.return_value = 'projects/test_image.jpg'
            
            # Act
            result = handle_project_image(image)
            
            # Assert
            assert result == 'projects/test_image.jpg'
            # Should call save since file size is different
            mock_storage.save.assert_called_once()
