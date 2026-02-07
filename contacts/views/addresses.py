"""
Address views
"""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
)
from rest_framework.views import APIView

from contacts.serializers import AddressSerializer, TinyAddressSerializer
from contacts.services import ContactService


class Addresses(APIView):
    """List and create addresses"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all addresses"""
        addresses = ContactService.list_addresses()
        serializer = TinyAddressSerializer(addresses, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        """Create new address"""
        serializer = AddressSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

        address = ContactService.create_address(request.user, serializer.validated_data)
        result = TinyAddressSerializer(address)
        return Response(result.data, status=HTTP_201_CREATED)


class AddressDetail(APIView):
    """Get, update, and delete address"""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Get address detail"""
        address = ContactService.get_address(pk)
        serializer = AddressSerializer(address)
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, pk):
        """Update address"""
        serializer = AddressSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

        address = ContactService.update_address(
            pk, request.user, serializer.validated_data
        )
        result = TinyAddressSerializer(address)
        return Response(result.data, status=HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        """Delete address"""
        ContactService.delete_address(pk, request.user)
        return Response(status=HTTP_204_NO_CONTENT)
