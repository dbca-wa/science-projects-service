"""
Document validation utilities
"""

from rest_framework.exceptions import ValidationError


def validate_document_status_transition(current_status, new_status):
    """
    Validate document status transition

    Args:
        current_status: Current document status
        new_status: New document status

    Raises:
        ValidationError: If transition is invalid
    """
    # Define valid transitions
    valid_transitions = {
        "new": ["revising", "inreview"],
        "revising": ["inreview"],
        "inreview": ["inapproval", "revising"],
        "inapproval": ["approved", "revising"],
        "approved": [],  # Cannot transition from approved
    }

    if current_status not in valid_transitions:
        raise ValidationError(f"Invalid current status: {current_status}")

    if new_status not in valid_transitions.get(current_status, []):
        raise ValidationError(
            f"Cannot transition from {current_status} to {new_status}"
        )


def validate_approval_stage(document):
    """
    Validate document is ready for approval

    Args:
        document: ProjectDocument instance

    Raises:
        ValidationError: If document not ready for approval
    """
    if document.status != "inreview":
        raise ValidationError("Document must be in review before requesting approval")

    # Check if document has required details
    if not document.has_project_document_data():
        raise ValidationError("Document must have details before approval")


def validate_document_kind(kind):
    """
    Validate document kind

    Args:
        kind: Document kind string

    Raises:
        ValidationError: If kind is invalid
    """
    from ..models import ProjectDocument

    valid_kinds = [choice[0] for choice in ProjectDocument.CategoryKindChoices.choices]

    if kind not in valid_kinds:
        raise ValidationError(
            f"Invalid document kind: {kind}. Must be one of {valid_kinds}"
        )


def validate_annual_report_year(year):
    """
    Validate annual report year

    Args:
        year: Report year

    Raises:
        ValidationError: If year is invalid
    """
    from datetime import datetime

    current_year = datetime.now().year

    if year < 2013:
        raise ValidationError("Report year must be 2013 or later")

    if year > current_year + 1:
        raise ValidationError("Report year cannot be more than one year in the future")


def validate_endorsement_requirements(project_plan):
    """
    Validate endorsement requirements for project plan

    Args:
        project_plan: ProjectPlan instance

    Raises:
        ValidationError: If endorsement requirements not met
    """
    if not hasattr(project_plan, "endorsements"):
        return

    endorsements = project_plan.endorsements.all()

    for endorsement in endorsements:
        if (
            endorsement.ae_endorsement_required
            and not endorsement.ae_endorsement_provided
        ):
            raise ValidationError(
                "Animal Ethics Committee endorsement is required but not provided"
            )
