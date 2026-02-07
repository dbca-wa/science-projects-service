# region Imports ====================================================================================================
import uuid

from django.db import models
from django.forms import ValidationError

from common.models import CommonModel

# endregion  =================================================================================================

# region Models ====================================================================================================


# FOR THE GUIDES (making it extensible/not hardcoded fields)
class ContentField(CommonModel):
    """Model used to store content field configs for guide sections (dev)"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, blank=True, null=True)
    field_key = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    section = models.ForeignKey(
        "adminoptions.GuideSection",
        related_name="content_fields",
        on_delete=models.CASCADE,
    )
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]
        unique_together = [["section", "field_key"]]

    def __str__(self):
        return f"{self.section.title} - {self.field_key}"


class GuideSection(models.Model):
    """Model to store guide section configs"""

    id = models.CharField(max_length=100, primary_key=True)
    title = models.CharField(max_length=255)
    order = models.IntegerField(default=0)
    show_divider_after = models.BooleanField(default=False)
    category = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title


class AdminOptions(CommonModel):
    """Model Definition for Admin Controls"""

    class EmailOptions(models.TextChoices):
        ENABLED = "enabled", "Enabled"
        ADMIN = "admin", "Admin"
        DISABLED = "disabled", "Disabled"

    email_options = models.CharField(
        max_length=50,
        choices=EmailOptions.choices,
        default=EmailOptions.DISABLED,
    )
    maintainer = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admin",
    )

    guide_content = models.JSONField(
        default=dict,
        blank=True,
        help_text="Stores all guide content with field keys as dictionary keys",
    )

    # ADMIN
    guide_admin = models.TextField(
        blank=True,
        null=True,
        help_text="Provide RTE data to be displayed on the guide for admin",
    )

    # ABOUT
    guide_about = models.TextField(
        blank=True,
        null=True,
        help_text="Provide RTE data to be displayed on the guide for about",
    )

    # LOGIN
    guide_login = models.TextField(
        blank=True,
        null=True,
        help_text="Provide RTE data to be displayed on the guide for login",
    )

    # PROFILE
    guide_profile = models.TextField(
        blank=True,
        null=True,
        help_text="Provide RTE data to be displayed on the guide for profile",
    )

    # USERS
    guide_user_creation = models.TextField(
        blank=True,
        null=True,
        help_text="Provide RTE data to be displayed on the guide for user creation",
    )

    guide_user_view = models.TextField(
        blank=True,
        null=True,
        help_text="Provide RTE data to be displayed on the guide for viewing users",
    )

    # PROJECTS
    guide_project_creation = models.TextField(
        blank=True,
        null=True,
        help_text="Provide RTE data to be displayed on the guide for project creation",
    )

    guide_project_view = models.TextField(
        blank=True,
        null=True,
        help_text="Provide RTE data to be displayed on the guide for viewing projects",
    )

    # TEAM
    guide_project_team = models.TextField(
        blank=True,
        null=True,
        help_text="Provide RTE data to be displayed on the guide for project teams",
    )

    # DOCUMENTS
    guide_documents = models.TextField(
        blank=True,
        null=True,
        help_text="Provide RTE data to be displayed on the guide for project documents",
    )

    # ANNUAL REPORT
    guide_report = models.TextField(
        blank=True,
        null=True,
        help_text="Provide RTE data to be displayed on the guide for annual report",
    )

    # Helper methods for working with the new guide_content field
    def get_guide_content(self, field_key):
        """Get content for a specific field key"""
        return self.guide_content.get(field_key, "")

    def set_guide_content(self, field_key, content):
        """Set content for a specific field key"""
        if not self.guide_content:
            self.guide_content = {}
        self.guide_content[field_key] = content
        self.save(update_fields=["guide_content"])

    def clean(self):
        # Ensure only one instance of AdminOptions exists
        if AdminOptions.objects.exists() and self.pk is None:
            raise ValidationError("Only one instance of AdminOptions is allowed.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return "Admin Options"

    class Meta:
        verbose_name = "Admin Controls"


class AdminTask(CommonModel):
    """Model Definition for Admin Tasks"""

    class ActionTypes(models.TextChoices):
        DELETEPROJECT = "deleteproject", "Delete Project"
        MERGEUSER = "mergeuser", "Merge User"
        SETCARETAKER = "setcaretaker", "Set Caretaker"

    class TaskStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        FULFILLED = "fulfilled", "Fulfilled"
        CANCELLED = "cancelled", "Cancelled"
        REJECTED = "rejected", "Rejected"

    class ProjectDeletionReasons(models.TextChoices):
        DUPLICATE = "duplicate", "Duplicate project"
        MISTAKE = "mistake", "Made by mistake"
        OTHER = "other", "Other"

    # Main Fields
    action = models.CharField(
        max_length=50,
        choices=ActionTypes.choices,
        default=ActionTypes.DELETEPROJECT,
    )

    # Status of task
    status = models.CharField(
        max_length=50,
        choices=TaskStatus.choices,
        default=TaskStatus.PENDING,
    )

    # Fields associated with the project admin actions (when deleting)
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="admintasks",
    )

    requester = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="adminrequests",
    )

    # Fields associated with the user admin actions (will be requester if not set for caretaker)
    primary_user = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="merge_admintasks",
    )

    # an array of user pks integers to merge or set caretaker
    secondary_users = models.JSONField(
        blank=True,
        null=True,
        help_text="An array of user pks to merge or set caretaker (array of 1)",
    )

    reason = models.TextField(
        blank=True,
        null=True,
        help_text="The requester's reasoning for the task",
    )

    start_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="The date the task was initiated",
    )

    end_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="The date the task was completed",
    )

    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Any additional notes for the task",
    )

    def __str__(self) -> str:
        return f"{self.action} - {self.project} - {self.requester}"

    class Meta:
        verbose_name = "Admin Task"
        verbose_name_plural = "Admin Tasks"


# endregion  =================================================================================================
