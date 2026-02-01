"""
Member service - Project team management
"""
from django.db import transaction, IntegrityError
from django.conf import settings
from rest_framework.exceptions import NotFound, ValidationError

from ..models import ProjectMember, Project
from users.models import User


class MemberService:
    """Business logic for project member operations"""

    @staticmethod
    def list_members(project_id=None, user_id=None):
        """
        List project members with N+1 optimization
        
        Args:
            project_id: Optional project ID to filter by
            user_id: Optional user ID to filter by
            
        Returns:
            QuerySet of ProjectMember objects
        """
        members = ProjectMember.objects.select_related(
            "user",
            "user__profile",
            "user__work",
            "user__work__business_area",
            "user__work__business_area__division",
            "user__work__business_area__division__director",
            "user__work__business_area__division__approver",
            "user__work__business_area__leader",
            "user__work__business_area__caretaker",
            "user__work__business_area__finance_admin",
            "user__work__business_area__data_custodian",
            "user__work__business_area__image",
            "project",
            "project__business_area",
            "project__business_area__division",
            "project__business_area__image",
            "project__image",
        ).prefetch_related(
            "user__work__business_area__division__directorate_email_list",
            "project__business_area__division__directorate_email_list",
        )
        
        if project_id:
            members = members.filter(project_id=project_id)
        
        if user_id:
            members = members.filter(user_id=user_id)
        
        return members

    @staticmethod
    def get_member(project_id, user_id):
        """
        Get a specific project member
        
        Args:
            project_id: Project ID
            user_id: User ID
            
        Returns:
            ProjectMember instance
            
        Raises:
            NotFound: If member doesn't exist
        """
        try:
            return ProjectMember.objects.select_related(
                "user",
                "user__profile",
                "user__work",
                "project",
                "project__business_area",
            ).get(project_id=project_id, user_id=user_id)
        except ProjectMember.DoesNotExist:
            raise NotFound(f"Member not found for project {project_id} and user {user_id}")

    @staticmethod
    def get_project_leader(project_id):
        """
        Get the project leader
        
        Args:
            project_id: Project ID
            
        Returns:
            ProjectMember instance
            
        Raises:
            NotFound: If no leader exists
        """
        try:
            return ProjectMember.objects.select_related(
                "user",
                "user__profile",
                "user__work",
                "project",
            ).get(project_id=project_id, is_leader=True)
        except ProjectMember.DoesNotExist:
            raise NotFound(f"No leader found for project {project_id}")
        except ProjectMember.MultipleObjectsReturned:
            # Return first leader if multiple exist (data issue)
            return ProjectMember.objects.filter(
                project_id=project_id, 
                is_leader=True
            ).first()

    @staticmethod
    @transaction.atomic
    def add_member(project_id, user_id, data, requesting_user):
        """
        Add a member to a project
        
        Args:
            project_id: Project ID
            user_id: User ID to add
            data: Member data (role, is_leader, etc.)
            requesting_user: User making the request
            
        Returns:
            Created ProjectMember instance
            
        Raises:
            IntegrityError: If member already exists
            ValidationError: If data is invalid
        """
        settings.LOGGER.info(
            f"{requesting_user} is adding user {user_id} to project {project_id}"
        )
        
        # Validate role is provided
        if not data.get('role'):
            raise ValidationError("Role is required")
        
        try:
            member = ProjectMember.objects.create(
                project_id=project_id,
                user_id=user_id,
                is_leader=data.get('is_leader', False),
                role=data['role'],
                time_allocation=data.get('time_allocation', 0),
                position=data.get('position', 100),
                short_code=data.get('short_code'),
                comments=data.get('comments'),
                old_id=1,
            )
            return member
        except IntegrityError:
            raise ValidationError("This user is already a member of this project")

    @staticmethod
    @transaction.atomic
    def update_member(project_id, user_id, data, requesting_user):
        """
        Update a project member
        
        Args:
            project_id: Project ID
            user_id: User ID
            data: Updated member data
            requesting_user: User making the request
            
        Returns:
            Updated ProjectMember instance
        """
        member = MemberService.get_member(project_id, user_id)
        settings.LOGGER.info(
            f"{requesting_user} is updating member {user_id} on project {project_id}"
        )
        
        # Update fields
        for field, value in data.items():
            if hasattr(member, field) and value is not None:
                setattr(member, field, value)
        
        member.save()
        return member

    @staticmethod
    @transaction.atomic
    def remove_member(project_id, user_id, requesting_user):
        """
        Remove a member from a project
        
        Args:
            project_id: Project ID
            user_id: User ID
            requesting_user: User making the request
        """
        member = MemberService.get_member(project_id, user_id)
        settings.LOGGER.info(
            f"{requesting_user} is removing user {user_id} from project {project_id}"
        )
        member.delete()

    @staticmethod
    @transaction.atomic
    def promote_to_leader(project_id, user_id, requesting_user):
        """
        Promote a member to project leader
        
        Args:
            project_id: Project ID
            user_id: User ID to promote
            requesting_user: User making the request
            
        Returns:
            Updated ProjectMember instance
        """
        settings.LOGGER.info(
            f"{requesting_user} is promoting user {user_id} to leader of project {project_id}"
        )
        
        # Demote current leader(s)
        ProjectMember.objects.filter(
            project_id=project_id,
            is_leader=True
        ).update(is_leader=False)
        
        # Promote new leader
        member = MemberService.get_member(project_id, user_id)
        member.is_leader = True
        member.save()
        
        return member

    @staticmethod
    def get_members_for_project(project_id):
        """
        Get all members for a specific project with optimization
        
        Args:
            project_id: Project ID
            
        Returns:
            QuerySet of ProjectMember objects
        """
        return MemberService.list_members(project_id=project_id)

    @staticmethod
    def get_user_projects(user_id):
        """
        Get all projects a user is a member of
        
        Args:
            user_id: User ID
            
        Returns:
            QuerySet of Project objects
        """
        return Project.objects.filter(
            members__user_id=user_id
        ).select_related(
            "business_area",
            "business_area__division",
            "business_area__image",
            "image",
        ).prefetch_related(
            "members",
            "members__user",
        ).distinct()
