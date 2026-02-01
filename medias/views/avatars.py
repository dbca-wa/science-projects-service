# region IMPORTS ==================================================================================================
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.exceptions import PermissionDenied
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
)

from ..models import UserAvatar
from ..serializers import UserAvatarSerializer, TinyUserAvatarSerializer
from ..services.media_service import MediaService

# endregion ========================================================================================================


class UserAvatars(APIView):
    """List and create user avatars"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        avatars = MediaService.list_user_avatars()
        serializer = TinyUserAvatarSerializer(
            avatars, many=True, context={"request": request}
        )
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        settings.LOGGER.info(f"{request.user} is posting a user avatar")
        serializer = UserAvatarSerializer(data=request.data)
        
        if serializer.is_valid():
            avatar = serializer.save()
            return Response(
                TinyUserAvatarSerializer(avatar).data,
                status=HTTP_201_CREATED,
            )
        else:
            settings.LOGGER.error(f"{serializer.errors}")
            return Response(serializer.errors, HTTP_400_BAD_REQUEST)


class UserAvatarDetail(APIView):
    """Retrieve, update, and delete user avatar"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, pk):
        avatar = MediaService.get_user_avatar(pk)
        serializer = UserAvatarSerializer(avatar, context={"request": request})
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, pk):
        avatar = MediaService.get_user_avatar(pk)
        settings.LOGGER.info(f"{request.user} is updating user avatar {avatar}")
        
        if not (request.user.is_superuser or request.user == avatar.user):
            settings.LOGGER.warning(
                f"Permission denied as {request.user} is not superuser and isn't the avatar owner of {avatar}"
            )
            raise PermissionDenied
        
        serializer = UserAvatarSerializer(avatar, data=request.data, partial=True)
        if serializer.is_valid():
            updated_avatar = serializer.save()
            return Response(
                TinyUserAvatarSerializer(updated_avatar).data,
                status=HTTP_202_ACCEPTED,
            )
        else:
            settings.LOGGER.error(f"{serializer.errors}")
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        avatar = MediaService.get_user_avatar(pk)
        
        if not (request.user.is_superuser or request.user == avatar.user):
            settings.LOGGER.warning(
                f"Permission denied as {request.user} is not superuser and isn't the avatar owner of {avatar}"
            )
            raise PermissionDenied
        
        MediaService.delete_user_avatar(pk, request.user)
        return Response(status=HTTP_204_NO_CONTENT)
