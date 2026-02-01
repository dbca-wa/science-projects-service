"""
User profile views
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
)
from rest_framework.exceptions import NotFound
from django.conf import settings

from users.models import UserWork
from projects.models import ProjectMember
from users.services import ProfileService
from users.serializers import (
    UserProfileSerializer,
    ProfilePageSerializer,
    UpdatePISerializer,
    UpdateProfileSerializer,
    UpdateMembershipSerializer,
    UserWorkSerializer,
    TinyUserWorkSerializer,
)
from projects.serializers import ProjectDataTableSerializer



class UserProfiles(APIView):
    """List user profiles"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        filters = {}
        if 'user' in request.query_params:
            filters['user'] = request.query_params['user']
        
        profiles = ProfileService.list_user_profiles(filters=filters)
        serializer = UserProfileSerializer(profiles, many=True)
        return Response(serializer.data)


class UserProfileDetail(APIView):
    """Get and update user profile"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Get user profile"""
        profile = ProfileService.get_user_profile(pk)
        serializer = ProfilePageSerializer(profile)
        return Response(serializer.data)

    def put(self, request, pk):
        """Update user profile"""
        serializer = UserProfileSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        profile = ProfileService.update_user_profile(pk, serializer.validated_data)
        result = ProfilePageSerializer(profile)
        return Response(result.data, status=HTTP_202_ACCEPTED)


class UpdatePersonalInformation(APIView):
    """Update user personal information"""
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = UpdatePISerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        user = ProfileService.update_personal_information(
            request.user.id,
            serializer.validated_data
        )
        result = UpdatePISerializer(user)
        return Response(result.data, status=HTTP_202_ACCEPTED)


class UpdateProfile(APIView):
    """Update user profile"""
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = UpdateProfileSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        profile = ProfileService.update_user_profile(
            request.user.profile.id,
            serializer.validated_data
        )
        result = UpdateProfileSerializer(profile)
        return Response(result.data, status=HTTP_202_ACCEPTED)


class UpdateMembership(APIView):
    """Update user work/membership"""
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = UpdateMembershipSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        # Update user work
        if hasattr(request.user, 'work') and request.user.work:
            work = request.user.work
            for field, value in serializer.validated_data.items():
                setattr(work, field, value)
            work.save()
            result = UpdateMembershipSerializer(work)
            return Response(result.data, status=HTTP_202_ACCEPTED)
        
        return Response({"error": "No work record found"}, status=404)


class RemoveAvatar(APIView):
    """Remove user avatar"""
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        try:
            if hasattr(request.user, 'avatar') and request.user.avatar:
                request.user.avatar.delete()
                return Response({"ok": "Avatar removed"}, status=HTTP_204_NO_CONTENT)
            return Response({"error": "No avatar found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=400)


class UserWorks(APIView):
    """List and create user works"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all user works"""
        all_works = UserWork.objects.all()
        serializer = TinyUserWorkSerializer(all_works, many=True, context={"request": request})
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        """Create user work"""
        settings.LOGGER.info(msg=f"{request.user} is creating user work")
        serializer = UserWorkSerializer(data=request.data)
        if not serializer.is_valid():
            settings.LOGGER.error(msg=f"{serializer.errors}")
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        work = serializer.save()
        result = TinyUserWorkSerializer(work)
        return Response(result.data, status=HTTP_201_CREATED)


class UserWorkDetail(APIView):
    """Get, update, and delete user work"""
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        """Get user work by ID"""
        try:
            return UserWork.objects.get(pk=pk)
        except UserWork.DoesNotExist:
            raise NotFound

    def get(self, request, pk):
        """Get user work detail"""
        work = self.get_object(pk)
        serializer = UserWorkSerializer(work, context={"request": request})
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, pk):
        """Update user work"""
        work = self.get_object(pk)
        settings.LOGGER.info(msg=f"{request.user} is updating work of {work}")
        serializer = UserWorkSerializer(work, data=request.data, partial=True)
        if not serializer.is_valid():
            settings.LOGGER.error(msg=f"{serializer.errors}")
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        updated_work = serializer.save()
        result = TinyUserWorkSerializer(updated_work)
        return Response(result.data, status=HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        """Delete user work"""
        work = self.get_object(pk)
        settings.LOGGER.info(msg=f"{request.user} is deleting work {work}")
        work.delete()
        return Response(status=HTTP_204_NO_CONTENT)


class UsersProjects(APIView):
    """Get user's projects"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, pk):
        """Get all projects for a user"""
        try:
            users_memberships = ProjectMember.objects.filter(user=pk).select_related(
                "project",
                "project__business_area",
                "project__image",
                "user",
            )
        except ProjectMember.DoesNotExist:
            raise NotFound

        if len(users_memberships) > 0:
            user_obj = users_memberships[0].user
            settings.LOGGER.info(
                msg=f"{request.user} is viewing {user_obj} and their projects"
            )
        else:
            settings.LOGGER.info(
                msg=f"{request.user} is viewing user with pk {pk} and their projects (none)"
            )

        projects_with_roles = [
            (membership.project, membership.role) for membership in users_memberships
        ]

        serialized_projects = ProjectDataTableSerializer(
            [proj for proj, _ in projects_with_roles],
            many=True,
            context={"request": request},
        )

        return Response(serialized_projects.data, status=HTTP_200_OK)
