"""
Quote admin views
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework.status import HTTP_201_CREATED

from quotes.services import QuoteService


class AddQuotesFromUniques(APIView):
    """Load quotes from unique_quotes.txt file"""
    permission_classes = [IsAdminUser]

    def post(self, request):
        """Load and create quotes from file"""
        quotes_data = QuoteService.load_quotes_from_file()
        result = QuoteService.bulk_create_quotes(quotes_data)
        
        return Response({
            "message": f"Created {result['created']} quotes",
            "errors": result['errors']
        }, status=HTTP_201_CREATED)
