"""
User CRUD views
"""
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
)

from common.utils import paginate_queryset
from users.services import UserService
from users.serializers import UserSerializer, TinyUserSerializer


class Users(APIView):
    """List and create users"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List users with pagination and filters"""
        # Delegate filtering to service (pass all query params)
        users = UserService.list_users(
            filters=request.query_params
        )
        
        # Paginate results
        paginated = paginate_queryset(users, request)
        
        serializer = TinyUserSerializer(paginated['items'], many=True)
        return Response({
            'users': serializer.data,
            'total_results': paginated['total_results'],
            'total_pages': paginated['total_pages'],
        })

    def post(self, request):
        """Create new user"""
        serializer = UserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        user = UserService.create_user(serializer.validated_data)
        result = UserSerializer(user)
        return Response(result.data, status=HTTP_201_CREATED)


class UserDetail(APIView):
    """Get, update, and delete user"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Get user detail"""
        user = UserService.get_user(pk)
        serializer = UserSerializer(user)
        return Response(serializer.data)

    def put(self, request, pk):
        """Update user"""
        serializer = UserSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        user = UserService.update_user(pk, serializer.validated_data)
        result = UserSerializer(user)
        return Response(result.data, status=HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        """Delete user"""
        UserService.delete_user(pk)
        return Response(status=HTTP_204_NO_CONTENT)


class DirectorateUsers(ListAPIView):
    """List users by directorate"""
    permission_classes = [IsAuthenticated]
    serializer_class = TinyUserSerializer

    def get_queryset(self):
        directorate_id = self.kwargs.get('directorate_id')
        return UserService.get_users_by_directorate(directorate_id)
