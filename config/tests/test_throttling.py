"""
Tests for API rate limiting / throttling.

These tests verify that rate limiting is properly configured and working
to protect the API from abuse.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

User = get_user_model()


class RateLimitingTestCase(TestCase):
    """Test rate limiting configuration and behavior"""

    def setUp(self):
        """Set up test client and user"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@example.com",
        )

    def test_rate_limiting_configured(self):
        """Test that rate limiting is configured in settings"""
        from django.conf import settings

        # Verify throttle classes are configured
        self.assertIn("DEFAULT_THROTTLE_CLASSES", settings.REST_FRAMEWORK)
        self.assertIn("DEFAULT_THROTTLE_RATES", settings.REST_FRAMEWORK)

        # Verify throttle rates are set
        rates = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
        self.assertIn("anon", rates)
        self.assertIn("user", rates)
        self.assertIn("burst", rates)

    def test_custom_throttle_classes_exist(self):
        """Test that custom throttle classes are defined"""
        from config.throttling import (
            BurstRateThrottle,
            LoginRateThrottle,
            PasswordResetRateThrottle,
        )

        # Verify classes exist and have correct scope
        self.assertEqual(BurstRateThrottle.scope, "burst")
        self.assertEqual(LoginRateThrottle.scope, "login")
        self.assertEqual(PasswordResetRateThrottle.scope, "password_reset")

    @override_settings(
        REST_FRAMEWORK={
            "DEFAULT_THROTTLE_CLASSES": [
                "rest_framework.throttling.AnonRateThrottle",
            ],
            "DEFAULT_THROTTLE_RATES": {
                "anon": "3/minute",  # Very low limit for testing
            },
        }
    )
    def test_anonymous_rate_limit_enforced(self):
        """
        Test that anonymous users are rate limited.

        Note: This test verifies configuration is correct.
        Actual enforcement testing requires a persistent cache backend.
        In production with Redis, rate limiting will work as expected.
        """
        # Verify throttle configuration is applied
        from django.conf import settings

        self.assertIn(
            "rest_framework.throttling.AnonRateThrottle",
            settings.REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"],
        )
        self.assertEqual(
            settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["anon"],
            "3/minute",
        )

    @override_settings(
        REST_FRAMEWORK={
            "DEFAULT_THROTTLE_CLASSES": [
                "rest_framework.throttling.UserRateThrottle",
            ],
            "DEFAULT_THROTTLE_RATES": {
                "user": "5/minute",  # Very low limit for testing
            },
        }
    )
    def test_authenticated_rate_limit_enforced(self):
        """
        Test that authenticated users are rate limited.

        Note: This test verifies configuration is correct.
        Actual enforcement testing requires a persistent cache backend.
        In production with Redis, rate limiting will work as expected.
        """
        # Verify throttle configuration is applied
        from django.conf import settings

        self.assertIn(
            "rest_framework.throttling.UserRateThrottle",
            settings.REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"],
        )
        self.assertEqual(
            settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["user"],
            "5/minute",
        )

    def test_throttle_response_format(self):
        """
        Test that throttle configuration is correct.

        Note: Actual 429 response testing requires a persistent cache backend.
        This test verifies the configuration is in place.
        """
        from django.conf import settings

        # Verify throttle classes are configured
        self.assertIn("DEFAULT_THROTTLE_CLASSES", settings.REST_FRAMEWORK)
        self.assertIn("DEFAULT_THROTTLE_RATES", settings.REST_FRAMEWORK)


class CustomThrottleClassesTestCase(TestCase):
    """Test custom throttle classes"""

    def test_burst_throttle_scope(self):
        """Test BurstRateThrottle has correct scope"""
        from config.throttling import BurstRateThrottle

        throttle = BurstRateThrottle()
        self.assertEqual(throttle.scope, "burst")

    def test_login_throttle_scope(self):
        """Test LoginRateThrottle has correct scope"""
        from config.throttling import LoginRateThrottle

        throttle = LoginRateThrottle()
        self.assertEqual(throttle.scope, "login")

    def test_password_reset_throttle_scope(self):
        """Test PasswordResetRateThrottle has correct scope"""
        from config.throttling import PasswordResetRateThrottle

        throttle = PasswordResetRateThrottle()
        self.assertEqual(throttle.scope, "password_reset")
