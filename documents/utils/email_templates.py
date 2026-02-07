"""
Email template utilities
"""

from django.template.loader import render_to_string


class EmailTemplateRenderer:
    """Utility for rendering email templates"""

    TEMPLATE_DIR = "./email_templates/"

    @classmethod
    def render(cls, template_name: str, context: dict) -> str:
        """
        Render email template

        Args:
            template_name: Template file name
            context: Template context dict

        Returns:
            str: Rendered HTML content
        """
        template_path = f"{cls.TEMPLATE_DIR}{template_name}"
        return render_to_string(template_path, context)

    @classmethod
    def render_document_email(
        cls, email_type: str, document, recipient: dict, actioning_user
    ) -> tuple[str, str]:
        """
        Render document-related email

        Args:
            email_type: Type of email (approved, recalled, etc.)
            document: Document instance
            recipient: Recipient dict with 'name', 'email'
            actioning_user: User performing action

        Returns:
            tuple: (subject, html_content)
        """
        # Build context
        context = {
            "document": document,
            "project": document.project if hasattr(document, "project") else None,
            "recipient_name": recipient["name"],
            "actioning_user": actioning_user,
            "actioning_user_email": actioning_user.email if actioning_user else None,
        }

        # Get template and subject
        template_map = {
            "approved": ("document_approved_email.html", "Document Approved"),
            "approved_directorate": (
                "document_approved_directorate_email.html",
                "Document Approved by Directorate",
            ),
            "recalled": ("document_recalled_email.html", "Document Recalled"),
            "sent_back": ("document_sent_back_email.html", "Document Sent Back"),
            "ready": ("document_ready_email.html", "Document Ready for Review"),
            "feedback": ("feedback_received_email.html", "Feedback Received"),
            "review": ("review_document_email.html", "Review Requested"),
            "bump": ("bump_email.html", "Reminder: Pending Action"),
            "mention": ("document_comment_mention.html", "You were mentioned"),
            "new_cycle": ("new_cycle_open_email.html", "New Reporting Cycle"),
            "project_closed": ("project_closed_email.html", "Project Closed"),
            "project_reopened": ("project_reopened_email.html", "Project Reopened"),
            "spms_invite": ("spms_link_email.html", "SPMS Invitation"),
        }

        template_name, subject = template_map.get(
            email_type, ("document_approved_email.html", "Notification")
        )
        html_content = cls.render(template_name, context)

        return subject, html_content

    @classmethod
    def get_template_context(
        cls,
        document=None,
        project=None,
        recipient_name: str = None,
        actioning_user=None,
        **kwargs,
    ) -> dict:
        """
        Build standard template context

        Args:
            document: Document instance (optional)
            project: Project instance (optional)
            recipient_name: Recipient's full name
            actioning_user: User performing action
            **kwargs: Additional context variables

        Returns:
            dict: Template context
        """
        context = {
            "document": document,
            "project": project,
            "recipient_name": recipient_name,
            "actioning_user": actioning_user,
            "actioning_user_email": actioning_user.email if actioning_user else None,
        }

        # Add any additional context
        context.update(kwargs)

        return context
