"""
Profile entry views (employment and education)
"""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
)
from rest_framework.views import APIView

from users.serializers import (
    EducationEntryCreationSerializer,
    EducationEntrySerializer,
    EmploymentEntryCreationSerializer,
    EmploymentEntrySerializer,
)
from users.services import EducationService, EmploymentService


class StaffProfileEmploymentEntries(APIView):
    """List and create employment entries"""

    permission_classes = [IsAuthenticated]

    def get(self, request, profile_id):
        """List employment entries"""
        entries = EmploymentService.list_employment(profile_id)
        serializer = EmploymentEntrySerializer(entries, many=True)
        return Response(serializer.data)

    def post(self, request, profile_id):
        """Create employment entry"""
        serializer = EmploymentEntryCreationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

        entry = EmploymentService.create_employment(
            profile_id, serializer.validated_data
        )
        result = EmploymentEntrySerializer(entry)
        return Response(result.data, status=HTTP_201_CREATED)


class StaffProfileEmploymentEntryDetail(APIView):
    """Get, update, and delete employment entry"""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Get employment entry"""
        entry = EmploymentService.get_employment(pk)
        serializer = EmploymentEntrySerializer(entry)
        return Response(serializer.data)

    def put(self, request, pk):
        """Update employment entry"""
        serializer = EmploymentEntrySerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

        entry = EmploymentService.update_employment(pk, serializer.validated_data)
        result = EmploymentEntrySerializer(entry)
        return Response(result.data, status=HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        """Delete employment entry"""
        EmploymentService.delete_employment(pk)
        return Response(status=HTTP_204_NO_CONTENT)


class StaffProfileEducationEntries(APIView):
    """List and create education entries"""

    permission_classes = [IsAuthenticated]

    def get(self, request, profile_id):
        """List education entries"""
        entries = EducationService.list_education(profile_id)
        serializer = EducationEntrySerializer(entries, many=True)
        return Response(serializer.data)

    def post(self, request, profile_id):
        """Create education entry"""
        serializer = EducationEntryCreationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

        entry = EducationService.create_education(profile_id, serializer.validated_data)
        result = EducationEntrySerializer(entry)
        return Response(result.data, status=HTTP_201_CREATED)


class StaffProfileEducationEntryDetail(APIView):
    """Get, update, and delete education entry"""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Get education entry"""
        entry = EducationService.get_education(pk)
        serializer = EducationEntrySerializer(entry)
        return Response(serializer.data)

    def put(self, request, pk):
        """Update education entry"""
        serializer = EducationEntrySerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

        entry = EducationService.update_education(pk, serializer.validated_data)
        result = EducationEntrySerializer(entry)
        return Response(result.data, status=HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        """Delete education entry"""
        EducationService.delete_education(pk)
        return Response(status=HTTP_204_NO_CONTENT)


class UserStaffEmploymentEntries(APIView):
    """List user's employment entries"""

    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        from users.services import ProfileService

        profile = ProfileService.get_staff_profile_by_user(user_id)
        if not profile:
            return Response({"error": "No staff profile found"}, status=404)

        entries = EmploymentService.list_employment(profile.id)
        serializer = EmploymentEntrySerializer(entries, many=True)
        return Response(serializer.data)


class UserStaffEducationEntries(APIView):
    """List user's education entries"""

    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        from users.services import ProfileService

        profile = ProfileService.get_staff_profile_by_user(user_id)
        if not profile:
            return Response({"error": "No staff profile found"}, status=404)

        entries = EducationService.list_education(profile.id)
        serializer = EducationEntrySerializer(entries, many=True)
        return Response(serializer.data)
