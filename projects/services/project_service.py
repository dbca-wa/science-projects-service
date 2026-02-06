"""
Project service - Core project operations
"""

from django.db import transaction
from django.db.models import Q, Case, When, Value, IntegerField, CharField
from django.db.models.functions import Cast
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from rest_framework.exceptions import NotFound
import os

from ..models import Project, ProjectDetail, ProjectArea
from medias.models import ProjectPhoto


class ProjectService:
    """Business logic for project operations"""

    @staticmethod
    def list_projects(user, filters=None):
        """
        List projects with optional filters and N+1 optimization

        Args:
            user: User requesting projects
            filters: Dict of filter parameters

        Returns:
            QuerySet of Project objects
        """
        projects = Project.objects.all()

        # Apply filters if provided
        if filters:
            projects = ProjectService._apply_filters(projects, filters)

        # N+1 query optimization
        projects = projects.select_related(
            "business_area",
            "business_area__division",
            "business_area__division__director",
            "business_area__division__approver",
            "business_area__leader",
            "business_area__caretaker",
            "business_area__finance_admin",
            "business_area__data_custodian",
            "business_area__image",
            "image",
            "image__uploader",
            "area",
        ).prefetch_related(
            "members",
            "members__user",
            "members__user__profile",
            "members__user__work",
            "members__user__work__business_area",
            "members__user__caretakers",
            "members__user__caretaking_for",
            "business_area__division__directorate_email_list",
            "admintasks",
        )

        # Custom ordering
        projects = projects.annotate(
            custom_ordering=Case(
                When(
                    status__in=["suspended", "completed", "terminated"], then=Value(1)
                ),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).order_by("custom_ordering", "-year", "id")

        return projects.distinct()

    @staticmethod
    def _apply_filters(queryset, filters):
        """Apply filters to project queryset"""
        # Search term
        search_term = filters.get("searchTerm")
        if search_term:
            if ProjectService._is_project_tag_search(search_term):
                queryset = ProjectService._parse_search_term(search_term)
            else:
                queryset = queryset.annotate(
                    number_as_text=Cast("number", output_field=CharField())
                ).filter(
                    Q(title__icontains=search_term)
                    | Q(description__icontains=search_term)
                    | Q(tagline__icontains=search_term)
                    | Q(keywords__icontains=search_term)
                    | Q(number_as_text__icontains=search_term)
                )

        # User filter
        selected_user = filters.get("selected_user")
        if selected_user:
            queryset = queryset.filter(members__user__pk=selected_user)

        # Business area filter
        business_area = filters.get("businessarea")
        if business_area and business_area != "All":
            if isinstance(business_area, str) and "," in business_area:
                business_areas = business_area.split(",")
                queryset = queryset.filter(business_area__pk__in=business_areas)
            else:
                queryset = queryset.filter(business_area__pk=business_area)

        # Status filter
        status_slug = filters.get("projectstatus", "All")
        if status_slug != "All":
            if status_slug == "unknown":
                queryset = queryset.exclude(status__in=Project.StatusChoices.values)
            else:
                queryset = queryset.filter(status=status_slug)

        # Kind filter
        kind_slug = filters.get("projectkind", "All")
        if kind_slug != "All":
            queryset = queryset.filter(kind=kind_slug)

        # Year filter
        year_filter = filters.get("year", "All")
        if year_filter != "All":
            queryset = queryset.filter(year=year_filter)

        # Active/inactive filters
        only_active = filters.get("only_active", False)
        only_inactive = filters.get("only_inactive", False)

        if only_active:
            queryset = queryset.filter(status__in=Project.ACTIVE_ONLY)
        elif only_inactive:
            queryset = queryset.exclude(status__in=Project.ACTIVE_ONLY)

        return queryset

    @staticmethod
    def _is_project_tag_search(search_term):
        """Check if search term is a project tag (e.g., CF-2022-123)"""
        if not search_term:
            return False
        lower_term = search_term.lower()
        return (
            lower_term.startswith("cf-")
            or lower_term.startswith("sp-")
            or lower_term.startswith("stp-")
            or lower_term.startswith("ext-")
        )

    @staticmethod
    def _determine_db_kind(provided):
        """Determine database kind from project tag prefix"""
        if provided.startswith("CF"):
            return "core_function"
        elif provided.startswith("STP"):
            return "student"
        elif provided.startswith("SP"):
            return "science"
        elif provided.startswith("EXT"):
            return "external"
        return None

    @staticmethod
    def _parse_search_term(search_term):
        """Parse project tag search term (e.g., CF-2022-123)"""
        if not search_term:
            return Project.objects.none()

        parts = search_term.split("-")

        if not parts or not parts[0]:
            return Project.objects.none()

        db_kind = ProjectService._determine_db_kind(parts[0].upper())
        if not db_kind:
            return Project.objects.none()

        projects = Project.objects.filter(kind=db_kind)

        # Case: prefix-year-number (e.g., "CF-2022-123")
        if len(parts) >= 3:
            if parts[1] and parts[1].strip():
                try:
                    year_as_int = int(parts[1])
                    if len(parts[1]) == 4:
                        projects = projects.filter(year=year_as_int)
                except (ValueError, TypeError):
                    pass

            if parts[2] and parts[2].strip():
                try:
                    number_as_int = int(parts[2])
                    projects = projects.filter(number__icontains=number_as_int)
                except (ValueError, TypeError):
                    pass

        # Case: prefix-year (e.g., "CF-2022")
        elif len(parts) == 2:
            if parts[1] and parts[1].strip():
                try:
                    year_as_int = int(parts[1])
                    if len(parts[1]) == 4:
                        projects = projects.filter(year=year_as_int)
                except (ValueError, TypeError):
                    pass

        # Case: prefix only (e.g., "CF")
        # No additional filtering needed, just the kind filter above

        # Apply N+1 optimization for ALL cases (including single-part searches)
        projects = projects.select_related(
            "business_area",
            "business_area__division",
            "business_area__division__director",
            "business_area__division__approver",
            "business_area__leader",
            "business_area__caretaker",
            "business_area__finance_admin",
            "business_area__data_custodian",
            "business_area__image",
            "image",
            "image__uploader",
            "area",
        ).prefetch_related(
            "members",
            "members__user",
            "members__user__profile",
            "members__user__work",
            "members__user__work__business_area",
            "members__user__caretakers",
            "members__user__caretaking_for",
            "business_area__division__directorate_email_list",
            "admintasks",
        )

        return projects

    @staticmethod
    def get_project(pk):
        """
        Get a single project with N+1 optimization

        Args:
            pk: Project primary key

        Returns:
            Project instance

        Raises:
            NotFound: If project doesn't exist
        """
        try:
            return (
                Project.objects.select_related(
                    "business_area",
                    "business_area__division",
                    "business_area__division__director",
                    "business_area__division__approver",
                    "business_area__leader",
                    "business_area__caretaker",
                    "business_area__finance_admin",
                    "business_area__data_custodian",
                    "business_area__image",
                    "image",
                    "image__uploader",
                    "area",
                )
                .prefetch_related(
                    "business_area__division__directorate_email_list",
                )
                .get(pk=pk)
            )
        except Project.DoesNotExist:
            raise NotFound(f"Project {pk} not found")

    @staticmethod
    @transaction.atomic
    def create_project(user, data):
        """
        Create a new project

        Args:
            user: User creating the project
            data: Validated project data

        Returns:
            Created Project instance
        """
        settings.LOGGER.info(f"{user} is creating a {data.get('kind')} project")

        # Create base project
        project = Project.objects.create(
            kind=data["kind"],
            status="new",
            year=data["year"],
            title=data["title"],
            description=data.get("description", ""),
            tagline="",
            keywords=data.get("keywords", ""),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            business_area_id=data.get("business_area"),
        )

        return project

    @staticmethod
    @transaction.atomic
    def update_project(pk, user, data):
        """
        Update an existing project

        Args:
            pk: Project primary key
            user: User updating the project
            data: Validated update data

        Returns:
            Updated Project instance
        """
        project = ProjectService.get_project(pk)
        settings.LOGGER.info(f"{user} is updating project: {project}")

        # Update base project fields
        for field, value in data.items():
            if hasattr(project, field) and value is not None:
                setattr(project, field, value)

        project.save()
        return project

    @staticmethod
    @transaction.atomic
    def delete_project(pk, user):
        """
        Delete a project

        Args:
            pk: Project primary key
            user: User deleting the project
        """
        project = ProjectService.get_project(pk)
        settings.LOGGER.info(f"{user} is deleting project: {project}")
        project.delete()

    @staticmethod
    def handle_project_image(image):
        """
        Handle project image upload

        Args:
            image: Uploaded image file

        Returns:
            File path string
        """
        if isinstance(image, str):
            return image

        if image is None:
            return None

        original_filename = image.name
        subfolder = "projects"
        file_path = f"{subfolder}/{original_filename}"

        # Check if file already exists with same size
        if default_storage.exists(file_path):
            full_file_path = default_storage.path(file_path)
            if os.path.exists(full_file_path):
                existing_file_size = os.path.getsize(full_file_path)
                new_file_size = image.size
                if existing_file_size == new_file_size:
                    return file_path

        # Save new file
        content = ContentFile(image.read())
        file_path = default_storage.save(file_path, content)
        return file_path

    @staticmethod
    def get_project_years():
        """Get list of unique project years"""
        return (
            Project.objects.values_list("year", flat=True).distinct().order_by("-year")
        )

    @staticmethod
    @transaction.atomic
    def suspend_project(pk, user):
        """
        Suspend a project

        Args:
            pk: Project primary key
            user: User suspending the project

        Returns:
            Updated Project instance
        """
        project = ProjectService.get_project(pk)
        settings.LOGGER.info(f"{user} is suspending project: {project}")
        project.status = Project.StatusChoices.SUSPENDED
        project.save()
        return project

    @staticmethod
    def toggle_user_profile_visibility(pk, user):
        """
        Toggle project visibility on user's profile

        Args:
            pk: Project primary key
            user: User toggling visibility

        Returns:
            Updated Project instance
        """
        project = ProjectService.get_project(pk)

        if user.pk in project.hidden_from_staff_profiles:
            project.hidden_from_staff_profiles.remove(user.pk)
            settings.LOGGER.info(
                f"{user} is showing project {project} on their profile"
            )
        else:
            project.hidden_from_staff_profiles.append(user.pk)
            settings.LOGGER.info(
                f"{user} is hiding project {project} from their profile"
            )

        project.save()
        return project
