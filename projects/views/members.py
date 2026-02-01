"""
Project member management views
"""
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_202_ACCEPTED, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST

from ..serializers import ProjectMemberSerializer, TinyProjectMemberSerializer
from ..services.member_service import MemberService
from ..permissions.project_permissions import CanManageProjectMembers


class ProjectMembers(APIView):
    """List and create project members"""
    
    def get(self, request):
        """Get all project members"""
        members = MemberService.list_members()
        serializer = TinyProjectMemberSerializer(members, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        """Add member to project"""
        serializer = ProjectMemberSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        member = MemberService.add_member(
            project_id=serializer.validated_data['project'].pk,
            user_id=serializer.validated_data['user'].pk,
            data=serializer.validated_data,
            requesting_user=request.user
        )
        
        result_serializer = TinyProjectMemberSerializer(member)
        return Response(result_serializer.data, status=HTTP_201_CREATED)


class ProjectMemberDetail(APIView):
    """Get, update, delete project member"""
    
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id, user_id):
        """Get specific project member"""
        member = MemberService.get_member(project_id, user_id)
        serializer = TinyProjectMemberSerializer(member)
        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, project_id, user_id):
        """Update project member"""
        serializer = ProjectMemberSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        member = MemberService.update_member(
            project_id=project_id,
            user_id=user_id,
            data=serializer.validated_data,
            requesting_user=request.user
        )
        
        result_serializer = TinyProjectMemberSerializer(member)
        return Response(result_serializer.data, status=HTTP_202_ACCEPTED)

    def delete(self, request, project_id, user_id):
        """Remove member from project"""
        MemberService.remove_member(project_id, user_id, request.user)
        return Response(status=HTTP_204_NO_CONTENT)


class ProjectLeaderDetail(APIView):
    """Get project leader"""
    
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        """Get project leader"""
        leader = MemberService.get_project_leader(project_id)
        serializer = TinyProjectMemberSerializer(leader)
        return Response(serializer.data, status=HTTP_200_OK)


class MembersForProject(APIView):
    """Get all members for a project"""
    
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Get members for specific project"""
        settings.LOGGER.info(f"{request.user} is viewing members for project {pk}")
        
        members = MemberService.get_members_for_project(pk)
        serializer = TinyProjectMemberSerializer(members, many=True)
        return Response(serializer.data, status=HTTP_200_OK)


class PromoteToLeader(APIView):
    """Promote member to project leader"""
    
    def post(self, request):
        """Promote user to leader"""
        user_id = request.data.get('user_id')
        project_id = request.data.get('project_id')
        
        if not user_id or not project_id:
            return Response(
                {'error': 'user_id and project_id are required'},
                status=HTTP_400_BAD_REQUEST
            )
        
        member = MemberService.promote_to_leader(
            project_id=project_id,
            user_id=user_id,
            requesting_user=request.user
        )
        
        serializer = TinyProjectMemberSerializer(member)
        return Response(serializer.data, status=HTTP_202_ACCEPTED)
