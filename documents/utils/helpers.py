"""
Document helper utilities
"""


def get_document_display_name(document):
    """
    Get display name for document

    Args:
        document: ProjectDocument instance

    Returns:
        str: Display name
    """
    kind_map = {
        "concept": "Concept Plan",
        "projectplan": "Project Plan",
        "progressreport": "Progress Report",
        "studentreport": "Student Report",
        "projectclosure": "Project Closure",
    }

    kind_name = kind_map.get(document.kind, document.kind.title())
    project_title = document.project.title if document.project else "Unknown Project"

    return f"{kind_name} - {project_title}"


def get_approval_stage_name(stage):
    """
    Get display name for approval stage

    Args:
        stage: Stage number (1, 2, or 3)

    Returns:
        str: Stage name
    """
    stage_names = {
        1: "Project Lead Approval",
        2: "Business Area Lead Approval",
        3: "Directorate Approval",
    }

    return stage_names.get(stage, f"Stage {stage}")


def get_document_status_display(status):
    """
    Get display name for document status

    Args:
        status: Status code

    Returns:
        str: Display name
    """
    status_map = {
        "new": "New Document",
        "revising": "Revising",
        "inreview": "In Review",
        "inapproval": "In Approval",
        "approved": "Approved",
    }

    return status_map.get(status, status.title())


def is_document_editable(document, user):
    """
    Check if document is editable by user

    Args:
        document: ProjectDocument instance
        user: User instance

    Returns:
        bool: True if editable
    """
    # Document must not be approved
    if document.status == "approved":
        return False

    # User must be project member
    if not document.project.members.filter(user=user).exists():
        return False

    # If in approval, only project lead can edit
    if document.status == "inapproval":
        return document.project.members.filter(user=user, is_leader=True).exists()

    return True


def get_next_approval_stage(document):
    """
    Get next approval stage for document

    Args:
        document: ProjectDocument instance

    Returns:
        int: Next stage number (1, 2, 3) or None if complete
    """
    if not document.project_lead_approval_granted:
        return 1
    elif not document.business_area_lead_approval_granted:
        return 2
    elif not document.directorate_approval_granted:
        return 3
    else:
        return None


def format_document_date(date):
    """
    Format document date for display

    Args:
        date: datetime object

    Returns:
        str: Formatted date
    """
    if not date:
        return ""

    return date.strftime("%d %B %Y")


def get_document_year(document):
    """
    Get year for document

    Args:
        document: ProjectDocument instance

    Returns:
        int: Document year
    """
    # Try to get year from document details
    if hasattr(document, "progress_report_details"):
        details = document.progress_report_details.first()
        if details and hasattr(details, "year"):
            return details.year

    if hasattr(document, "student_report_details"):
        details = document.student_report_details.first()
        if details and hasattr(details, "year"):
            return details.year

    # Fall back to project year
    if document.project:
        return document.project.year

    # Fall back to creation year
    return document.created_at.year


def sanitize_html_content(html_content):
    """
    Sanitize HTML content for documents

    Args:
        html_content: HTML string

    Returns:
        str: Sanitized HTML
    """
    from bs4 import BeautifulSoup

    if not html_content:
        return ""

    # Parse HTML
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove script tags
    for script in soup.find_all("script"):
        script.decompose()

    # Remove style tags
    for style in soup.find_all("style"):
        style.decompose()

    return str(soup)


def get_current_maintainer_id():
    """
    Get the current maintainer user ID

    Returns:
        int: Maintainer user ID
    """
    from django.conf import settings

    # Get maintainer ID from settings or environment
    maintainer_id = getattr(settings, "MAINTAINER_USER_ID", None)

    if not maintainer_id:
        # Fall back to first superuser
        from users.models import User

        superuser = User.objects.filter(is_superuser=True).first()
        if superuser:
            maintainer_id = superuser.pk

    return maintainer_id


def extract_text_content(html_content):
    """
    Extract plain text from HTML content

    Args:
        html_content: HTML string

    Returns:
        str: Plain text content
    """
    from bs4 import BeautifulSoup

    if not html_content:
        return ""

    # Parse HTML
    soup = BeautifulSoup(html_content, "html.parser")

    # Get text content
    text = soup.get_text(separator=" ", strip=True)

    return text


def get_encoded_image():
    """
    Get base64 encoded DBCA logo image

    Returns:
        str: Base64 encoded image string
    """
    import base64
    import os

    from django.conf import settings

    # Path to DBCA logo
    image_path = os.path.join(settings.BASE_DIR, "config", "dbca.jpg")

    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
            return f"data:image/jpeg;base64,{encoded_string}"
    except FileNotFoundError:
        # Return empty string if image not found
        return ""
