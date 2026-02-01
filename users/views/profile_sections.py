"""
Staff profile section views
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from users.services import ProfileService
from users.serializers import (
    StaffProfileHeroSerializer,
    StaffProfileOverviewSerializer,
    StaffProfileCVSerializer,
)


class StaffProfileHeroDetail(APIView):
    """Get staff profile hero section"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, pk):
        profile = ProfileService.get_staff_profile(pk)
        serializer = StaffProfileHeroSerializer(profile)
        return Response(serializer.data)


class StaffProfileOverviewDetail(APIView):
    """Get staff profile overview section"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, pk):
        profile = ProfileService.get_staff_profile(pk)
        serializer = StaffProfileOverviewSerializer(profile)
        return Response(serializer.data)


class StaffProfileCVDetail(APIView):
    """Get staff profile CV section"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, pk):
        profile = ProfileService.get_staff_profile(pk)
        serializer = StaffProfileCVSerializer(profile)
        return Response(serializer.data)
