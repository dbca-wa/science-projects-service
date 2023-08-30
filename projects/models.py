from django.db import models
from django.forms import ValidationError
import categories
from common.models import CommonModel
from datetime import datetime as dt
from django.db.models import UniqueConstraint
from django.contrib.postgres.fields import JSONField, ArrayField

# ------------------------------
# Section: Research Function Model
# ------------------------------


# DONE
class ResearchFunction(CommonModel):
    """
    Model Definition for Research Function

    """

    name = models.CharField(max_length=150)
    description = models.TextField(
        null=True,
        blank=True,
    )
    association = models.TextField(
        null=True,
        blank=True,
        help_text="The research function's association with departmental programs/divisions.",
    )
    leader = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="research_functions_led",
        verbose_name="Function Leader",
        help_text="The scientist in charge of the Research Function",
    )
    is_active = models.BooleanField(
        default=False,
        help_text="Whether this research function has been deprecated or not.",
    )
    old_id = models.BigIntegerField()

    class Meta:
        verbose_name = "Research Function"
        verbose_name_plural = "Research Functions"

    def __str__(self) -> str:
        return f"{self.name}"


# ------------------------------
# Section: Project Models
# ------------------------------


def get_next_available_number_for_year():
    """Return the lowest available project number for a given project year."""

    year = dt.today().year
    project_numbers = Project.objects.filter(year=year).values("number")
    if project_numbers.count() == 0:
        return 1
    else:
        return max([x["number"] for x in list(project_numbers)]) + 1


# DONE
class Project(CommonModel):
    """
    Model Definition for Project
    """

    class CategoryKindChoices(models.TextChoices):
        SCIENCE = "science", "Science"
        STUDENT = "student", "Student"
        EXTERNAL = "external", "External"
        COREFUNCTION = "core_function", "Core Function"

    class StatusChoices(models.TextChoices):
        NEW = ("new", "New")
        PENDING = ("pending", "Pending Project Plan")
        ACTIVE = ("active", "Active (Approved)")
        UPDATING = ("updating", "Update Requested")
        CLOSUREREQ = ("closure_requested", "Closure Requested")
        CLOSING = ("closing", "Closure Pending Final Update")
        FINAL_UPDATE = ("final_update", "Final Update Requested")
        COMPLETED = ("completed", "Completed and Closed")
        TERMINATED = ("terminated", "Terminated and Closed")
        SUSPENDED = ("suspended", "Suspended")

    ACTIVE_ONLY = (
        StatusChoices.NEW,
        StatusChoices.PENDING,
        StatusChoices.ACTIVE,
        StatusChoices.UPDATING,
        StatusChoices.CLOSUREREQ,
        StatusChoices.CLOSING,
        StatusChoices.FINAL_UPDATE,
    )

    PUBLISHED_ONLY = (
        StatusChoices.ACTIVE,
        StatusChoices.UPDATING,
        StatusChoices.CLOSUREREQ,
        StatusChoices.CLOSING,
        StatusChoices.FINAL_UPDATE,
        StatusChoices.COMPLETED,
    )

    CLOSED_ONLY = (
        StatusChoices.COMPLETED,
        StatusChoices.TERMINATED,
        StatusChoices.SUSPENDED,
    )

    old_id = models.BigIntegerField()
    kind = models.CharField(
        choices=CategoryKindChoices.choices,
        blank=True,
        null=True,
        help_text="The project type determines the approval and \
                    documentation requirements during the project's \
                    life span. Choose wisely - you will not be able \
                    to change the project type later. \
                    If you get it wrong, create a new project of the \
                    correct type and tell admins to delete the duplicate \
                    project of the incorrect type.",
    )
    status = models.CharField(
        max_length=50,
        choices=StatusChoices.choices,
        default=StatusChoices.NEW,
    )
    year = models.PositiveIntegerField(
        default=dt.today().year,
        help_text="The project year with four digits, e.g. 2014",
    )
    number = models.PositiveIntegerField(
        default=get_next_available_number_for_year,
        help_text="The running project number within the project year.",
    )

    title = models.CharField(
        max_length=500,
        unique=True,
    )

    description = models.TextField(
        null=True,
        blank=True,
    )

    tagline = models.CharField(
        max_length=500,
        blank=True,
        null=True,
    )
    keywords = models.CharField(
        max_length=500,
        blank=True,
        null=True,
    )  # will extract as semicolon seperated values like linkedin skills

    start_date = models.DateField(
        blank=True,
        null=True,
    )  # Clarify if these two required
    end_date = models.DateField(
        blank=True,
        null=True,
    )

    business_area = models.ForeignKey(
        "agencies.BusinessArea",
        null=True,
        blank=True,
        on_delete=models.SET_NULL
        #  related_name='business'
    )

    def __str__(self) -> str:
        return f"({self.kind.upper()}) {self.title}"


# DONE
class ProjectArea(CommonModel):
    project = models.OneToOneField(
        "Project",
        related_name="area",
        on_delete=models.CASCADE,
    )
    areas = ArrayField(models.PositiveIntegerField(), default=list)

    def __str__(self) -> str:
        return f"{self.project} - {', '.join(str(area) for area in self.areas)}"

    class Meta:
        verbose_name = "Project Area"
        verbose_name_plural = "Project Areas"

    def save(self, *args, **kwargs):
        # Check for duplicate primary keys in the areas array
        duplicate_area_pks = set(
            [area for area in self.areas if self.areas.count(area) > 1]
        )
        if duplicate_area_pks:
            raise ValidationError(
                {
                    "areas": f"Duplicate primary keys found in areas: {duplicate_area_pks}"
                }
            )

        super().save(*args, **kwargs)


