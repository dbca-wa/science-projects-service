"""
Business logic for caretaker task operations
"""
from django.conf import settings

from projects.models import Project, ProjectMember
from documents.models import ProjectDocument
from ..models import Caretaker


class CaretakerTaskService:
    """Service for managing caretaker tasks and document access"""

    @staticmethod
    def get_all_caretaker_assignments(user_id, processed_users=None):
        """
        Recursively gather all caretaker assignments, including nested relationships
        
        Args:
            user_id: ID of user to check
            processed_users: Set of already processed user IDs (for recursion)
            
        Returns:
            List of Caretaker objects
        """
        if processed_users is None:
            processed_users = set()
        
        if user_id in processed_users:
            return []
        
        processed_users.add(user_id)
        
        # Get direct caretaker assignments with optimized queries
        direct_assignments = Caretaker.objects.filter(
            caretaker=user_id
        ).select_related(
            'user',
            'user__work',
            'user__work__business_area',
        ).prefetch_related(
            'user__business_areas_led',
        )
        
        all_assignments = list(direct_assignments)
        
        # For each user being caretaken, get their caretaker assignments
        for assignment in direct_assignments:
            nested_assignments = CaretakerTaskService.get_all_caretaker_assignments(
                assignment.user.id, processed_users
            )
            all_assignments.extend(nested_assignments)
        
        return all_assignments

    @staticmethod
    def get_directorate_documents(project_queryset):
        """
        Get documents requiring Directorate attention
        
        Args:
            project_queryset: QuerySet of projects to check
            
        Returns:
            QuerySet of ProjectDocument objects
        """
        return ProjectDocument.objects.exclude(
            status=ProjectDocument.StatusChoices.APPROVED
        ).filter(
            project__in=project_queryset,
            business_area_lead_approval_granted=True,
            directorate_approval_granted=False,
        ).select_related(
            'project',
            'project__business_area',
        )

    @staticmethod
    def get_ba_documents(project_queryset):
        """
        Get documents requiring BA lead attention
        
        Args:
            project_queryset: QuerySet of projects to check
            
        Returns:
            QuerySet of ProjectDocument objects
        """
        return ProjectDocument.objects.exclude(
            status=ProjectDocument.StatusChoices.APPROVED
        ).filter(
            project__in=project_queryset,
            project_lead_approval_granted=True,
            business_area_lead_approval_granted=False,
        ).select_related(
            'project',
            'project__business_area',
        )

    @staticmethod
    def get_lead_documents(project_ids):
        """
        Get documents requiring project lead attention
        
        Args:
            project_ids: List/QuerySet of project IDs
            
        Returns:
            QuerySet of ProjectDocument objects
        """
        return ProjectDocument.objects.exclude(
            status=ProjectDocument.StatusChoices.APPROVED
        ).filter(
            project__in=project_ids,
            project_lead_approval_granted=False,
        ).select_related(
            'project',
            'project__business_area',
        )

    @staticmethod
    def get_team_documents(project_ids):
        """
        Get documents requiring team member attention
        
        Args:
            project_ids: List/QuerySet of project IDs
            
        Returns:
            QuerySet of ProjectDocument objects
        """
        return ProjectDocument.objects.exclude(
            status=ProjectDocument.StatusChoices.APPROVED
        ).filter(
            project__in=project_ids,
            project_lead_approval_granted=False,
        ).select_related(
            'project',
            'project__business_area',
        )

    @staticmethod
    def analyze_caretakee_roles(caretaker_assignments):
        """
        Analyze roles for all caretakees
        
        Args:
            caretaker_assignments: List of Caretaker objects
            
        Returns:
            Dict with role information
        """
        caretakee_ids = [assignment.user.id for assignment in caretaker_assignments]
        
        # Single query for all lead memberships
        lead_user_ids = set(
            ProjectMember.objects.exclude(
                project__status=Project.CLOSED_ONLY
            ).filter(
                user_id__in=caretakee_ids,
                is_leader=True
            ).values_list('user_id', flat=True)
        )
        
        # Single query for all team memberships
        team_user_ids = set(
            ProjectMember.objects.exclude(
                project__status=Project.CLOSED_ONLY
            ).filter(
                user_id__in=caretakee_ids,
                is_leader=False
            ).values_list('user_id', flat=True)
        )
        
        # Determine special roles
        directorate_user_found = False
        ba_leader_user_ids = set()
        
        for assignment in caretaker_assignments:
            user = assignment.user
            user_ba = user.work.business_area if hasattr(user, "work") else None
            
            # Check Directorate
            if ((user_ba and user_ba.name == "Directorate") or user.is_superuser):
                directorate_user_found = True
            
            # Check if BA leader
            if user.business_areas_led.exists():
                ba_leader_user_ids.add(user.id)
        
        return {
            'directorate_user_found': directorate_user_found,
            'ba_leader_user_ids': ba_leader_user_ids,
            'project_lead_user_ids': lead_user_ids,
            'team_member_user_ids': team_user_ids,
        }

    @staticmethod
    def get_tasks_for_user(user_id, requesting_user):
        """
        Get all tasks for a caretaker user
        
        Args:
            user_id: ID of caretaker user
            requesting_user: User making the request
            
        Returns:
            Dict with categorized document tasks
        """
        settings.LOGGER.info(
            f"{requesting_user} is getting pending caretaker documents for user {user_id}"
        )
        
        # Gather caretaker assignments
        caretaker_assignments = CaretakerTaskService.get_all_caretaker_assignments(user_id)
        
        # Analyze roles
        roles = CaretakerTaskService.analyze_caretakee_roles(caretaker_assignments)
        
        # Get active projects
        active_projects = Project.objects.exclude(status=Project.CLOSED_ONLY)
        
        # Build document lists
        all_documents = []
        
        # Directorate documents
        directorate_documents = []
        if roles['directorate_user_found']:
            directorate_documents = CaretakerTaskService.get_directorate_documents(active_projects)
            
            # Filter out documents requesting user already has access to
            requesting_user_ba = requesting_user.work.business_area if hasattr(requesting_user, "work") else None
            requesting_user_is_directorate = (
                (requesting_user_ba and requesting_user_ba.name == "Directorate") 
                or requesting_user.is_superuser
            )
            
            if requesting_user_is_directorate:
                directorate_documents = []
            
            all_documents.extend(directorate_documents)
        
        # BA documents
        ba_documents = []
        if roles['ba_leader_user_ids']:
            ba_projects = Project.objects.exclude(
                status=Project.CLOSED_ONLY
            ).filter(
                business_area__leader__in=roles['ba_leader_user_ids']
            )
            ba_documents = CaretakerTaskService.get_ba_documents(ba_projects)
            all_documents.extend(ba_documents)
        
        # Project lead documents
        lead_documents = []
        if roles['project_lead_user_ids']:
            lead_projects = ProjectMember.objects.filter(
                user_id__in=roles['project_lead_user_ids'],
                is_leader=True
            ).values_list("project_id", flat=True)
            lead_documents = CaretakerTaskService.get_lead_documents(lead_projects)
            all_documents.extend(lead_documents)
        
        # Team member documents
        member_documents = []
        if roles['team_member_user_ids']:
            team_projects = ProjectMember.objects.exclude(
                project__status=Project.CLOSED_ONLY
            ).filter(
                user_id__in=roles['team_member_user_ids'],
                is_leader=False,
            ).values_list("project_id", flat=True)
            member_documents = CaretakerTaskService.get_team_documents(team_projects)
            all_documents.extend(member_documents)
        
        return {
            'caretaker_assignments': caretaker_assignments,
            'roles': roles,
            'directorate_documents': directorate_documents,
            'ba_documents': ba_documents,
            'lead_documents': lead_documents,
            'member_documents': member_documents,
        }
