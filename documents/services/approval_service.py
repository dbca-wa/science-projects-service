"""
Approval service - Document approval workflow logic
"""

from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from ..models import ProjectDocument
from .notification_service import NotificationService


class ApprovalService:
    """Business logic for document approval workflows"""

    @staticmethod
    @transaction.atomic
    def request_approval(document, requester):
        """
        Request approval for document

        Args:
            document: ProjectDocument instance
            requester: User requesting approval

        Raises:
            ValidationError: If document not ready for approval
        """
        if document.status != ProjectDocument.StatusChoices.INREVIEW:
            raise ValidationError(
                "Document must be in review before requesting approval"
            )

        settings.LOGGER.info(
            f"{requester} is requesting approval for document {document}"
        )

        document.status = ProjectDocument.StatusChoices.INAPPROVAL
        document.save()

        # Notify approvers
        NotificationService.notify_document_ready(document, requester)

    @staticmethod
    @transaction.atomic
    def approve_stage_one(document, approver):
        """
        Approve document at stage 1 (project lead)

        Args:
            document: ProjectDocument instance
            approver: User approving the document

        Raises:
            PermissionDenied: If user not authorized
        """
        # Check permission
        if not ApprovalService._can_approve_stage_one(document, approver):
            raise PermissionDenied("User not authorized to approve at stage 1")

        settings.LOGGER.info(f"{approver} is approving document {document} at stage 1")

        document.project_lead_approval_granted = True
        document.save()

        # Notify next approver
        NotificationService.notify_document_ready(document, approver)

    @staticmethod
    @transaction.atomic
    def approve_stage_two(document, approver):
        """
        Approve document at stage 2 (business area lead)

        Args:
            document: ProjectDocument instance
            approver: User approving the document

        Raises:
            PermissionDenied: If user not authorized
            ValidationError: If stage 1 not complete
        """
        # Check stage 1 complete
        if not document.project_lead_approval_granted:
            raise ValidationError("Stage 1 approval must be granted first")

        # Check permission
        if not ApprovalService._can_approve_stage_two(document, approver):
            raise PermissionDenied("User not authorized to approve at stage 2")

        settings.LOGGER.info(f"{approver} is approving document {document} at stage 2")

        document.business_area_lead_approval_granted = True
        document.save()

        # Notify next approver
        NotificationService.notify_document_ready(document, approver)

    @staticmethod
    @transaction.atomic
    def approve_stage_three(document, approver):
        """
        Approve document at stage 3 (directorate) - final approval

        Args:
            document: ProjectDocument instance
            approver: User approving the document

        Raises:
            PermissionDenied: If user not authorized
            ValidationError: If previous stages not complete
        """
        # Check previous stages complete
        if not document.project_lead_approval_granted:
            raise ValidationError("Stage 1 approval must be granted first")
        if not document.business_area_lead_approval_granted:
            raise ValidationError("Stage 2 approval must be granted first")

        # Check permission
        if not ApprovalService._can_approve_stage_three(document, approver):
            raise PermissionDenied("User not authorized to approve at stage 3")

        settings.LOGGER.info(
            f"{approver} is approving document {document} at stage 3 (final)"
        )

        document.directorate_approval_granted = True
        document.status = ProjectDocument.StatusChoices.APPROVED
        document.save()

        # Notify document approved
        NotificationService.notify_document_approved(document, approver)
        NotificationService.notify_document_approved_directorate(document, approver)

    @staticmethod
    @transaction.atomic
    def send_back(document, sender, reason):
        """
        Send document back for revision

        Args:
            document: ProjectDocument instance
            sender: User sending back the document
            reason: Reason for sending back
        """
        settings.LOGGER.info(f"{sender} is sending back document {document}: {reason}")

        document.status = ProjectDocument.StatusChoices.REVISING
        document.save()

        # Notify document sent back
        NotificationService.notify_document_sent_back(document, sender, reason)

    @staticmethod
    @transaction.atomic
    def recall(document, recaller, reason):
        """
        Recall document from approval process

        Args:
            document: ProjectDocument instance
            recaller: User recalling the document
            reason: Reason for recall
        """
        settings.LOGGER.info(f"{recaller} is recalling document {document}: {reason}")

        # Reset approval flags
        document.project_lead_approval_granted = False
        document.business_area_lead_approval_granted = False
        document.directorate_approval_granted = False
        document.status = ProjectDocument.StatusChoices.REVISING
        document.save()

        # Notify document recalled
        NotificationService.notify_document_recalled(document, recaller, reason)

    @staticmethod
    @transaction.atomic
    def batch_approve(documents, approver, stage):
        """
        Batch approve multiple documents

        Args:
            documents: List of ProjectDocument instances
            approver: User approving the documents
            stage: Approval stage (1, 2, or 3)

        Returns:
            dict: Results with approved and failed documents
        """
        results = {
            "approved": [],
            "failed": [],
        }

        for document in documents:
            try:
                if stage == 1:
                    ApprovalService.approve_stage_one(document, approver)
                elif stage == 2:
                    ApprovalService.approve_stage_two(document, approver)
                elif stage == 3:
                    ApprovalService.approve_stage_three(document, approver)
                else:
                    raise ValidationError(f"Invalid stage: {stage}")

                results["approved"].append(document.pk)
            except (PermissionDenied, ValidationError) as e:
                results["failed"].append(
                    {
                        "document_id": document.pk,
                        "error": str(e),
                    }
                )

        return results

    @staticmethod
    def _can_approve_stage_one(document, user):
        """Check if user can approve at stage 1"""
        # User must be project lead
        return document.project.members.filter(user=user, is_leader=True).exists()

    @staticmethod
    def _can_approve_stage_two(document, user):
        """Check if user can approve at stage 2"""
        # User must be business area leader
        return document.project.business_area.leader == user

    @staticmethod
    def _can_approve_stage_three(document, user):
        """Check if user can approve at stage 3"""
        # User must be director
        if not document.project.business_area.division:
            return False
        return document.project.business_area.division.director == user

    @staticmethod
    def get_approval_stage(document):
        """
        Get current approval stage for document

        Args:
            document: ProjectDocument instance

        Returns:
            int: Current stage (0=not in approval, 1-3=stage number, 4=approved)
        """
        if document.status != ProjectDocument.StatusChoices.INAPPROVAL:
            if document.status == ProjectDocument.StatusChoices.APPROVED:
                return 4
            return 0

        if not document.project_lead_approval_granted:
            return 1
        elif not document.business_area_lead_approval_granted:
            return 2
        elif not document.directorate_approval_granted:
            return 3
        else:
            return 4

    @staticmethod
    def get_next_approver(document):
        """
        Get next approver for document

        Args:
            document: ProjectDocument instance

        Returns:
            User instance or None
        """
        stage = ApprovalService.get_approval_stage(document)

        if stage == 1:
            # Get project lead
            leader_member = document.project.members.filter(is_leader=True).first()
            return leader_member.user if leader_member else None
        elif stage == 2:
            # Get business area leader
            return document.project.business_area.leader
        elif stage == 3:
            # Get director
            if document.project.business_area.division:
                return document.project.business_area.division.director

        return None
