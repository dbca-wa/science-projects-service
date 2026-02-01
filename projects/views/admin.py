"""
Project admin and remedy views
"""
from django.conf import settings
from django.db.models import Q, Count
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import HTTP_200_OK

from ..serializers import ProblematicProjectSerializer, TinyProjectSerializer
from ..models import Project, ProjectMember
from documents.models import ProjectClosure


class UnapprovedThisFY(APIView):
    """Get unapproved projects for current fiscal year"""
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get projects needing approval"""
        settings.LOGGER.info(f"{request.user} is viewing unapproved projects")
        
        # Get current fiscal year (July 1 - June 30)
        from datetime import date
        today = date.today()
        if today.month >= 7:
            fy_start_year = today.year
        else:
            fy_start_year = today.year - 1
        
        # Get projects from current FY that are not approved
        projects = Project.objects.filter(
            year=fy_start_year,
            status__in=['new', 'pending']
        ).select_related(
            'business_area',
            'business_area__division',
        ).prefetch_related(
            'members',
            'members__user',
        )
        
        serializer = TinyProjectSerializer(projects, many=True)
        return Response(serializer.data, status=HTTP_200_OK)


class ProblematicProjects(APIView):
    """Get projects with issues"""
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get projects with various issues"""
        settings.LOGGER.info(f"{request.user} is viewing problematic projects")
        
        # Projects that are open but have approved closure
        open_with_closure = Project.objects.filter(
            status__in=['active', 'updating'],
        ).exclude(
            Q(projectclosure__isnull=True) | Q(projectclosure__document__status='new')
        ).select_related(
            'business_area',
        ).prefetch_related(
            'members',
        ).distinct()
        
        # Projects with no members
        memberless = Project.objects.annotate(
            member_count=Count('members')
        ).filter(
            member_count=0,
            status__in=['active', 'updating']
        ).select_related(
            'business_area',
        )
        
        # Projects with no leader
        leaderless = Project.objects.filter(
            status__in=['active', 'updating']
        ).exclude(
            members__is_leader=True
        ).select_related(
            'business_area',
        ).prefetch_related(
            'members',
        ).distinct()
        
        # Projects with multiple leaders
        multiple_leaders = Project.objects.annotate(
            leader_count=Count('members', filter=Q(members__is_leader=True))
        ).filter(
            leader_count__gt=1,
            status__in=['active', 'updating']
        ).select_related(
            'business_area',
        ).prefetch_related(
            'members',
        )
        
        # Projects with external leaders
        external_leaders = Project.objects.filter(
            members__is_leader=True,
            members__user__is_staff=False,
            status__in=['active', 'updating']
        ).select_related(
            'business_area',
        ).prefetch_related(
            'members',
            'members__user',
        ).distinct()
        
        response_data = {
            'open_with_closure': ProblematicProjectSerializer(open_with_closure, many=True).data,
            'memberless': ProblematicProjectSerializer(memberless, many=True).data,
            'leaderless': ProblematicProjectSerializer(leaderless, many=True).data,
            'multiple_leaders': ProblematicProjectSerializer(multiple_leaders, many=True).data,
            'external_leaders': ProblematicProjectSerializer(external_leaders, many=True).data,
        }
        
        return Response(response_data, status=HTTP_200_OK)


class RemedyOpenClosed(APIView):
    """Projects that are open but have approved closure"""
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get open projects with approved closures"""
        projects = Project.objects.filter(
            status__in=['active', 'updating'],
        ).exclude(
            Q(projectclosure__isnull=True) | Q(projectclosure__document__status='new')
        ).select_related(
            'business_area',
            'business_area__division',
        ).prefetch_related(
            'members',
            'members__user',
            'projectclosure_set',
        ).distinct()
        
        serializer = ProblematicProjectSerializer(projects, many=True)
        return Response(serializer.data, status=HTTP_200_OK)


class RemedyMemberlessProjects(APIView):
    """Projects with no members"""
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get projects with no members"""
        projects = Project.objects.annotate(
            member_count=Count('members')
        ).filter(
            member_count=0,
            status__in=['active', 'updating']
        ).select_related(
            'business_area',
            'business_area__division',
        )
        
        serializer = ProblematicProjectSerializer(projects, many=True)
        return Response(serializer.data, status=HTTP_200_OK)


class RemedyNoLeaderProjects(APIView):
    """Projects with no leader"""
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get projects with no leader"""
        projects = Project.objects.filter(
            status__in=['active', 'updating']
        ).exclude(
            members__is_leader=True
        ).select_related(
            'business_area',
            'business_area__division',
        ).prefetch_related(
            'members',
            'members__user',
        ).distinct()
        
        serializer = ProblematicProjectSerializer(projects, many=True)
        return Response(serializer.data, status=HTTP_200_OK)


class RemedyMultipleLeaderProjects(APIView):
    """Projects with multiple leaders"""
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get projects with multiple leaders"""
        projects = Project.objects.annotate(
            leader_count=Count('members', filter=Q(members__is_leader=True))
        ).filter(
            leader_count__gt=1,
            status__in=['active', 'updating']
        ).select_related(
            'business_area',
            'business_area__division',
        ).prefetch_related(
            'members',
            'members__user',
        )
        
        serializer = ProblematicProjectSerializer(projects, many=True)
        return Response(serializer.data, status=HTTP_200_OK)


class RemedyExternalLeaderProjects(APIView):
    """Projects with external (non-staff) leaders"""
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get projects with external leaders"""
        projects = Project.objects.filter(
            members__is_leader=True,
            members__user__is_staff=False,
            status__in=['active', 'updating']
        ).select_related(
            'business_area',
            'business_area__division',
        ).prefetch_related(
            'members',
            'members__user',
        ).distinct()
        
        serializer = ProblematicProjectSerializer(projects, many=True)
        return Response(serializer.data, status=HTTP_200_OK)
