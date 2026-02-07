"""
Quote service - Business logic for quote operations
"""

import os

from django.conf import settings
from rest_framework.exceptions import NotFound

from quotes.models import Quote


class QuoteService:
    """Business logic for quote operations"""

    @staticmethod
    def list_quotes():
        """List all quotes"""
        return Quote.objects.all()

    @staticmethod
    def get_quote(pk):
        """Get quote by ID"""
        try:
            return Quote.objects.get(pk=pk)
        except Quote.DoesNotExist:
            raise NotFound(f"Quote {pk} not found")

    @staticmethod
    def get_random_quote():
        """Get random quote"""
        return Quote.objects.order_by("?").first()

    @staticmethod
    def create_quote(data):
        """Create new quote"""
        settings.LOGGER.info(msg="Creating quote")
        return Quote.objects.create(**data)

    @staticmethod
    def update_quote(pk, data):
        """Update quote"""
        quote = QuoteService.get_quote(pk)
        settings.LOGGER.info(msg=f"Updating quote: {quote}")

        for field, value in data.items():
            setattr(quote, field, value)
        quote.save()

        return quote

    @staticmethod
    def delete_quote(pk):
        """Delete quote"""
        quote = QuoteService.get_quote(pk)
        settings.LOGGER.info(msg=f"Deleting quote: {quote}")
        quote.delete()

    @staticmethod
    def load_quotes_from_file():
        """Load quotes from unique_quotes.txt file"""
        settings.LOGGER.info(msg="Loading quotes from file")

        file_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "../unique_quotes.txt"
        )

        with open(file_path) as quotesfile:
            processed_quotes = []
            duplicates = []
            unique_quotes = []

            array_of_raw_quotes = quotesfile.readlines()

            # Remove duplicates
            for line in array_of_raw_quotes:
                line = line.strip().lower()
                if line not in processed_quotes:
                    processed_quotes.append(line)
                else:
                    duplicates.append(line)

            # Parse quotes
            for p1 in processed_quotes:
                line_array = p1.split(" - ")
                check = len(line_array)

                if check <= 2:
                    quote = line_array[0]
                    author = line_array[1] if len(line_array) > 1 else ""
                else:
                    quote_array = line_array[:-1]
                    quote = " - ".join(item for item in quote_array).strip()
                    author = line_array[-1]

                unique_quotes.append({"text": quote, "author": author})

            return unique_quotes

    @staticmethod
    def bulk_create_quotes(quotes_data):
        """Bulk create quotes from list of dicts"""
        created_count = 0
        errors = []

        for quote_data in quotes_data:
            try:
                Quote.objects.create(**quote_data)
                created_count += 1
            except Exception as e:
                errors.append(str(e))
                settings.LOGGER.error(msg=f"Error creating quote: {e}")

        return {"created": created_count, "errors": errors}
