"""
Tests for quotes admin
"""
import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model

from quotes.admin import QuoteAdmin, generate_quotes, export_selected_quotes_txt, export_all_quotes_txt
from quotes.models import Quote

User = get_user_model()


@pytest.fixture
def admin_site():
    """Provide admin site"""
    return AdminSite()


@pytest.fixture
def quote_admin(admin_site):
    """Provide QuoteAdmin instance"""
    return QuoteAdmin(Quote, admin_site)


@pytest.fixture
def superuser(db):
    """Provide a superuser"""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin123'
    )


class TestQuoteAdmin:
    """Tests for QuoteAdmin configuration"""

    def test_list_display(self, quote_admin):
        """Test list_display configuration"""
        assert 'text' in quote_admin.list_display
        assert 'author' in quote_admin.list_display
        assert 'created_at' in quote_admin.list_display
        assert 'updated_at' in quote_admin.list_display

    def test_list_filter(self, quote_admin):
        """Test list_filter configuration"""
        assert 'author' in quote_admin.list_filter

    def test_search_fields(self, quote_admin):
        """Test search_fields configuration"""
        assert 'text' in quote_admin.search_fields
        assert 'author' in quote_admin.search_fields

    def test_actions(self, quote_admin):
        """Test admin actions are registered"""
        action_names = [action.__name__ for action in quote_admin.actions]
        assert 'generate_quotes' in action_names
        assert 'export_selected_quotes_txt' in action_names
        assert 'export_all_quotes_txt' in action_names


class TestAdminActions:
    """Tests for admin actions"""

    def test_export_selected_quotes_txt(self, quote_admin, superuser, quote, quote2, db):
        """Test exporting selected quotes to txt"""
        # Arrange
        request = type('Request', (), {'user': superuser})()
        queryset = Quote.objects.filter(id__in=[quote.id, quote2.id])
        
        # Act - should not raise
        export_selected_quotes_txt(quote_admin, request, queryset)
        
        # Assert - action completes without error
        # (actual file creation is tested manually as it uses tempfile)

    def test_export_all_quotes_txt(self, quote_admin, superuser, quote, quote2, db):
        """Test exporting all quotes to txt"""
        # Arrange
        request = type('Request', (), {'user': superuser})()
        queryset = Quote.objects.filter(id=quote.id)  # Select only one
        
        # Act - should not raise
        export_all_quotes_txt(quote_admin, request, queryset)
        
        # Assert - action completes without error
        # (actual file creation is tested manually as it uses tempfile)

    def test_export_all_quotes_txt_multiple_selected(self, quote_admin, superuser, quote, quote2, db, capsys):
        """Test export all quotes with multiple selected shows error"""
        # Arrange
        request = type('Request', (), {'user': superuser})()
        queryset = Quote.objects.filter(id__in=[quote.id, quote2.id])
        
        # Act
        export_all_quotes_txt(quote_admin, request, queryset)
        
        # Assert - should print error message
        captured = capsys.readouterr()
        assert "PLEASE SELECT ONLY ONE" in captured.out
