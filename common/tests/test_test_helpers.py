"""
Tests for test helper utilities.

Ensures URL construction helpers work correctly.
"""

from common.tests.test_helpers import (
    APIUrlBuilder,
    api_url,
    documents_urls,
    projects_urls,
    users_urls,
)


class TestApiUrlFunction:
    """Tests for api_url() function"""

    def test_app_only(self):
        """Test URL with app name only"""
        assert api_url("documents") == "/api/v1/documents/list"
        assert api_url("projects") == "/api/v1/projects/list"
        assert api_url("users") == "/api/v1/users/list"

    def test_app_with_path(self):
        """Test URL with app name and path"""
        assert api_url("documents", "conceptplans") == "/api/v1/documents/conceptplans"
        assert api_url("projects", "export") == "/api/v1/projects/export"
        assert api_url("users", "log-in") == "/api/v1/users/log-in"

    def test_app_with_nested_path(self):
        """Test URL with nested path"""
        assert (
            api_url("documents", "reports/download")
            == "/api/v1/documents/reports/download"
        )
        assert api_url("projects", "areas/types") == "/api/v1/projects/areas/types"

    def test_app_with_id(self):
        """Test URL with ID in path"""
        assert (
            api_url("documents", "conceptplans/123")
            == "/api/v1/documents/conceptplans/123"
        )
        assert api_url("projects", "456") == "/api/v1/projects/456"

    def test_leading_slash_removed(self):
        """Test that leading slash in path is removed"""
        assert api_url("documents", "/conceptplans") == "/api/v1/documents/conceptplans"
        assert api_url("projects", "/export") == "/api/v1/projects/export"


class TestAPIUrlBuilder:
    """Tests for APIUrlBuilder class"""

    def test_list_method(self):
        """Test list() method"""
        builder = APIUrlBuilder("documents")
        assert builder.list() == "/api/v1/documents/list"

        builder = APIUrlBuilder("projects")
        assert builder.list() == "/api/v1/projects/list"

    def test_detail_method(self):
        """Test detail() method"""
        builder = APIUrlBuilder("documents")
        assert builder.detail(123) == "/api/v1/documents/123"
        assert builder.detail(456) == "/api/v1/documents/456"

    def test_path_single_part(self):
        """Test path() with single part"""
        builder = APIUrlBuilder("documents")
        assert builder.path("conceptplans") == "/api/v1/documents/conceptplans"
        assert builder.path("reports") == "/api/v1/documents/reports"

    def test_path_multiple_parts(self):
        """Test path() with multiple parts"""
        builder = APIUrlBuilder("documents")
        assert builder.path("conceptplans", 123) == "/api/v1/documents/conceptplans/123"
        assert (
            builder.path("reports", "download") == "/api/v1/documents/reports/download"
        )
        assert (
            builder.path("reports", 456, "generate_pdf")
            == "/api/v1/documents/reports/456/generate_pdf"
        )

    def test_path_with_integers(self):
        """Test path() with integer parts"""
        builder = APIUrlBuilder("projects")
        assert builder.path(123) == "/api/v1/projects/123"
        assert builder.path("members", 456) == "/api/v1/projects/members/456"


class TestPreConfiguredBuilders:
    """Tests for pre-configured builder instances"""

    def test_documents_urls(self):
        """Test documents_urls builder"""
        assert documents_urls.list() == "/api/v1/documents/list"
        assert documents_urls.detail(123) == "/api/v1/documents/123"
        assert documents_urls.path("conceptplans") == "/api/v1/documents/conceptplans"
        assert (
            documents_urls.path("conceptplans", 123)
            == "/api/v1/documents/conceptplans/123"
        )

    def test_projects_urls(self):
        """Test projects_urls builder"""
        assert projects_urls.list() == "/api/v1/projects/list"
        assert projects_urls.detail(456) == "/api/v1/projects/456"
        assert projects_urls.path("export") == "/api/v1/projects/export"
        assert projects_urls.path("members", 789) == "/api/v1/projects/members/789"

    def test_users_urls(self):
        """Test users_urls builder"""
        assert users_urls.list() == "/api/v1/users/list"
        assert users_urls.detail(111) == "/api/v1/users/111"
        assert users_urls.path("log-in") == "/api/v1/users/log-in"
        assert users_urls.path("log-out") == "/api/v1/users/log-out"


class TestRealWorldUsage:
    """Tests simulating real-world usage patterns"""

    def test_crud_operations(self):
        """Test typical CRUD operation URLs"""
        # List
        assert documents_urls.list() == "/api/v1/documents/list"

        # Create (same as list)
        assert documents_urls.list() == "/api/v1/documents/list"

        # Read
        assert documents_urls.detail(123) == "/api/v1/documents/123"

        # Update (same as read)
        assert documents_urls.detail(123) == "/api/v1/documents/123"

        # Delete (same as read)
        assert documents_urls.detail(123) == "/api/v1/documents/123"

    def test_nested_resources(self):
        """Test nested resource URLs"""
        # Project members
        assert projects_urls.path("members") == "/api/v1/projects/members"
        assert projects_urls.path(123, "members") == "/api/v1/projects/123/members"
        assert (
            projects_urls.path(123, "members", 456)
            == "/api/v1/projects/123/members/456"
        )

        # Document reports
        assert documents_urls.path("reports") == "/api/v1/documents/reports"
        assert documents_urls.path("reports", 789) == "/api/v1/documents/reports/789"
        assert (
            documents_urls.path("reports", 789, "generate_pdf")
            == "/api/v1/documents/reports/789/generate_pdf"
        )

    def test_action_endpoints(self):
        """Test action endpoint URLs"""
        # Authentication
        assert users_urls.path("log-in") == "/api/v1/users/log-in"
        assert users_urls.path("log-out") == "/api/v1/users/log-out"

        # Document actions
        assert documents_urls.path("batchapprove") == "/api/v1/documents/batchapprove"
        assert (
            documents_urls.path("actions", "approve")
            == "/api/v1/documents/actions/approve"
        )

        # Project actions
        assert projects_urls.path("export") == "/api/v1/projects/export"
        assert projects_urls.path("search") == "/api/v1/projects/search"
