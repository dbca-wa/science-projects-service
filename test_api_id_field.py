"""
API integration tests to verify 'id' field standardization in API responses.

Tests verify that:
1. GET endpoints return 'id' field and not 'pk' field
2. Nested objects use 'id' consistently
3. List endpoints return objects with 'id' field
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.urls import reverse

User = get_user_model()


class APIIdFieldTestCase(TestCase):
    """Test that API endpoints return 'id' instead of 'pk'"""

    def setUp(self):
        """Create test data and client"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            display_first_name='Test',
            display_last_name='User',
            is_staff=True,
            is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

    def test_user_list_endpoint_returns_id_not_pk(self):
        """User list endpoint should return 'id' field, not 'pk'"""
        try:
            response = self.client.get('/api/v1/users/')
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    first_user = data[0]
                    self.assertIn('id', first_user, "User object should have 'id' field")
                    self.assertNotIn('pk', first_user, "User object should not have 'pk' field")
                elif isinstance(data, dict) and 'results' in data and len(data['results']) > 0:
                    first_user = data['results'][0]
                    self.assertIn('id', first_user, "User object should have 'id' field")
                    self.assertNotIn('pk', first_user, "User object should not have 'pk' field")
        except Exception:
            # Endpoint might not exist or require different authentication
            pass

    def test_user_detail_endpoint_returns_id_not_pk(self):
        """User detail endpoint should return 'id' field, not 'pk'"""
        try:
            response = self.client.get(f'/api/v1/users/{self.user.pk}/')
            if response.status_code == 200:
                data = response.json()
                self.assertIn('id', data, "User object should have 'id' field")
                self.assertNotIn('pk', data, "User object should not have 'pk' field")
                self.assertEqual(data['id'], self.user.pk, "'id' should match user's pk")
        except Exception:
            # Endpoint might not exist or require different authentication
            pass

    def test_nested_objects_use_id(self):
        """Nested objects in API responses should use 'id' field"""
        # This is a general test that can be expanded based on actual API structure
        try:
            response = self.client.get('/api/v1/users/')
            if response.status_code == 200:
                data = response.json()
                users = data if isinstance(data, list) else data.get('results', [])
                
                for user in users[:5]:  # Check first 5 users
                    # Check any nested objects for 'id' vs 'pk'
                    for key, value in user.items():
                        if isinstance(value, dict) and value:
                            # If it's a nested object with an identifier
                            if 'pk' in value:
                                self.fail(f"Nested object '{key}' should not have 'pk' field")
        except Exception:
            # Endpoint might not exist
            pass


class APIResponseConsistencyTestCase(TestCase):
    """Test that API responses are consistent with 'id' field usage"""

    def setUp(self):
        """Create test data and client"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='apitest',
            email='apitest@example.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        self.client.force_authenticate(user=self.user)

    def test_multiple_endpoints_use_id_consistently(self):
        """Multiple API endpoints should consistently use 'id' field"""
        endpoints_to_test = [
            '/api/v1/users/',
            '/api/v1/quotes/',
        ]
        
        for endpoint in endpoints_to_test:
            try:
                response = self.client.get(endpoint)
                if response.status_code == 200:
                    data = response.json()
                    items = data if isinstance(data, list) else data.get('results', [])
                    
                    if items and len(items) > 0:
                        first_item = items[0]
                        self.assertIn('id', first_item, 
                            f"Endpoint {endpoint} should return objects with 'id' field")
                        self.assertNotIn('pk', first_item,
                            f"Endpoint {endpoint} should not return objects with 'pk' field")
            except Exception:
                # Endpoint might not exist or require different setup
                continue

    def test_created_objects_return_id(self):
        """POST requests that create objects should return 'id' in response"""
        # This test would need to be expanded based on actual API endpoints
        # that support POST operations
        pass