# DONE
class ProjectMember(CommonModel):
    class RoleChoices(models.TextChoices):
        SUPERVISING = ("supervising", "Supervising Scientist")
        RESEARCH = ("research", "Research Scientist")
        TECHNICAL = ("technical", "Technical Officer")
        EXTERNALCOL = ("externalcol", "External Collaborator")
        ACADEMICSUPER = ("academicsuper", "Academic Supervisor")
        STUDENT = ("student", "Supervised Student")
        EXTERNALPEER = ("externalpeer", "External Peer")
        CONSULTED = ("consulted", "Consulted Peer")
        GROUP = ("group", "Involved Group")

    STAFF_ROLES = (
        RoleChoices.SUPERVISING,
        RoleChoices.RESEARCH,
        RoleChoices.TECHNICAL,
    )

    project = models.ForeignKey(
        "projects.Project",
        related_name="members",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        "users.User",
        related_name="member_of",
        on_delete=models.CASCADE,
    )
    is_leader = models.BooleanField(
        default=False,  # Set the default value to False
    )
    role = models.CharField(
        max_length=50,
        choices=RoleChoices.choices,
    )
    time_allocation = models.FloatField(
        blank=True,
        null=True,
        default=0,
        verbose_name="Time allocation (0 to 1 FTE)",
        help_text="Indicative time allocation as a fraction of a Full Time Equivalent (210 person-days). Values between 0 and 1. Fill in estimated allocation for the next 12 months.",
    )
    position = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="List position",
        default=100,
        help_text="The lowest position number comes first in the team members list. Ignore to keep alphabetical order, increase to shift member towards the end of the list, decrease to promote member to beginning of the list.",
    )
    short_code = models.CharField(
        blank=True,
        null=True,
        max_length=500,
        verbose_name="Short code",
        help_text="Cost code for this project membership's salary. Allocated by divisional admin.",
    )
    comments = models.TextField(
        blank=True,
        null=True,
        help_text="Any comments clarifying the project membership.",
    )

    old_id = models.BigIntegerField()

    def __str__(self) -> str:
        return f"{self.user} ({self.project}) "

    class Meta:
        verbose_name = "Project Member"
        verbose_name_plural = "Project Members"


# DONE
class ProjectDetail(CommonModel):
    project = models.ForeignKey(
        "projects.Project",
        related_name="details",
        on_delete=models.CASCADE,
    )
    creator = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        related_name="projects_created",
        blank=True,
        null=True,
    )
    modifier = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        related_name="projects_modified",
        blank=True,
        null=True,
    )
    owner = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        related_name="projects_owned",
        null=True,
    )
    data_custodian = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        related_name="projects_where_data_custodian",
        blank=True,
        null=True,
    )
    site_custodian = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        related_name="projects_where_site_custodian",
        blank=True,
        null=True,
    )

    research_function = models.ForeignKey(
        "projects.ResearchFunction",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    old_output_program_id = models.BigIntegerField(
        blank=True,
        null=True,
    )

    def __str__(self) -> str:
        return f"(DETAILS) {self.project}"

    class Meta:
        verbose_name = "Base Project Detail"
        verbose_name_plural = "Base Project Details"


# DONE
class StudentProjectDetails(models.Model):
    """
    Student Project Model Definition
    """

    class StudentLevelChoices(models.TextChoices):
        PD = ("pd", "Post-Doc")
        PHD = ("phd", "PhD")
        MSC = ("msc", "MSc")
        HON = ("honours", "BSc Honours")
        YR4 = ("fourth_year", "Fourth Year")
        YR3 = ("third_year", "Third Year")
        UND = ("undergrad", "Undergradate")

    project = models.OneToOneField(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="student_project_info",
    )
    level = models.CharField(
        max_length=50,
        choices=StudentLevelChoices.choices,
        null=True,
        blank=True,
        default=StudentLevelChoices.PHD,
        help_text="The academic qualification achieved through this project.",
    )

    organisation = models.TextField(
        verbose_name="Academic Organisation",
        blank=True,
        null=True,
        help_text="The full name of the academic organisation.",
    )
    old_id = models.BigIntegerField()

    class Meta:
        verbose_name = "Student Project Detail"
        verbose_name_plural = "Student Project Details"

    def __str__(self) -> str:
        return f"{self.level} | {self.organisation}"


# DONE
class ExternalProjectDetails(models.Model):
    project = models.OneToOneField(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="external_project_info",
    )
    collaboration_with = models.CharField(
        max_length=1500, default="NO COLLABORATOR SET"
    )
    budget = models.CharField(
        max_length=1000,
        null=True,
        blank=True,
    )
    description = models.CharField(
        max_length=10000,
        null=True,
        blank=True,
    )
    aims = models.CharField(
        max_length=5000,
        null=True,
        blank=True,
    )
    old_id = models.BigIntegerField()

    class Meta:
        verbose_name = "External Project Detail"
        verbose_name_plural = "External Project Details"

    def __str__(self) -> str:
        return f"{self.project} | {self.collaboration_with} "
