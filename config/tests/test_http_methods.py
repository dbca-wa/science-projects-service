"""
Test HTTP methods work correctly without trailing slashes.
Verifies that PUT/PATCH/DELETE requests don't cause 500 errors.
"""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from common.tests.test_helpers import caretakers_urls, projects_urls, users_urls

User = get_user_model()


class HTTPMethodsTestCase(TestCase):
    """Test that all HTTP methods work without trailing slashes."""

    def setUp(self):
        """Create test user."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.client = Client()

    def test_put_request_no_500_error(self):
        """Test that PUT requests don't cause 500 errors (original issue)."""
        # This was the original failing request
        response = self.client.put(
            users_urls.path(self.user.id, "pi"), content_type="application/json"
        )

        # Should NOT be 500 (server error)
        # Will be 401/403 (auth) or 400 (bad request), but not 500
        self.assertNotEqual(
            response.status_code,
            500,
            "PUT request should not cause 500 error with APPEND_SLASH=False",
        )

    def test_patch_request_no_500_error(self):
        """Test that PATCH requests don't cause 500 errors."""
        response = self.client.patch(
            users_urls.detail(self.user.id), content_type="application/json"
        )

        self.assertNotEqual(
            response.status_code, 500, "PATCH request should not cause 500 error"
        )

    def test_delete_request_no_500_error(self):
        """Test that DELETE requests don't cause 500 errors."""
        response = self.client.delete(users_urls.detail(self.user.id))

        self.assertNotEqual(
            response.status_code, 500, "DELETE request should not cause 500 error"
        )

    def test_get_request_works(self):
        """Test that GET requests still work."""
        response = self.client.get(users_urls.detail(self.user.id))

        # Should be 401 (not authenticated) or 200 (success)
        self.assertIn(
            response.status_code, [200, 401, 403], "GET request should work normally"
        )

    def test_post_request_works(self):
        """Test that POST requests still work."""
        response = self.client.post(users_urls.list(), content_type="application/json")

        # Should be 400/401/403, not 500
        self.assertNotEqual(
            response.status_code, 500, "POST request should not cause 500 error"
        )

    def test_no_301_redirects(self):
        """Test that requests don't cause 301 redirects."""
        # Test various endpoints
        endpoints = [
            users_urls.detail(self.user.id),
            users_urls.path("me"),
            caretakers_urls.list(),
            projects_urls.list(),
        ]

        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertNotEqual(
                response.status_code,
                301,
                f"GET {endpoint} should not cause 301 redirect",
            )
