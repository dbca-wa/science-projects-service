"""
Tests for quote services
"""

from unittest.mock import mock_open, patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound

from quotes.models import Quote
from quotes.services.quote_service import QuoteService

User = get_user_model()


class TestQuoteService:
    """Tests for Quote service operations"""

    def test_list_quotes(self, quote, quote2, db):
        """Test listing all quotes"""
        # Act
        quotes = QuoteService.list_quotes()

        # Assert
        assert quotes.count() == 2
        assert quote in quotes
        assert quote2 in quotes

    def test_list_quotes_empty(self, db):
        """Test listing quotes when none exist"""
        # Act
        quotes = QuoteService.list_quotes()

        # Assert
        assert quotes.count() == 0

    def test_get_quote(self, quote, db):
        """Test getting quote by ID"""
        # Act
        result = QuoteService.get_quote(quote.id)

        # Assert
        assert result.id == quote.id
        assert result.text == "Test quote text"
        assert result.author == "Test Author"

    def test_get_quote_not_found(self, db):
        """Test getting non-existent quote raises NotFound"""
        # Act & Assert
        with pytest.raises(NotFound, match="Quote 999 not found"):
            QuoteService.get_quote(999)

    def test_get_random_quote(self, quote, quote2, db):
        """Test getting random quote"""
        # Act
        result = QuoteService.get_random_quote()

        # Assert
        assert result is not None
        assert result in [quote, quote2]

    def test_get_random_quote_empty(self, db):
        """Test getting random quote when none exist"""
        # Act
        result = QuoteService.get_random_quote()

        # Assert
        assert result is None

    def test_create_quote(self, db):
        """Test creating a quote"""
        # Arrange
        data = {
            "text": "New quote text",
            "author": "New Author",
        }

        # Act
        quote = QuoteService.create_quote(data)

        # Assert
        assert quote.id is not None
        assert quote.text == "New quote text"
        assert quote.author == "New Author"

    def test_create_quote_duplicate_text(self, quote, db):
        """Test creating quote with duplicate text fails"""
        # Arrange
        data = {
            "text": "Test quote text",  # Same as existing quote
            "author": "Different Author",
        }

        # Act & Assert
        with pytest.raises(Exception):  # IntegrityError
            QuoteService.create_quote(data)

    def test_update_quote(self, quote, db):
        """Test updating a quote"""
        # Arrange
        data = {"text": "Updated quote text"}

        # Act
        updated = QuoteService.update_quote(quote.id, data)

        # Assert
        assert updated.id == quote.id
        assert updated.text == "Updated quote text"
        assert updated.author == "Test Author"  # Unchanged

    def test_update_quote_author(self, quote, db):
        """Test updating quote author"""
        # Arrange
        data = {"author": "Updated Author"}

        # Act
        updated = QuoteService.update_quote(quote.id, data)

        # Assert
        assert updated.id == quote.id
        assert updated.author == "Updated Author"
        assert updated.text == "Test quote text"  # Unchanged

    def test_update_quote_not_found(self, db):
        """Test updating non-existent quote raises NotFound"""
        # Arrange
        data = {"text": "Updated text"}

        # Act & Assert
        with pytest.raises(NotFound, match="Quote 999 not found"):
            QuoteService.update_quote(999, data)

    def test_delete_quote(self, quote, db):
        """Test deleting a quote"""
        # Arrange
        quote_id = quote.id

        # Act
        QuoteService.delete_quote(quote_id)

        # Assert
        assert not Quote.objects.filter(id=quote_id).exists()

    def test_delete_quote_not_found(self, db):
        """Test deleting non-existent quote raises NotFound"""
        # Act & Assert
        with pytest.raises(NotFound, match="Quote 999 not found"):
            QuoteService.delete_quote(999)


class TestQuoteFileOperations:
    """Tests for Quote file operations"""

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="Quote 1 - Author 1\nQuote 2 - Author 2\n",
    )
    def test_load_quotes_from_file(self, mock_file, db):
        """Test loading quotes from file"""
        # Act
        quotes = QuoteService.load_quotes_from_file()

        # Assert
        assert len(quotes) == 2
        assert quotes[0] == {"text": "quote 1", "author": "author 1"}
        assert quotes[1] == {"text": "quote 2", "author": "author 2"}

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="Quote 1 - Author 1\nQuote 1 - Author 1\n",
    )
    def test_load_quotes_removes_duplicates(self, mock_file, db):
        """Test loading quotes removes duplicates"""
        # Act
        quotes = QuoteService.load_quotes_from_file()

        # Assert
        assert len(quotes) == 1
        assert quotes[0] == {"text": "quote 1", "author": "author 1"}

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="Quote with - multiple - dashes - Author\n",
    )
    def test_load_quotes_handles_multiple_dashes(self, mock_file, db):
        """Test loading quotes handles multiple dashes correctly"""
        # Act
        quotes = QuoteService.load_quotes_from_file()

        # Assert
        assert len(quotes) == 1
        assert quotes[0] == {
            "text": "quote with - multiple - dashes",
            "author": "author",
        }

    @patch("builtins.open", new_callable=mock_open, read_data="Quote without author\n")
    def test_load_quotes_handles_missing_author(self, mock_file, db):
        """Test loading quotes handles missing author"""
        # Act
        quotes = QuoteService.load_quotes_from_file()

        # Assert
        assert len(quotes) == 1
        assert quotes[0] == {"text": "quote without author", "author": ""}

    def test_bulk_create_quotes(self, db):
        """Test bulk creating quotes"""
        # Arrange
        quotes_data = [
            {"text": "Quote 1", "author": "Author 1"},
            {"text": "Quote 2", "author": "Author 2"},
            {"text": "Quote 3", "author": "Author 3"},
        ]

        # Act
        result = QuoteService.bulk_create_quotes(quotes_data)

        # Assert
        assert result["created"] == 3
        assert len(result["errors"]) == 0
        assert Quote.objects.count() == 3

    def test_bulk_create_quotes_empty_list(self, db):
        """Test bulk creating quotes with empty list"""
        # Arrange
        quotes_data = []

        # Act
        result = QuoteService.bulk_create_quotes(quotes_data)

        # Assert
        assert result["created"] == 0
        assert len(result["errors"]) == 0
        assert Quote.objects.count() == 0


class TestQuoteModelValidation:
    """Tests for Quote model validation"""

    def test_quote_text_unique(self, quote, db):
        """Test quote text must be unique"""
        # Act & Assert
        with pytest.raises(Exception):  # IntegrityError
            Quote.objects.create(
                text="Test quote text",  # Same as existing
                author="Different Author",
            )

    def test_quote_str_representation(self, quote, db):
        """Test quote string representation"""
        # Act
        str_repr = str(quote)

        # Assert
        assert str(quote.pk) in str_repr
        assert "Test quote text" in str_repr
