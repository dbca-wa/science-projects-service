"""
Quote CRUD views
"""

from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
)
from rest_framework.views import APIView

from common.utils import paginate_queryset
from quotes.serializers import QuoteDetailSerializer, QuoteListSerializer
from quotes.services import QuoteService


class Quotes(APIView):
    """List and create quotes"""

    def get(self, request):
        """List quotes with pagination"""
        quotes = QuoteService.list_quotes()
        paginated = paginate_queryset(quotes, request)

        serializer = QuoteListSerializer(paginated["items"], many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        """Create new quote"""
        if not request.user.is_authenticated:
            return Response(
                {"error": "Authentication required"}, status=HTTP_400_BAD_REQUEST
            )

        serializer = QuoteListSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

        quote = QuoteService.create_quote(serializer.validated_data)
        result = QuoteListSerializer(quote)
        return Response(result.data, status=HTTP_201_CREATED)


class QuoteDetail(APIView):
    """Get, update, and delete quote"""

    def get(self, request, pk):
        """Get quote detail"""
        quote = QuoteService.get_quote(pk)
        serializer = QuoteDetailSerializer(quote, context={"request": request})
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, pk):
        """Update quote"""
        if not request.user.is_authenticated:
            return Response(
                {"error": "Authentication required"}, status=HTTP_400_BAD_REQUEST
            )

        serializer = QuoteDetailSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

        quote = QuoteService.update_quote(pk, serializer.validated_data)
        result = QuoteDetailSerializer(quote)
        return Response(result.data, status=HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        """Delete quote"""
        if not request.user.is_authenticated:
            return Response(
                {"error": "Authentication required"}, status=HTTP_400_BAD_REQUEST
            )

        QuoteService.delete_quote(pk)
        return Response(status=HTTP_204_NO_CONTENT)


class QuoteRandom(APIView):
    """Get random quote"""

    def get(self, request):
        """Get random quote"""
        quote = QuoteService.get_random_quote()
        serializer = QuoteDetailSerializer(quote, context={"request": request})
        return Response(serializer.data, status=HTTP_200_OK)
