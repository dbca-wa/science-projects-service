"""
Authentication views
"""

from django.conf import settings
from rest_framework.exceptions import ParseError, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView

from users.services import UserService


class Login(APIView):
    """User login"""

    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            raise ParseError("Username and password are required")

        user = UserService.authenticate_user(username, password)
        if user:
            UserService.login_user(request, user)
            return Response({"ok": "Welcome"})
        else:
            return Response({"error": "Incorrect password"})


class Logout(APIView):
    """User logout"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        if settings.DEBUG:
            UserService.logout_user(request)
            return Response({"ok": "True"})
        else:
            logout_data = UserService.logout_user(request)
            return Response(data=logout_data, status=HTTP_200_OK)


class ChangePassword(APIView):
    """Change user password"""

    permission_classes = [IsAuthenticated]

    def put(self, request):
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not old_password or not new_password:
            raise ParseError("Old and new passwords are required")

        try:
            UserService.change_password(request.user, old_password, new_password)
            return Response({"ok": "Password changed successfully"})
        except ValidationError as e:
            return Response({"error": str(e)}, status=400)
