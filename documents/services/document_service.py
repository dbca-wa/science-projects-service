"""
Document service - Base document operations
"""
from django.db import transaction
from django.db.models import Q
from django.conf import settings
from rest_framework.exceptions import NotFound, PermissionDenied

from ..models import ProjectDocument


class DocumentService:
    """Business logic for base document operations"""

    @staticmethod
    def list_documents(user, filters=None):
        """
        List documents with optional filters and N+1 optimization
        
        Args:
            user: User requesting documents
            filters: Dict of filter parameters
            
        Returns:
            QuerySet of ProjectDocument objects
        """
        documents = ProjectDocument.objects.all()
        
        # Apply filters if provided
        if filters:
            documents = DocumentService._apply_filters(documents, filters)
        
        # N+1 query optimization
        documents = documents.select_related(
            "project",
            "project__business_area",
            "project__business_area__division",
            "project__business_area__leader",
            "creator",
            "modifier",
        ).prefetch_related(
            "project__members",
            "project__members__user",
        )
        
        return documents.distinct()

    @staticmethod
    def get_document(pk):
        """
        Get document by ID with N+1 optimization
        
        Args:
            pk: Document primary key
            
        Returns:
            ProjectDocument instance
            
        Raises:
            NotFound: If document does not exist
        """
        try:
            return ProjectDocument.objects.select_related(
                "project",
                "project__business_area",
                "project__business_area__division",
                "project__business_area__leader",
                "creator",
                "modifier",
            ).prefetch_related(
                "project__members",
                "project__members__user",
            ).get(pk=pk)
        except ProjectDocument.DoesNotExist:
            raise NotFound(f"Document {pk} not found")

    @staticmethod
    @transaction.atomic
    def create_document(user, project, kind, data=None):
        """
        Create a new document
        
        Args:
            user: User creating the document
            project: Project instance
            kind: Document kind (concept, projectplan, etc.)
            data: Additional document data (optional)
            
        Returns:
            Created ProjectDocument instance
        """
        settings.LOGGER.info(f"{user} is creating {kind} document for project {project}")
        
        # Get next old_id (for legacy compatibility)
        from django.db.models import Max
        max_old_id = ProjectDocument.objects.aggregate(Max('old_id'))['old_id__max'] or 0
        
        document = ProjectDocument.objects.create(
            project=project,
            creator=user,
            modifier=user,
            kind=kind,
            status=ProjectDocument.StatusChoices.NEW,
            old_id=max_old_id + 1,
        )
        
        return document

    @staticmethod
    @transaction.atomic
    def update_document(pk, user, data):
        """
        Update document
        
        Args:
            pk: Document primary key
            user: User updating the document
            data: Updated document data
            
        Returns:
            Updated ProjectDocument instance
        """
        document = DocumentService.get_document(pk)
        settings.LOGGER.info(f"{user} is updating document {document}")
        
        # Update fields
        for field, value in data.items():
            if hasattr(document, field):
                setattr(document, field, value)
        
        document.modifier = user
        document.save()
        
        return document

    @staticmethod
    @transaction.atomic
    def delete_document(pk, user):
        """
        Delete document
        
        Args:
            pk: Document primary key
            user: User deleting the document
        """
        document = DocumentService.get_document(pk)
        settings.LOGGER.info(f"{user} is deleting document {document}")
        
        document.delete()

    @staticmethod
    def get_documents_pending_action(user, stage=None):
        """
        Get documents pending user's action
        
        Args:
            user: User to check pending actions for
            stage: Approval stage (1, 2, 3, or None for all)
            
        Returns:
            QuerySet of ProjectDocument objects
        """
        documents = ProjectDocument.objects.filter(
            status=ProjectDocument.StatusChoices.INAPPROVAL
        )
        
        # Filter by stage
        if stage == 1:
            # Stage 1: Project lead approval
            documents = documents.filter(
                project__members__user=user,
                project__members__is_leader=True,
                project_lead_approval_granted=False,
            )
        elif stage == 2:
            # Stage 2: Business area lead approval
            documents = documents.filter(
                project__business_area__leader=user,
                project_lead_approval_granted=True,
                business_area_lead_approval_granted=False,
            )
        elif stage == 3:
            # Stage 3: Directorate approval
            documents = documents.filter(
                project__business_area__division__director=user,
                project_lead_approval_granted=True,
                business_area_lead_approval_granted=True,
                directorate_approval_granted=False,
            )
        else:
            # All stages
            documents = documents.filter(
                Q(
                    project__members__user=user,
                    project__members__is_leader=True,
                    project_lead_approval_granted=False,
                )
                | Q(
                    project__business_area__leader=user,
                    project_lead_approval_granted=True,
                    business_area_lead_approval_granted=False,
                )
                | Q(
                    project__business_area__division__director=user,
                    project_lead_approval_granted=True,
                    business_area_lead_approval_granted=True,
                    directorate_approval_granted=False,
                )
            )
        
        # N+1 optimization
        documents = documents.select_related(
            "project",
            "project__business_area",
            "creator",
        ).prefetch_related(
            "project__members",
            "project__members__user",
        )
        
        return documents.distinct()

    @staticmethod
    def _apply_filters(queryset, filters):
        """Apply filters to document queryset"""
        from django.db.models import Q
        
        # Search term
        search_term = filters.get("searchTerm")
        if search_term:
            queryset = queryset.filter(
                Q(project__title__icontains=search_term)
                | Q(project__description__icontains=search_term)
                | Q(kind__icontains=search_term)
            )
        
        # Kind filter
        kind = filters.get("kind")
        if kind and kind != "All":
            queryset = queryset.filter(kind=kind)
        
        # Status filter
        status = filters.get("status")
        if status and status != "All":
            queryset = queryset.filter(status=status)
        
        # Project filter
        project_id = filters.get("project")
        if project_id:
            queryset = queryset.filter(project__pk=project_id)
        
        # Year filter
        year = filters.get("year")
        if year and year != "All":
            queryset = queryset.filter(project__year=year)
        
        return queryset
