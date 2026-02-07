"""
Test helper utilities for DRY test writing.

Provides utilities to reduce repetition in view tests.
"""


def api_url(app_name: str, path: str = "", versioned: bool = True) -> str:
    """
    Construct API URL with optional versioning prefix.

    Args:
        app_name: Name of the app (e.g., 'documents', 'projects', 'users')
        path: Optional path after the app name (e.g., 'conceptplans', 'reports/download')
        versioned: Whether to include /api/v1/ prefix (default: True)

    Returns:
        Full URL with optional /api/v1/ prefix and NO trailing slash

    Examples:
        >>> api_url('documents')
        '/api/v1/documents/list'

        >>> api_url('documents', 'conceptplans')
        '/api/v1/documents/conceptplans'

        >>> api_url('admin', versioned=False)
        '/admin'

        >>> api_url('health', versioned=False)
        '/health'
    """
    if versioned:
        base = f"/api/v1/{app_name}"
    else:
        base = f"/{app_name}"

    if not path:
        return f"{base}/list"

    # Remove leading/trailing slashes from path
    path = path.strip("/")

    # Build URL - NO trailing slash
    url = f"{base}/{path}"

    return url


def url(path: str) -> str:
    """
    Construct a simple URL (for non-API endpoints like /admin, /health).

    Args:
        path: URL path (e.g., 'admin', 'health', 'files/test.pdf')

    Returns:
        Full URL with leading slash and NO trailing slash

    Examples:
        >>> url('admin')
        '/admin'

        >>> url('health')
        '/health'

        >>> url('files/test.pdf')
        '/files/test.pdf'
    """
    # Remove leading slash if present
    path = path.lstrip("/")

    # Remove trailing slash if present
    path = path.rstrip("/")

    return f"/{path}"


class APIUrlBuilder:
    """
    Builder class for constructing API URLs with optional versioning.

    Provides a more object-oriented approach to URL construction.
    Supports both versioned API URLs (/api/v1/...) and non-versioned URLs.

    Example:
        >>> urls = APIUrlBuilder('documents')
        >>> urls.list()
        '/api/v1/documents/list'

        >>> urls.detail(123)
        '/api/v1/documents/123'

        >>> urls.path('conceptplans')
        '/api/v1/documents/conceptplans'

        >>> urls.path('conceptplans', 123)
        '/api/v1/documents/conceptplans/123'

        >>> # Non-versioned URLs
        >>> admin_urls = APIUrlBuilder('admin', versioned=False)
        >>> admin_urls.list()
        '/admin/list'
    """

    def __init__(self, app_name: str, versioned: bool = True):
        """
        Initialize URL builder for an app.

        Args:
            app_name: Name of the app (e.g., 'documents', 'projects', 'admin')
            versioned: Whether to include /api/v1/ prefix (default: True)
        """
        self.app_name = app_name
        self.versioned = versioned

        if versioned:
            self.base = f"/api/v1/{app_name}"
        else:
            self.base = f"/{app_name}"

    def list(self) -> str:
        """Get list endpoint URL."""
        return f"{self.base}/list"

    def detail(self, pk: int) -> str:
        """Get detail endpoint URL."""
        return f"{self.base}/{pk}"

    def path(self, *parts) -> str:
        """
        Construct URL with custom path parts.

        Args:
            *parts: Path parts to join (strings or integers)

        Returns:
            Full URL with path parts joined and NO trailing slash

        Examples:
            >>> urls = APIUrlBuilder('documents')
            >>> urls.path('conceptplans')
            '/api/v1/documents/conceptplans'

            >>> urls.path('conceptplans', 123)
            '/api/v1/documents/conceptplans/123'

            >>> urls.path('reports', 'download')
            '/api/v1/documents/reports/download'

            >>> # Non-versioned URLs
            >>> files_urls = APIUrlBuilder('files', versioned=False)
            >>> files_urls.path('test.pdf')
            '/files/test.pdf'
        """
        path_str = "/".join(str(part) for part in parts)
        return f"{self.base}/{path_str}"


# Convenience instances for common apps
adminoptions_urls = APIUrlBuilder("adminoptions")
agencies_urls = APIUrlBuilder("agencies")
caretakers_urls = APIUrlBuilder("caretakers")
categories_urls = APIUrlBuilder("categories")
communications_urls = APIUrlBuilder("communications")
contacts_urls = APIUrlBuilder("contacts")
documents_urls = APIUrlBuilder("documents")
locations_urls = APIUrlBuilder("locations")
medias_urls = APIUrlBuilder("medias")
projects_urls = APIUrlBuilder("projects")
quotes_urls = APIUrlBuilder("quotes")
users_urls = APIUrlBuilder("users")
