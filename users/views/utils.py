"""
User utility views
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.status import HTTP_200_OK

from users.services import UserService
from users.serializers import TinyUserSerializer, UserMeSerializer


class CheckEmailExists(APIView):
    """Check if email already exists"""
    permission_classes = [AllowAny]

    def get(self, request):
        email = request.query_params.get('email')
        if not email:
            return Response({"error": "Email parameter required"}, status=400)
        
        exists = UserService.check_email_exists(email)
        return Response({"exists": exists})


class CheckNameExists(APIView):
    """Check if username already exists"""
    permission_classes = [AllowAny]

    def get(self, request):
        username = request.query_params.get('username')
        if not username:
            return Response({"error": "Username parameter required"}, status=400)
        
        exists = UserService.check_username_exists(username)
        return Response({"exists": exists})


class CheckUserIsStaff(APIView):
    """Check if user is staff"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            user = UserService.get_user(pk)
            return Response({"is_staff": user.is_staff})
        except Exception:
            return Response({"error": "User not found"}, status=400)


class Me(APIView):
    """Get current user info"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserMeSerializer(request.user)
        return Response(serializer.data)


class SmallInternalUserSearch(APIView):
    """Search users (internal)"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        search = request.query_params.get('search', '')
        if len(search) < 2:
            return Response([])
        
        users = UserService.list_users(filters={'search': search})[:10]
        serializer = TinyUserSerializer(users, many=True)
        return Response(serializer.data)
