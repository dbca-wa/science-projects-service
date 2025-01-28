# region Imports ====================================================================================================
from django.db import models
from django.forms import ValidationError
from common.models import CommonModel
from django.core.cache import cache

# endregion  =================================================================================================

# region Models ====================================================================================================


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


class Caretaker(CommonModel):
    """Entries for approved caretaker requests"""

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="caretaker",
    )

    caretaker = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="caretaker_for",
    )

    end_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="The date at which caretaker status ends",
    )

    reason = models.TextField(
        blank=True,
        null=True,
        help_text="The reasoning for the caretaker request",
    )

    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Any additional notes for the caretaker request",
    )

    def __str__(self) -> str:
        return f"USER: {self.user} -> CARETAKER: {self.caretaker}; {self.reason}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Clear cache for both users involved
        cache.delete(f"caretakers_{self.user.pk}")
        cache.delete(f"caretaking_{self.user.pk}")
        cache.delete(f"caretakers_{self.caretaker.pk}")
        cache.delete(f"caretaking_{self.caretaker.pk}")

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)  # Ensure the parent delete is called
        # Clear cache for both users involved
        cache.delete(f"caretakers_{self.user.pk}")
        cache.delete(f"caretaking_{self.user.pk}")
        cache.delete(f"caretakers_{self.caretaker.pk}")
        cache.delete(f"caretaking_{self.caretaker.pk}")

    class Meta:
        verbose_name = "Caretaker"
        verbose_name_plural = "Caretakers"


# endregion  =================================================================================================
