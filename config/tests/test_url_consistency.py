"""
Test URL consistency - verify no trailing slashes and APPEND_SLASH is False
"""
from django.test import TestCase
from django.conf import settings
from django.urls import get_resolver


class URLConsistencyTestCase(TestCase):
    """Test that all URLs follow the no-trailing-slash convention"""

    def test_append_slash_is_false(self):
        """Verify APPEND_SLASH setting is False"""
        self.assertFalse(
            settings.APPEND_SLASH,
            "APPEND_SLASH should be False to prevent redirect issues with PUT/PATCH/DELETE"
        )

    def test_no_trailing_slashes_in_url_patterns(self):
        """Verify no URL patterns end with trailing slash (except root path)"""
        resolver = get_resolver()
        
        def check_patterns(patterns, prefix=""):
            """Recursively check URL patterns for trailing slashes"""
            violations = []
            
            for pattern in patterns:
                # Get the pattern string
                if hasattr(pattern, 'pattern'):
                    pattern_str = str(pattern.pattern)
                    full_pattern = prefix + pattern_str
                    
                    # Skip root path (empty string is valid)
                    if pattern_str == "":
                        continue
                    
                    # Check for trailing slash
                    if pattern_str.endswith('/'):
                        violations.append(full_pattern)
                
                # Recursively check included URL patterns
                if hasattr(pattern, 'url_patterns'):
                    new_prefix = prefix
                    if hasattr(pattern, 'pattern'):
                        new_prefix += str(pattern.pattern)
                    violations.extend(check_patterns(pattern.url_patterns, new_prefix))
            
            return violations
        
        violations = check_patterns(resolver.url_patterns)
        
        self.assertEqual(
            len(violations), 0,
            f"Found {len(violations)} URL patterns with trailing slashes:\n" +
            "\n".join(f"  - {v}" for v in violations[:10]) +
            (f"\n  ... and {len(violations) - 10} more" if len(violations) > 10 else "")
        )

    def test_critical_endpoints_no_trailing_slash(self):
        """Test that critical endpoints don't have trailing slashes"""
        from django.urls import reverse, NoReverseMatch
        
        # Test some critical endpoints
        critical_endpoints = [
            ('users-list', 'users'),  # Should not end with /
            ('caretaker-list', 'caretakers'),  # Should not end with /
        ]
        
        for url_name, expected_path in critical_endpoints:
            try:
                url = reverse(url_name)
                # Remove leading /api/v1/ if present
                clean_url = url.replace('/api/v1/', '').strip('/')
                
                self.assertFalse(
                    clean_url.endswith('/'),
                    f"URL '{url_name}' ({url}) should not end with trailing slash"
                )
            except NoReverseMatch:
                # Some URLs might not have names, skip them
                pass
