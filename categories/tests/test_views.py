"""
Tests for categories views
"""
import pytest
from rest_framework import status

from categories.models import ProjectCategory
from common.tests.test_helpers import categories_urls


class TestProjectCategoryViewSet:
    """Tests for ProjectCategoryViewSet"""

    def test_list_categories(self, api_client, user, project_category, db):
        """Test listing categories"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(categories_urls.list())
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['id'] == project_category.id

    def test_list_categories_filters_science_only(self, api_client, user, project_category, student_category, db):
        """Test listing categories only returns science categories"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(categories_urls.list())
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1  # Only science category
        assert response.data[0]['kind'] == 'science'

    def test_list_categories_empty(self, api_client, user, db):
        """Test listing categories when none exist"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(categories_urls.list())
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    def test_retrieve_category(self, api_client, user, project_category, db):
        """Test retrieving single category"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(categories_urls.detail(project_category.id))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == project_category.id
        assert response.data['name'] == project_category.name
        assert response.data['kind'] == project_category.kind

    def test_retrieve_category_not_found(self, api_client, user, db):
        """Test retrieving non-existent category"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(categories_urls.detail(999))
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_category(self, api_client, user, db):
        """Test creating category"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            'name': 'New Category',
            'kind': 'science',
        }
        
        # Act
        response = api_client.post(categories_urls.list(), data, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Category'
        assert response.data['kind'] == 'science'
        assert ProjectCategory.objects.filter(name='New Category').exists()

    def test_create_category_invalid_data(self, api_client, user, db):
        """Test creating category with invalid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            'name': '',  # Empty name
            'kind': 'science',
        }
        
        # Act
        response = api_client.post(categories_urls.list(), data, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data

    def test_create_category_missing_kind(self, api_client, user, db):
        """Test creating category without kind"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            'name': 'New Category',
        }
        
        # Act
        response = api_client.post(categories_urls.list(), data, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'kind' in response.data

    def test_create_category_invalid_kind(self, api_client, user, db):
        """Test creating category with invalid kind"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            'name': 'New Category',
            'kind': 'invalid_kind',
        }
        
        # Act
        response = api_client.post(categories_urls.list(), data, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'kind' in response.data

    def test_update_category(self, api_client, user, project_category, db):
        """Test updating category"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            'name': 'Updated Category',
            'kind': 'science',
        }
        
        # Act
        response = api_client.put(
            categories_urls.detail(project_category.id),
            data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Category'
        project_category.refresh_from_db()
        assert project_category.name == 'Updated Category'

    def test_update_category_partial(self, api_client, user, project_category, db):
        """Test partial update of category"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            'name': 'Partially Updated',
        }
        
        # Act
        response = api_client.put(
            categories_urls.detail(project_category.id),
            data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Partially Updated'
        project_category.refresh_from_db()
        assert project_category.name == 'Partially Updated'
        assert project_category.kind == 'science'  # Unchanged

    def test_update_category_not_found(self, api_client, user, db):
        """Test updating non-existent category"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            'name': 'Updated Category',
            'kind': 'science',
        }
        
        # Act
        response = api_client.put(categories_urls.detail(999), data, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_category(self, api_client, user, project_category, db):
        """Test deleting category"""
        # Arrange
        api_client.force_authenticate(user=user)
        category_id = project_category.id
        
        # Act
        response = api_client.delete(categories_urls.detail(category_id))
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not ProjectCategory.objects.filter(id=category_id).exists()

    def test_delete_category_not_found(self, api_client, user, db):
        """Test deleting non-existent category"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.delete(categories_urls.detail(999))
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_multiple_science_categories(self, api_client, user, db):
        """Test listing multiple science categories"""
        # Arrange
        api_client.force_authenticate(user=user)
        category1 = ProjectCategory.objects.create(name='Biodiversity', kind='science')
        category2 = ProjectCategory.objects.create(name='Marine Science', kind='science')
        category3 = ProjectCategory.objects.create(name='Student Project', kind='student')
        
        # Act
        response = api_client.get(categories_urls.list())
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2  # Only science categories
        names = [item['name'] for item in response.data]
        assert 'Biodiversity' in names
        assert 'Marine Science' in names
        assert 'Student Project' not in names

    def test_create_all_kind_types(self, api_client, user, db):
        """Test creating categories with all kind types"""
        # Arrange
        api_client.force_authenticate(user=user)
        kinds = ['science', 'student', 'external', 'core_function']
        
        # Act & Assert
        for kind in kinds:
            data = {
                'name': f'{kind.title()} Category',
                'kind': kind,
            }
            response = api_client.post(categories_urls.list(), data, format='json')
            assert response.status_code == status.HTTP_201_CREATED
            assert response.data['kind'] == kind

    def test_viewset_queryset_filters_science(self, api_client, user, db):
        """Test viewset queryset only includes science categories"""
        # Arrange
        api_client.force_authenticate(user=user)
        science_cat = ProjectCategory.objects.create(name='Science', kind='science')
        student_cat = ProjectCategory.objects.create(name='Student', kind='student')
        external_cat = ProjectCategory.objects.create(name='External', kind='external')
        core_cat = ProjectCategory.objects.create(name='Core', kind='core_function')
        
        # Act
        response = api_client.get(categories_urls.list())
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['id'] == science_cat.id
        
        # Verify other categories exist but aren't returned
        assert ProjectCategory.objects.count() == 4

    def test_list_categories_unauthenticated(self, api_client, project_category, db):
        """Test listing categories without authentication"""
        # Act
        response = api_client.get(categories_urls.list())
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_category_unauthenticated(self, api_client, db):
        """Test creating category without authentication"""
        # Arrange
        data = {
            'name': 'New Category',
            'kind': 'science',
        }
        
        # Act
        response = api_client.post(categories_urls.list(), data, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
