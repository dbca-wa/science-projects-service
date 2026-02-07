"""
Notification service - Business logic for document notifications
"""

from .email_service import EmailService


class NotificationService:
    """Business logic for document notifications"""

    @staticmethod
    def notify_document_approved(document, approver):
        """
        Notify relevant parties when document is approved

        Args:
            document: Approved document instance
            approver: User who approved the document
        """
        recipients = NotificationService._get_document_recipients(document)

        EmailService.send_document_notification(
            notification_type="approved",
            document=document,
            recipients=recipients,
            actioning_user=approver,
            additional_context={
                "email_subject": f"{document.kind.title()} Approved",
            },
        )

    @staticmethod
    def notify_document_approved_directorate(document, approver):
        """
        Notify directorate when document is approved at directorate level

        Args:
            document: Approved document instance
            approver: User who approved the document
        """
        recipients = NotificationService._get_directorate_recipients(document)

        EmailService.send_document_notification(
            notification_type="approved_directorate",
            document=document,
            recipients=recipients,
            actioning_user=approver,
            additional_context={
                "email_subject": f"{document.kind.title()} Approved by Directorate",
            },
        )

    @staticmethod
    def notify_document_recalled(document, recaller, reason):
        """
        Notify when document is recalled

        Args:
            document: Recalled document instance
            recaller: User who recalled the document
            reason: Reason for recall
        """
        recipients = NotificationService._get_document_recipients(document)

        EmailService.send_document_notification(
            notification_type="recalled",
            document=document,
            recipients=recipients,
            actioning_user=recaller,
            additional_context={
                "email_subject": f"{document.kind.title()} Recalled",
                "recall_reason": reason,
            },
        )

    @staticmethod
    def notify_document_sent_back(document, sender, reason):
        """
        Notify when document is sent back for revision

        Args:
            document: Document instance
            sender: User who sent back the document
            reason: Reason for sending back
        """
        recipients = NotificationService._get_document_recipients(document)

        EmailService.send_document_notification(
            notification_type="sent_back",
            document=document,
            recipients=recipients,
            actioning_user=sender,
            additional_context={
                "email_subject": f"{document.kind.title()} Sent Back",
                "sent_back_reason": reason,
            },
        )

    @staticmethod
    def notify_document_ready(document, submitter):
        """
        Notify when document is ready for review

        Args:
            document: Document instance
            submitter: User who submitted the document
        """
        recipients = NotificationService._get_approver_recipients(document)

        EmailService.send_document_notification(
            notification_type="ready",
            document=document,
            recipients=recipients,
            actioning_user=submitter,
            additional_context={
                "email_subject": f"{document.kind.title()} Ready for Review",
            },
        )

    @staticmethod
    def notify_feedback_received(document, feedback_provider, feedback_text):
        """
        Notify when feedback is received on document

        Args:
            document: Document instance
            feedback_provider: User who provided feedback
            feedback_text: Feedback content
        """
        recipients = NotificationService._get_document_recipients(document)

        EmailService.send_document_notification(
            notification_type="feedback",
            document=document,
            recipients=recipients,
            actioning_user=feedback_provider,
            additional_context={
                "email_subject": f"Feedback on {document.kind.title()}",
                "feedback_text": feedback_text,
            },
        )

    @staticmethod
    def notify_review_request(document, requester):
        """
        Notify when document review is requested

        Args:
            document: Document instance
            requester: User requesting review
        """
        recipients = NotificationService._get_approver_recipients(document)

        EmailService.send_document_notification(
            notification_type="review",
            document=document,
            recipients=recipients,
            actioning_user=requester,
            additional_context={
                "email_subject": f"Review Requested: {document.kind.title()}",
            },
        )

    @staticmethod
    def send_bump_emails(documents, reminder_type="pending"):
        """
        Send reminder emails for pending documents

        Args:
            documents: List of document instances
            reminder_type: Type of reminder (pending, overdue, etc.)
        """
        for document in documents:
            recipients = NotificationService._get_approver_recipients(document)

            EmailService.send_document_notification(
                notification_type="bump",
                document=document,
                recipients=recipients,
                actioning_user=None,
                additional_context={
                    "email_subject": f"Reminder: {document.kind.title()} Pending",
                    "reminder_type": reminder_type,
                },
            )

    @staticmethod
    def notify_comment_mention(document, comment, mentioned_user, commenter):
        """
        Notify when user is mentioned in document comment

        Args:
            document: Document instance
            comment: Comment text
            mentioned_user: User who was mentioned
            commenter: User who made the comment
        """
        recipients = [
            {
                "name": mentioned_user.get_full_name(),
                "email": mentioned_user.email,
                "kind": "Mentioned User",
            }
        ]

        EmailService.send_document_notification(
            notification_type="mention",
            document=document,
            recipients=recipients,
            actioning_user=commenter,
            additional_context={
                "email_subject": f"You were mentioned in {document.kind.title()}",
                "comment": comment,
            },
        )

    @staticmethod
    def notify_new_cycle_open(cycle, projects):
        """
        Notify when new reporting cycle is opened

        Args:
            cycle: Cycle instance
            projects: List of projects affected
        """
        for project in projects:
            recipients = NotificationService._get_project_team_recipients(project)

            EmailService.send_document_notification(
                notification_type="new_cycle",
                document=None,
                recipients=recipients,
                actioning_user=None,
                additional_context={
                    "email_subject": f"New Reporting Cycle Opened: {cycle.year}",
                    "cycle": cycle,
                    "project": project,
                },
            )

    @staticmethod
    def notify_project_closed(project, closer):
        """
        Notify when project is closed

        Args:
            project: Project instance
            closer: User who closed the project
        """
        recipients = NotificationService._get_project_team_recipients(project)

        EmailService.send_document_notification(
            notification_type="project_closed",
            document=None,
            recipients=recipients,
            actioning_user=closer,
            additional_context={
                "email_subject": f"Project Closed: {project.title}",
                "project": project,
            },
        )

    @staticmethod
    def notify_project_reopened(project, reopener):
        """
        Notify when project is reopened

        Args:
            project: Project instance
            reopener: User who reopened the project
        """
        recipients = NotificationService._get_project_team_recipients(project)

        EmailService.send_document_notification(
            notification_type="project_reopened",
            document=None,
            recipients=recipients,
            actioning_user=reopener,
            additional_context={
                "email_subject": f"Project Reopened: {project.title}",
                "project": project,
            },
        )

    @staticmethod
    def send_spms_invite(user, inviter, invite_link):
        """
        Send SPMS invite email

        Args:
            user: User being invited
            inviter: User sending the invite
            invite_link: Link to SPMS
        """
        recipients = [
            {
                "name": user.get_full_name(),
                "email": user.email,
                "kind": "Invited User",
            }
        ]

        EmailService.send_document_notification(
            notification_type="spms_invite",
            document=None,
            recipients=recipients,
            actioning_user=inviter,
            additional_context={
                "email_subject": "You have been invited to SPMS",
                "invite_link": invite_link,
            },
        )

    @staticmethod
    def _get_document_recipients(document):
        """
        Get list of recipients for document notifications

        Returns:
            List of dicts with 'name', 'email', 'kind'
        """
        recipients = []

        # Add project team
        if hasattr(document, "project") and document.project:
            for member in document.project.members.all():
                recipients.append(
                    {
                        "name": member.user.get_full_name(),
                        "email": member.user.email,
                        "kind": "Project Lead" if member.is_leader else "Team Member",
                    }
                )

        # Add business area contacts
        if hasattr(document, "project") and document.project.business_area:
            ba = document.project.business_area
            if ba.leader:
                recipients.append(
                    {
                        "name": ba.leader.get_full_name(),
                        "email": ba.leader.email,
                        "kind": "Business Area Leader",
                    }
                )

        return recipients

    @staticmethod
    def _get_directorate_recipients(document):
        """
        Get directorate-level recipients for document notifications

        Returns:
            List of dicts with 'name', 'email', 'kind'
        """
        recipients = []

        # Add directorate contacts
        if hasattr(document, "project") and document.project.business_area:
            ba = document.project.business_area
            if hasattr(ba, "division") and ba.division:
                division = ba.division
                if hasattr(division, "director") and division.director:
                    recipients.append(
                        {
                            "name": division.director.get_full_name(),
                            "email": division.director.email,
                            "kind": "Director",
                        }
                    )

        return recipients

    @staticmethod
    def _get_approver_recipients(document):
        """
        Get approver recipients based on document approval stage

        Returns:
            List of dicts with 'name', 'email', 'kind'
        """
        recipients = []

        # Logic depends on document approval stage
        # This is a placeholder - actual logic depends on approval workflow
        if hasattr(document, "project") and document.project:
            # Stage 1: Project team leaders
            for member in document.project.members.filter(is_leader=True):
                recipients.append(
                    {
                        "name": member.user.get_full_name(),
                        "email": member.user.email,
                        "kind": "Project Lead",
                    }
                )

        return recipients

    @staticmethod
    def _get_project_team_recipients(project):
        """
        Get all project team members as recipients

        Returns:
            List of dicts with 'name', 'email', 'kind'
        """
        recipients = []

        for member in project.members.all():
            recipients.append(
                {
                    "name": member.user.get_full_name(),
                    "email": member.user.email,
                    "kind": "Project Lead" if member.is_leader else "Team Member",
                }
            )

        return recipients
