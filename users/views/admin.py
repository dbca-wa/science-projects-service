"""
Admin operation views
"""

from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView

from users.serializers import UserSerializer
from users.services import UserService


class ToggleUserActive(APIView):
    """Toggle user active status"""

    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        user = UserService.toggle_active(pk)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)


class SwitchAdmin(APIView):
    """Toggle user admin status"""

    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        user = UserService.switch_admin(pk)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)
