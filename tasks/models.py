from django.db import models

from common.models import CommonModel


class StatusChoices(models.TextChoices):
    TODO = "todo", "To Do"
    INPROGRESS = "inprogress", "In Progress"
    DONE = "done", "Done"


class TaskTypeChoices(models.TextChoices):
    PERSONAL = "personal", "Personal"
    ASSIGNED = "assigned", "Assigned"


class DocumentActionChoices(models.TextChoices):
    # 1. Creates an AssignedTodo (Revise) for Author/s (project members besides reviewer)
    # State: NEW/UNDER_REVISION
    REQ_AUTH_REV = "requestauthorrevision", "Request Author Revision"
    # 2. Creates an AssignedTodo (Review) for Reviewer, and completes every project members related todo
    # State: IN_REVIEW
    REQ_REV_REV = "requestreviewerrevision", "Request Reviewer Revision"
    # 3. Approves the changes and Creates an AssignedTodo for Directorate for final approval (completes todo)
    # State: SEEKING_APPROVAL
    SEEK_FINAL_APPROVAL = "seekapproval", "Seek Approval"
    # 4. Rejects the changes and Creates an AssignedTodo (REVIEW) for Reviewer, with notes on reasoning
    # State: IN_REVIEW
    DIRECTORATE_DENY = "deny", "Deny"  # Deny document
    # 5. Approves the changes and sets the document to be added to ARAR Where possible
    # State: APPROVED
    DIRECTORATE_APPROVE = "approve", "Approve"  # Deny document

    # 0. Admin action (where directorate occupied or other issues)
    # Sets doc state (from approved) to INREVIEW and Creates an AssignedTodo (Review) for Reviewer
    RECALL = "recall", "Recall"  # Recall from approval


class AssignedTaskChoices(models.TextChoices):
    # When document is NEW
    SUBMIT_FOR_REVIEW = "submitreview", "Submit For Review"
    # When document in IN_REVIEW
    REVIEW = (
        "review",
        "Review",
    )  # Asses document, and approve or deny (as a result of REQREVREV action)
    # When document in UNDER_REVISION
    REVISE = "revise", "Revise"  # Revise document (as a result of REQAUTHREV action)
    # When document in SEEKING_APPROVAL
    FINAL_REVIEW = "finalreview", "FinalReview"  # Directorate Final Review


class Task(CommonModel):
    creator = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="taskscreated",
    )
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="tasks",
        blank=True,
        null=True,
    )
    document = models.ForeignKey(
        "documents.ProjectDocument",
        on_delete=models.CASCADE,
        related_name="tasks",
        blank=True,
        null=True,
    )
    name = models.CharField(
        max_length=250,
    )
    description = models.TextField(
        null=True,
        blank=True,
    )
    notes = models.CharField(
        max_length=2000,
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.TODO,
    )

    task_type = models.CharField(
        max_length=20,
        choices=TaskTypeChoices.choices,
        # default=TaskTypeChoices.PERSONAL,
    )

    # task_link = models.CharField(
    #     max_length=250,
    #     blank=True,
    #     null=True,
    # )

    def __str__(self) -> str:
        return f"{self.user} | {self.name}"

    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
