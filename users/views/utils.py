"""
User utility views
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.status import HTTP_200_OK

from users.services import UserService
from users.serializers import TinyUserSerializer


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

    def get(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({"error": "User ID required"}, status=400)
        
        user = UserService.get_user(user_id)
        return Response({"is_staff": user.is_staff})


class Me(APIView):
    """Get current user info"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = TinyUserSerializer(request.user)
        return Response(serializer.data)


class SmallInternalUserSearch(APIView):
    """Search users (internal)"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        search = request.query_params.get('search', '')
        if len(search) < 2:
            return Response([])
        
        users = UserService.list_users(search=search)[:10]
        serializer = TinyUserSerializer(users, many=True)
        return Response(serializer.data)
