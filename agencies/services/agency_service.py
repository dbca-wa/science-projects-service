"""
Agency service - Business logic for agency, branch, division, business area, and affiliation operations
"""
from django.conf import settings
from django.db.models import Q
from rest_framework.exceptions import NotFound

from agencies.models import (
    Agency,
    Branch,
    Division,
    BusinessArea,
    DepartmentalService,
    Affiliation,
)


class AgencyService:
    """Business logic for agency-related operations"""

    # Affiliation operations
    @staticmethod
    def list_affiliations(search=None):
        """List affiliations with optional search"""
        queryset = Affiliation.objects.all()
        if search:
            queryset = queryset.filter(Q(name__icontains=search))
        return queryset.order_by("name")

    @staticmethod
    def get_affiliation(pk):
        """Get affiliation by ID"""
        try:
            return Affiliation.objects.get(pk=pk)
        except Affiliation.DoesNotExist:
            raise NotFound(f"Affiliation {pk} not found")

    @staticmethod
    def create_affiliation(user, data):
        """Create new affiliation"""
        settings.LOGGER.info(f"{user} is creating affiliation")
        return Affiliation.objects.create(**data)

    @staticmethod
    def update_affiliation(pk, user, data):
        """Update affiliation"""
        affiliation = AgencyService.get_affiliation(pk)
        settings.LOGGER.info(f"{user} is updating affiliation {affiliation}")
        
        for field, value in data.items():
            setattr(affiliation, field, value)
        affiliation.save()
        
        return affiliation

    @staticmethod
    def delete_affiliation(pk, user):
        """Delete affiliation"""
        affiliation = AgencyService.get_affiliation(pk)
        settings.LOGGER.info(f"{user} is deleting affiliation {affiliation}")
        affiliation.delete()

    # Agency operations
    @staticmethod
    def list_agencies():
        """List all agencies"""
        return Agency.objects.all()

    @staticmethod
    def get_agency(pk):
        """Get agency by ID"""
        try:
            return Agency.objects.get(pk=pk)
        except Agency.DoesNotExist:
            raise NotFound(f"Agency {pk} not found")

    @staticmethod
    def create_agency(user, data):
        """Create new agency"""
        settings.LOGGER.info(f"{user} is creating agency")
        return Agency.objects.create(**data)

    @staticmethod
    def update_agency(pk, user, data):
        """Update agency"""
        agency = AgencyService.get_agency(pk)
        settings.LOGGER.info(f"{user} is updating agency {agency}")
        
        for field, value in data.items():
            setattr(agency, field, value)
        agency.save()
        
        return agency

    @staticmethod
    def delete_agency(pk, user):
        """Delete agency"""
        agency = AgencyService.get_agency(pk)
        settings.LOGGER.info(f"{user} is deleting agency {agency}")
        agency.delete()

    # Branch operations
    @staticmethod
    def list_branches(search=None):
        """List branches with optional search"""
        queryset = Branch.objects.all()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(email__icontains=search)
            )
        return queryset.order_by("email")

    @staticmethod
    def get_branch(pk):
        """Get branch by ID"""
        try:
            return Branch.objects.get(pk=pk)
        except Branch.DoesNotExist:
            raise NotFound(f"Branch {pk} not found")

    @staticmethod
    def create_branch(user, data):
        """Create new branch"""
        settings.LOGGER.info(f"{user} is creating branch")
        return Branch.objects.create(**data)

    @staticmethod
    def update_branch(pk, user, data):
        """Update branch"""
        branch = AgencyService.get_branch(pk)
        settings.LOGGER.info(f"{user} is updating branch {branch}")
        
        for field, value in data.items():
            setattr(branch, field, value)
        branch.save()
        
        return branch

    @staticmethod
    def delete_branch(pk, user):
        """Delete branch"""
        branch = AgencyService.get_branch(pk)
        settings.LOGGER.info(f"{user} is deleting branch {branch}")
        branch.delete()

    # Business Area operations
    @staticmethod
    def list_business_areas(search=None, division=None, focus=None):
        """List business areas with optional filters"""
        queryset = BusinessArea.objects.select_related(
            "division",
            "division__director",
            "division__approver",
            "leader",
            "caretaker",
            "finance_admin",
            "data_custodian",
            "image",
        ).prefetch_related(
            "division__directorate_email_list"
        )
        
        if search:
            queryset = queryset.filter(Q(name__icontains=search))
        if division:
            queryset = queryset.filter(division=division)
        if focus:
            queryset = queryset.filter(focus=focus)
        
        return queryset.order_by("name")

    @staticmethod
    def get_business_area(pk):
        """Get business area by ID with optimized queries"""
        try:
            return BusinessArea.objects.select_related(
                "division",
                "division__director",
                "division__approver",
                "leader",
                "caretaker",
                "finance_admin",
                "data_custodian",
                "image",
            ).prefetch_related(
                "division__directorate_email_list"
            ).get(pk=pk)
        except BusinessArea.DoesNotExist:
            raise NotFound(f"Business area {pk} not found")

    @staticmethod
    def create_business_area(user, data):
        """Create new business area"""
        settings.LOGGER.info(f"{user} is creating business area")
        return BusinessArea.objects.create(**data)

    @staticmethod
    def update_business_area(pk, user, data):
        """Update business area"""
        ba = AgencyService.get_business_area(pk)
        settings.LOGGER.info(f"{user} is updating business area {ba}")
        
        for field, value in data.items():
            setattr(ba, field, value)
        ba.save()
        
        return ba

    @staticmethod
    def delete_business_area(pk, user):
        """Delete business area"""
        ba = AgencyService.get_business_area(pk)
        settings.LOGGER.info(f"{user} is deleting business area {ba}")
        ba.delete()

    @staticmethod
    def set_business_area_active(pk):
        """Toggle business area active status"""
        ba = AgencyService.get_business_area(pk)
        ba.is_active = not ba.is_active
        ba.save()
        return ba

    # Division operations
    @staticmethod
    def list_divisions():
        """List all divisions"""
        return Division.objects.all()

    @staticmethod
    def get_division(pk):
        """Get division by ID"""
        try:
            return Division.objects.get(pk=pk)
        except Division.DoesNotExist:
            raise NotFound(f"Division {pk} not found")

    @staticmethod
    def create_division(user, data):
        """Create new division"""
        settings.LOGGER.info(f"{user} is creating division")
        return Division.objects.create(**data)

    @staticmethod
    def update_division(pk, user, data):
        """Update division"""
        division = AgencyService.get_division(pk)
        settings.LOGGER.info(f"{user} is updating division {division}")
        
        for field, value in data.items():
            setattr(division, field, value)
        division.save()
        
        return division

    @staticmethod
    def delete_division(pk, user):
        """Delete division"""
        division = AgencyService.get_division(pk)
        settings.LOGGER.info(f"{user} is deleting division {division}")
        division.delete()

    # Departmental Service operations
    @staticmethod
    def list_departmental_services():
        """List all departmental services"""
        return DepartmentalService.objects.all()

    @staticmethod
    def get_departmental_service(pk):
        """Get departmental service by ID"""
        try:
            return DepartmentalService.objects.get(pk=pk)
        except DepartmentalService.DoesNotExist:
            raise NotFound(f"Departmental service {pk} not found")

    @staticmethod
    def create_departmental_service(user, data):
        """Create new departmental service"""
        settings.LOGGER.info(f"{user} is creating departmental service")
        return DepartmentalService.objects.create(**data)

    @staticmethod
    def update_departmental_service(pk, user, data):
        """Update departmental service"""
        service = AgencyService.get_departmental_service(pk)
        settings.LOGGER.info(f"{user} is updating departmental service {service}")
        
        for field, value in data.items():
            setattr(service, field, value)
        service.save()
        
        return service

    @staticmethod
    def delete_departmental_service(pk, user):
        """Delete departmental service"""
        service = AgencyService.get_departmental_service(pk)
        settings.LOGGER.info(f"{user} is deleting departmental service {service}")
        service.delete()

    @staticmethod
    def delete_affiliation(pk: int, user) -> dict:
        """
        Delete an affiliation and clean it from related projects
        
        Args:
            pk: Affiliation ID
            user: User performing the deletion
            
        Returns:
            Dict with deletion results
            
        Raises:
            NotFound: If affiliation not found
        """
        from projects.models import ExternalProjectDetails, StudentProjectDetails
        
        affiliation = AgencyService.get_affiliation(pk)
        
        # Find and clean external projects
        external_projects = ExternalProjectDetails.objects.filter(
            collaboration_with__icontains=affiliation.name
        )
        
        external_count = 0
        for ext in external_projects:
            if ext.collaboration_with:
                affiliations = [a.strip() for a in ext.collaboration_with.split('; ') if a.strip()]
                affiliations = [a for a in affiliations if a != affiliation.name]
                ext.collaboration_with = '; '.join(affiliations) if affiliations else ''
                ext.save()
                external_count += 1
        
        # Find and clean student projects
        student_projects = StudentProjectDetails.objects.filter(
            organisation__icontains=affiliation.name
        )
        
        student_count = 0
        for student in student_projects:
            if student.organisation:
                affiliations = [a.strip() for a in student.organisation.split('; ') if a.strip()]
                affiliations = [a for a in affiliations if a != affiliation.name]
                student.organisation = '; '.join(affiliations) if affiliations else ''
                student.save()
                student_count += 1
        
        project_count = external_count + student_count
        
        settings.LOGGER.info(
            f"{user} deleted affiliation {affiliation.name}, "
            f"cleaned from {project_count} project(s) "
            f"({external_count} external, {student_count} student)"
        )
        
        affiliation.delete()
        
        return {
            'message': f'Affiliation deleted and removed from {project_count} project(s)',
            'external_projects_updated': external_count,
            'student_projects_updated': student_count,
        }

    @staticmethod
    def clean_orphaned_affiliations(user) -> dict:
        """
        Clean orphaned affiliations that have no links to any projects or users
        
        Args:
            user: User performing the cleanup
            
        Returns:
            Dict with cleanup results
        """
        from projects.models import ExternalProjectDetails, StudentProjectDetails
        from users.models import UserWork
        
        all_affiliations = Affiliation.objects.all()
        total_count = all_affiliations.count()
        
        orphaned_affiliations = []
        
        for affiliation in all_affiliations:
            external_refs = ExternalProjectDetails.objects.filter(
                collaboration_with__icontains=affiliation.name
            ).count()
            
            student_refs = StudentProjectDetails.objects.filter(
                organisation__icontains=affiliation.name
            ).count()
            
            user_refs = UserWork.objects.filter(
                affiliation=affiliation.pk
            ).count()
            
            if external_refs == 0 and student_refs == 0 and user_refs == 0:
                orphaned_affiliations.append(affiliation)
        
        orphaned_count = len(orphaned_affiliations)
        
        if orphaned_count == 0:
            settings.LOGGER.info("No orphaned affiliations found")
            return {
                "message": "No orphaned affiliations found",
                "deleted_count": 0,
                "total_count": total_count
            }
        
        deleted_names = [aff.name for aff in orphaned_affiliations]
        for aff in orphaned_affiliations:
            settings.LOGGER.info(f"Deleting orphaned affiliation: {aff.name} (pk={aff.pk})")
            aff.delete()
        
        settings.LOGGER.info(
            f"Cleaned {orphaned_count} orphaned affiliation(s): {', '.join(deleted_names[:10])}"
            + (f" and {len(deleted_names) - 10} more..." if len(deleted_names) > 10 else "")
        )
        
        return {
            "message": f"Cleaned {orphaned_count} orphaned affiliation(s)",
            "deleted_count": orphaned_count,
            "total_count": total_count,
            "deleted_names": deleted_names[:10]
        }

    @staticmethod
    def list_business_areas():
        """
        List all business areas with optimized queries
        
        Returns:
            QuerySet of BusinessArea objects
        """
        return (
            BusinessArea.objects.select_related(
                "division",
                "image",
            )
            .prefetch_related(
                "division__directorate_email_list",
            )
            .all()
        )
