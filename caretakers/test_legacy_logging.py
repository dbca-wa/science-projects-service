"""
Tests for legacy endpoint logging.
"""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class LegacyEndpointLoggingTest(TestCase):
    """Test that legacy endpoints log warnings when called"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.client.force_login(self.user)

    @patch("caretakers.urls_compat.logger")
    def test_legacy_list_endpoint_logs_warning(self, mock_logger):
        """Test that calling legacy list endpoint logs a warning"""
        self.client.get("/api/v1/adminoptions/caretakers/")

        # Check that warning was logged
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]

        # Verify warning message contains expected information
        self.assertIn("⚠️  LEGACY ENDPOINT CALLED", call_args)
        self.assertIn("/api/v1/adminoptions/caretakers/", call_args)
        self.assertIn("GET", call_args)
        self.assertIn("testuser", call_args)
        self.assertIn("Please update to use /api/v1/caretakers/", call_args)

    @patch("caretakers.urls_compat.logger")
    def test_legacy_check_endpoint_logs_warning(self, mock_logger):
        """Test that calling legacy check endpoint logs a warning"""
        self.client.get("/api/v1/adminoptions/caretakers/checkcaretaker")

        # Check that warning was logged
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]

        # Verify warning message
        self.assertIn("⚠️  LEGACY ENDPOINT CALLED", call_args)
        self.assertIn("/api/v1/adminoptions/caretakers/checkcaretaker", call_args)
        self.assertIn("GET", call_args)

    @patch("caretakers.urls_compat.logger")
    def test_legacy_requests_endpoint_logs_warning(self, mock_logger):
        """Test that calling legacy requests endpoint logs a warning"""
        self.client.get("/api/v1/adminoptions/caretakers/requests?user=1")

        # Check that warning was logged
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]

        # Verify warning message
        self.assertIn("⚠️  LEGACY ENDPOINT CALLED", call_args)
        self.assertIn("/api/v1/adminoptions/caretakers/requests", call_args)

    @patch("caretakers.urls_compat.logger")
    def test_new_endpoint_does_not_log_warning(self, mock_logger):
        """Test that calling new endpoint does NOT log a warning"""
        self.client.get("/api/v1/caretakers/")

        # Check that warning was NOT logged
        mock_logger.warning.assert_not_called()
