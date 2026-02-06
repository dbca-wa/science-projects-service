"""
Contact views - Agency, Branch, and User contacts
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
)

from contacts.services import ContactService
from contacts.serializers import (
    AgencyContactSerializer,
    AgencyContactCreateSerializer,
    TinyAgencyContactSerializer,
    BranchContactSerializer,
    BranchContactCreateSerializer,
    TinyBranchContactSerializer,
    UserContactSerializer,
    UserContactCreateSerializer,
    TinyUserContactSerializer,
)


class AgencyContacts(APIView):
    """List and create agency contacts"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all agency contacts"""
        contacts = ContactService.list_agency_contacts()
        serializer = TinyAgencyContactSerializer(contacts, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        """Create new agency contact"""
        serializer = AgencyContactCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        contact = ContactService.create_agency_contact(request.user, serializer.validated_data)
        result = AgencyContactSerializer(contact)
        return Response(result.data, status=HTTP_201_CREATED)


class AgencyContactDetail(APIView):
    """Get, update, and delete agency contact"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Get agency contact detail"""
        contact = ContactService.get_agency_contact(pk)
        serializer = AgencyContactSerializer(contact)
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, pk):
        """Update agency contact"""
        contact = ContactService.get_agency_contact(pk)
        serializer = AgencyContactCreateSerializer(contact, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        contact = serializer.save()
        result = AgencyContactSerializer(contact)
        return Response(result.data, status=HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        """Delete agency contact"""
        ContactService.delete_agency_contact(pk, request.user)
        return Response(status=HTTP_204_NO_CONTENT)


class BranchContacts(APIView):
    """List and create branch contacts"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all branch contacts"""
        contacts = ContactService.list_branch_contacts()
        serializer = TinyBranchContactSerializer(contacts, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        """Create new branch contact"""
        serializer = BranchContactCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        contact = ContactService.create_branch_contact(request.user, serializer.validated_data)
        result = BranchContactSerializer(contact)
        return Response(result.data, status=HTTP_201_CREATED)


class BranchContactDetail(APIView):
    """Get, update, and delete branch contact"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Get branch contact detail"""
        contact = ContactService.get_branch_contact(pk)
        serializer = BranchContactSerializer(contact)
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, pk):
        """Update branch contact"""
        contact = ContactService.get_branch_contact(pk)
        serializer = BranchContactCreateSerializer(contact, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        contact = serializer.save()
        result = BranchContactSerializer(contact)
        return Response(result.data, status=HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        """Delete branch contact"""
        ContactService.delete_branch_contact(pk, request.user)
        return Response(status=HTTP_204_NO_CONTENT)


class UserContacts(APIView):
    """List and create user contacts"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all user contacts"""
        contacts = ContactService.list_user_contacts()
        serializer = TinyUserContactSerializer(contacts, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        """Create new user contact"""
        serializer = UserContactCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        contact = ContactService.create_user_contact(request.user, serializer.validated_data)
        result = UserContactSerializer(contact)
        return Response(result.data, status=HTTP_201_CREATED)


class UserContactDetail(APIView):
    """Get, update, and delete user contact"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Get user contact detail"""
        contact = ContactService.get_user_contact(pk)
        serializer = UserContactSerializer(contact)
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, pk):
        """Update user contact"""
        contact = ContactService.get_user_contact(pk)
        serializer = UserContactCreateSerializer(contact, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        contact = serializer.save()
        result = UserContactSerializer(contact)
        return Response(result.data, status=HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        """Delete user contact"""
        ContactService.delete_user_contact(pk, request.user)
        return Response(status=HTTP_204_NO_CONTENT)
