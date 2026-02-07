"""
Test URL construction with include() and no trailing slashes.
Verifies that Django correctly concatenates URL patterns.
"""

from django.test import TestCase
from django.urls import resolve


class URLConstructionTestCase(TestCase):
    """Test that URL patterns are constructed correctly without trailing slashes."""

    def test_projects_base_url(self):
        """Test that /api/v1/projects/list resolves correctly."""
        # This should resolve to the Projects view
        url = "/api/v1/projects/list"
        resolved = resolve(url)
        self.assertIsNotNone(resolved)

    def test_projects_map_url(self):
        """Test that /api/v1/projects/map resolves correctly."""
        url = "/api/v1/projects/map"
        resolved = resolve(url)
        # Should resolve without 404
        self.assertIsNotNone(resolved)

    def test_projects_mine_url(self):
        """Test that /api/v1/projects/mine resolves correctly."""
        url = "/api/v1/projects/mine"
        resolved = resolve(url)
        self.assertIsNotNone(resolved)

    def test_projects_detail_url(self):
        """Test that /api/v1/projects/123 resolves correctly."""
        url = "/api/v1/projects/123"
        resolved = resolve(url)
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.kwargs["pk"], 123)

    def test_users_base_url(self):
        """Test that /api/v1/users/list resolves correctly."""
        url = "/api/v1/users/list"
        resolved = resolve(url)
        self.assertIsNotNone(resolved)

    def test_users_me_url(self):
        """Test that /api/v1/users/me resolves correctly."""
        url = "/api/v1/users/me"
        resolved = resolve(url)
        self.assertIsNotNone(resolved)

    def test_users_detail_url(self):
        """Test that /api/v1/users/123 resolves correctly."""
        url = "/api/v1/users/123"
        resolved = resolve(url)
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.kwargs["pk"], 123)

    def test_caretakers_base_url(self):
        """Test that /api/v1/caretakers/list resolves correctly."""
        url = "/api/v1/caretakers/list"
        resolved = resolve(url)
        self.assertIsNotNone(resolved)

    def test_caretakers_requests_url(self):
        """Test that /api/v1/caretakers/requests resolves correctly."""
        url = "/api/v1/caretakers/requests"
        resolved = resolve(url)
        self.assertIsNotNone(resolved)

    def test_caretakers_check_url(self):
        """Test that /api/v1/caretakers/check resolves correctly."""
        url = "/api/v1/caretakers/check"
        resolved = resolve(url)
        self.assertIsNotNone(resolved)

    def test_no_trailing_slash_404(self):
        """Test that URLs WITH trailing slashes return 404 (since APPEND_SLASH=False)."""
        from django.test import Client

        client = Client()

        # These should all return 404 because we have APPEND_SLASH=False
        response = client.get("/api/v1/projects/list/")
        self.assertEqual(response.status_code, 404)

        response = client.get("/api/v1/users/list/")
        self.assertEqual(response.status_code, 404)

        response = client.get("/api/v1/caretakers/list/")
        self.assertEqual(response.status_code, 404)

    def test_nested_paths_work(self):
        """Test that nested paths like /projects/123/team work correctly."""
        url = "/api/v1/projects/123/team"
        resolved = resolve(url)
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.kwargs["pk"], 123)

    def test_multi_level_paths(self):
        """Test that multi-level paths like /projects/remedy/open_closed work."""
        url = "/api/v1/projects/remedy/open_closed"
        resolved = resolve(url)
        self.assertIsNotNone(resolved)

    def test_url_concatenation_examples(self):
        """
        Test specific examples to verify Django concatenates correctly.

        With config: path("api/v1/projects", include("projects.urls"))
        And projects: path("map", ...)
        Result should be: /api/v1/projects/map (NOT /api/v1/projectsmap)
        """
        # Test that "map" is correctly appended with /
        url = "/api/v1/projects/map"
        resolved = resolve(url)
        self.assertIsNotNone(resolved)

        # Test that this WRONG URL doesn't work
        from django.urls.exceptions import Resolver404

        with self.assertRaises(Resolver404):
            resolve("/api/v1/projectsmap")  # This should NOT work
