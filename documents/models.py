import json
from django.db import models
from common.models import CommonModel
from datetime import datetime as dt
from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import MinValueValidator

from users.models import User


# Done (NOTE: Divisions removed)
class AnnualReport(CommonModel):
    """
    The Annual Research Report.

    There can only be one ARR per year, enforced with a `unique` year.
    """

    old_id = models.IntegerField()

    creator = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        related_name="created_reports",
        blank=True,
        null=True,
    )
    modifier = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        related_name="modified_reports",
        blank=True,
        null=True,
    )

    year = models.PositiveIntegerField(
        verbose_name="Report Year",
        help_text=(
            "The publication year of this report with four digits, e.g. 2014 for the ARAR 2013-2014"
        ),
        unique=True,
        validators=[MinValueValidator(2013)],
    )

    dm = models.TextField(
        verbose_name="Director's Message",
        blank=True,
        null=True,
        help_text="Directors's message (less than 10,000 words)",
    )

    service_delivery_intro = models.TextField(
        verbose_name="Service Deilvery Structure",
        blank=True,
        null=True,
        help_text="Introductory paragraph for the Science Delivery Structure section in the ARAR",
    )

    research_intro = models.TextField(
        verbose_name="Research Activities Intro",
        blank=True,
        null=True,
        help_text="Introduction paragraph for the Research Activity section in the ARAR",
    )

    student_intro = models.TextField(
        verbose_name="Student Projects Introduction",
        blank=True,
        null=True,
        help_text="Introduction paragraph for the Student Projects section in the ARAR",
    )

    publications = models.TextField(
        blank=True,
        null=True,
        verbose_name="Publications and Reports",
        help_text="Publications for the year",
    )

    date_open = models.DateField(
        help_text="The date at which submissions are opened for this report",
    )

    date_closed = models.DateField(
        help_text="The date at which submissions are closed for this report",
    )

    is_published = models.BooleanField(
        default=True,
    )

    def __str__(self) -> str:
        return f"ARAR - {self.year}"

    class Meta:
        verbose_name = "Annual Report"
        verbose_name_plural = "Annual Reports"


# Done (NOTE: Access document media - pdf via reverse accessor)
class ProjectDocument(CommonModel):
    """
    Project Document Definition
    """

    class CategoryKindChoices(models.TextChoices):
        CONCEPTPLAN = "concept", "Concept Plan"
        PROJECTPLAN = "projectplan", "Project Plan"
        PROGRESSREPORT = "progressreport", "Progress Report"
        STUDENTREPORT = "studentreport", "Student Report"
        PROJECTCLOSURE = "projectclosure", "Project Closure"

    class StatusChoices(models.TextChoices):
        NEW = "new", "New Document"
        REVISING = "revising", "Revising"
        INREVIEW = "inreview", "Review Requested"
        INAPPROVAL = "inapproval", "Approval Requested"
        APPROVED = "approved", "Approved"

    old_id = models.IntegerField()

    status = models.CharField(
        max_length=50,
        choices=StatusChoices.choices,
        default=StatusChoices.NEW,
    )

    project = models.ForeignKey(
        "projects.Project",
        related_name="documents",
        on_delete=models.CASCADE,
    )

    creator = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents_created",
    )

    modifier = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents_modified",
    )

    kind = models.CharField(
        choices=CategoryKindChoices.choices,
        blank=True,
        null=True,
        help_text="Type of document from above category kind choices",
    )

    project_lead_approval_granted = models.BooleanField(default=False)
    business_area_lead_approval_granted = models.BooleanField(default=False)
    directorate_approval_granted = models.BooleanField(default=False)
    pdf_generation_in_progress = models.BooleanField(default=False)

    # id, created, updated, oldid, status, kind, p,b,d,p, creator, modifier, projid

    def __str__(self) -> str:
        return f"{self.created_at.year} | {self.kind.capitalize()} - {self.project}"

    class Meta:
        verbose_name = "Project Document"
        verbose_name_plural = "Project Documents"


# Done
class ConceptPlan(models.Model):
    """
    Concept Plan Definition
    """

    document = models.ForeignKey(
        "documents.ProjectDocument",
        on_delete=models.CASCADE,
        related_name="concept_plan_details",
    )

    # =========
    background = models.TextField(
        blank=True, null=True, help_text="Provide background in up to 500 words"
    )
    # renamed from summary
    aims = models.TextField(
        blank=True,
        null=True,
        help_text="List the aims in up to 500 words",
    )
    outcome = models.TextField(
        blank=True,
        null=True,
        help_text="Summarise expected outcome in up to 500 words",
    )
    collaborations = models.TextField(
        blank=True,
        null=True,
        help_text="List expected collaborations in up to 500 words",
    )
    strategic_context = models.TextField(
        blank=True,
        null=True,
        help_text="Describe strategic context and management implications in up to 500 words",
    )

    staff_time_allocation = models.TextField(
        blank=True,
        null=True,
        help_text="Summarise staff time allocation by role for the first three years, or for a time span appropriate for the Project's life time",
        default=json.dumps(
            [
                ["Role", "Year 1", "Year 2", "Year 3"],
                ["Scientist", "", "", ""],
                ["Technical", "", "", ""],
                ["Volunteer", "", "", ""],
                ["Collaborator", "", "", ""],
            ],
            cls=DjangoJSONEncoder,
        ),
    )

    budget = models.TextField(
        blank=True,
        null=True,
        help_text="Indicate the operating budget for the first three years, or for a time span appropriate for the Project's life time.",
        default=json.dumps(
            [
                ["Source", "Year 1", "Year 2", "Year 3"],
                ["Consolidated Funds (DBCA)", "", "", ""],
                ["External Funding", "", "", ""],
            ],
            cls=DjangoJSONEncoder,
        ),
    )

    def __str__(self) -> str:
        title = self.document.project.title
        if len(title) > 50:
            title = title[:50] + "..."
        return f"CONCEPT PLAN | {title}"

    class Meta:
        verbose_name = "Concept Plan"
        verbose_name_plural = "Concept Plans"


# Done
class ProjectPlan(models.Model):
    """
    Project Plan Definition
    """

    document = models.ForeignKey(
        "documents.ProjectDocument",
        on_delete=models.CASCADE,
        related_name="project_plan_details",
    )

    background = models.TextField(
        blank=True,
        null=True,
        help_text="Describe project background (SPP C16) including a literature review",
    )

    aims = models.TextField(
        blank=True,
        null=True,
        help_text="List project aims",
    )

    outcome = models.TextField(
        blank=True,
        null=True,
        help_text="Describe expected project outcome",
    )

    knowledge_transfer = models.TextField(
        blank=True,
        null=True,
        help_text="Anticipated users of the knowledge to be gained, and technology transfer strategy",
    )

    project_tasks = models.TextField(
        blank=True,
        null=True,
        help_text="Major tasks, milestones and outputs. Indicate delivery time frame for each task.",
    )

    listed_references = (
        models.TextField(  # changed from references as it is a reserved word
            blank=True,
            null=True,
            help_text="Paste in the bibliography of your literature research",
        )
    )

    methodology = models.TextField(
        blank=True,
        null=True,
        help_text="Describe the study design and statistical analysis.",
    )

    involves_plants = models.BooleanField(
        default=False,
        help_text="Tick to indicate that this project will collect plant specimens, which will require endorsement by the Herbarium Curator.",
    )

    involves_animals = models.BooleanField(
        default=False,
        help_text="Tick to indicate that this project will involve direct interaction with animals, which will require endorsement by the Animal Ethics Committee.",
    )

    operating_budget = models.TextField(
        blank=True,
        null=True,
        help_text="Estimated budget: consolidated DBCA funds",
        default=json.dumps(
            [
                ["Source", "Year 1", "Year 2", "Year 3"],
                ["FTE Scientist", "", "", ""],
                ["FTE Technical", "", "", ""],
                ["Equipment", "", "", ""],
                ["Vehicle", "", "", ""],
                ["Travel", "", "", ""],
                ["Other", "", "", ""],
                ["Total", "", "", ""],
            ],
            cls=DjangoJSONEncoder,
        ),
    )

    operating_budget_external = models.TextField(
        blank=True,
        null=True,
        help_text="Estimated budget: external funds",
        default=json.dumps(
            [
                ["Source", "Year 1", "Year 2", "Year 3"],
                ["Salaries, Wages, Overtime", "", "", ""],
                ["Overheads", "", "", ""],
                ["Equipment", "", "", ""],
                ["Vehicle", "", "", ""],
                ["Travel", "", "", ""],
                ["Other", "", "", ""],
                ["Total", "", "", ""],
            ],
            cls=DjangoJSONEncoder,
        ),
    )

    related_projects = models.TextField(
        blank=True,
        null=True,
        help_text="Name related SPPs and the extent you have consulted with their project leaders",
    )

    def __str__(self) -> str:
        title = self.document.project.title
        if len(title) > 50:
            title = title[:50] + "..."
        return f"{title}"

    class Meta:
        verbose_name = "Project Plan"
        verbose_name_plural = "Project Plans"


# Done
class ProgressReport(models.Model):
    """
    Model Definition for info specific to Progress Reports
    """

    document = models.ForeignKey(
        "documents.ProjectDocument",
        on_delete=models.CASCADE,
        related_name="progress_report_details",
    )

    report = models.ForeignKey(
        "documents.AnnualReport",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="The annual report publishing this Report",
    )

    year = models.PositiveIntegerField(
        # editable=False,
        # default=dt.today().year,
        help_text="The year on which this progress report reports on with four digits, e.g. 2014 for FY 2013/14.",
    )

    is_final_report = models.BooleanField(
        default=False,
        help_text="Whether this report is the final progress report after submitting a project closure request.",
    )

    context = models.TextField(
        blank=True,
        null=True,
        help_text="A shortened introduction / background for the annual activity update. Aim for 100 to 150 words.",
    )

    aims = models.TextField(
        blank=True,
        null=True,
        help_text="A bullet point list of aims for the annual activity update. Aim for 100 to 150 words. One bullet point per aim.",
    )

    progress = models.TextField(
        blank=True,
        null=True,
        help_text="Current progress and achievements for the annual activity update. Aim for 100 to 150 words. One bullet point per achievement.",
    )

    implications = models.TextField(
        blank=True,
        null=True,
        help_text="Management implications for the annual activity update. Aim for 100 to 150 words. One bullet point per implication.",
    )

    future = models.TextField(
        blank=True,
        null=True,
        help_text="Future directions for the annual activity update. Aim for 100 to 150 words. One bullet point per direction.",
    )

    def __str__(self) -> str:
        title = self.document.project.title
        if len(title) > 50:
            title = title[:50] + "..."
        return f"PROGRESS REPORT ({self.year}) | {title}"

    class Meta:
        verbose_name = "Progress Report"
        verbose_name_plural = "Progress Reports"


# Done
class StudentReport(models.Model):
    """
    Model Definition for info specific to Student Projects
    """

    document = models.ForeignKey(
        "documents.ProjectDocument",
        on_delete=models.CASCADE,
        related_name="student_report_details",
    )

    # ===================

    report = models.ForeignKey(
        "documents.AnnualReport",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="The annual report publishing this StudentReport",
    )

    progress_report = models.TextField(
        blank=True,
        null=True,
        help_text="Report progress made this year in max. 150 words.",
    )

    year = models.PositiveIntegerField(
        editable=False,
        default=dt.today().year,
        help_text="The year on which this progress report reports on with four digits, e.g. 2014 for FY 2013/14.",
    )

    def __str__(self) -> str:
        title = self.document.project.title
        if len(title) > 50:
            title = title[:50] + "..."
        return f"STUDENT REPORT ({self.year}) | {title}"

    class Meta:
        verbose_name = "Student Report"
        verbose_name_plural = "Student Reports"


# Done
class ProjectClosure(models.Model):
    """
    Model Definition for info specific to Project Closure
    """

    document = models.ForeignKey(
        "documents.ProjectDocument",
        on_delete=models.CASCADE,
        related_name="project_closure_details",
    )

    # renamed from goal_coices
    class OutcomeChoices(models.TextChoices):
        COMPLETED = "completed", "Completed with final update"
        FORCE_COMPLETED = "forcecompleted", "Completed w/o Final Update"
        SUSPENDED = "suspended", "Suspended"
        TERMINATED = "terminated", "Terminated"

    # renamed from goal
    intended_outcome = models.CharField(
        max_length=300,
        blank=True,
        null=True,
        default=OutcomeChoices.COMPLETED,
        choices=OutcomeChoices.choices,
        help_text="The intended project status outcome of this closure",
    )

    reason = models.TextField(
        blank=True,
        null=True,
        help_text="Reason for closure, provided by project team and/or program leader.",
    )

    scientific_outputs = models.TextField(
        blank=True,
        null=True,
        help_text="List key publications and documents.",
    )

    knowledge_transfer = models.TextField(
        blank=True,
        null=True,
        help_text="List knowledge transfer achievements.",
    )

    data_location = models.TextField(
        blank=True,
        null=True,
        help_text="Paste links to all datasets of this project on the http://internal-data.dpaw.wa.gov.au",
    )

    hardcopy_location = models.TextField(
        blank=True,
        null=True,
        help_text="Location of hardcopy of all project data.",
    )

    backup_location = models.TextField(
        blank=True,
        null=True,
        help_text="Location of electronic project data.",
    )

    def __str__(self) -> str:
        title = self.document.project.title
        if len(title) > 50:
            title = title[:50] + "..."
        return f"CLOSURE | {title}| {self.intended_outcome}: {self.reason}"

    class Meta:
        verbose_name = "Project Closure"
        verbose_name_plural = "Project Closures"


# DONE
class Endorsement(models.Model):
    """
    Model Definition for endorsements. Split from Project Plan.
    """

    class EndorsementChoices(models.TextChoices):
        NOTREQUIRED = "notrequired", "Not Required"
        REQUIRED = "required", "Required"
        DENIED = "denied", "Denied"
        GRANTED = "granted", "Granted"

    project_plan = models.ForeignKey(
        "documents.ProjectPlan",
        related_name="endorsements",
        on_delete=models.CASCADE,
    )

    bm_endorsement = models.CharField(
        max_length=100,
        choices=EndorsementChoices.choices,
        default=EndorsementChoices.REQUIRED,
        help_text="The Biometrician's endorsement of the methodology's statistical validity.",
    )

    hc_endorsement = models.CharField(
        blank=True,
        null=True,
        max_length=100,
        default=EndorsementChoices.NOTREQUIRED,
        choices=EndorsementChoices.choices,
        help_text="The Herbarium Curator's endorsement of the planned collection of voucher specimens.",
    )

    ae_endorsement = models.CharField(
        blank=True,
        null=True,
        max_length=100,
        default=EndorsementChoices.NOTREQUIRED,
        choices=EndorsementChoices.choices,
        help_text="The Animal Ethics Committee's endorsement of the planned direct interaction with animals. Approval process is currently handled outside of SPMS.",
    )

    data_manager_endorsement = models.CharField(
        blank=True,
        null=True,
        max_length=100,
        default=EndorsementChoices.NOTREQUIRED,
        choices=EndorsementChoices.choices,
        help_text="The Data Manager's endorsement of the project's data management. \
            The DM will help to set up Wiki pages, data catalogue permissions, \
            scientific sites, and advise on metadata creation.",
    )

    data_management = models.TextField(
        blank=True,
        null=True,
        help_text="Describe how and where data will be maintained, archived, cataloged. Read DBCA guideline 16.",
    )

    no_specimens = models.TextField(
        blank=True,
        null=True,
        help_text="Estimate the number of collected vouchered specimens. Provide any additional info required for the Harbarium Curator's endorsement.",
    )

    def __str__(self) -> str:
        return f"ENDORSEMENTS - {self.project_plan}"

    class Meta:
        verbose_name = "Endorsement"
        verbose_name_plural = "Endorsements"


# TODO: views
class Publication(CommonModel):
    """
    Model Definition for publications
    """

    class PublicationChoices(models.TextChoices):
        INTERNAL = "internal", "Internal"
        EXTERNAL = "external", "External"

    title = models.CharField(max_length=500)
    year = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1800)],
    )
    kind = models.CharField(
        max_length=100,
        choices=PublicationChoices.choices,
    )
    internal_authors = models.ManyToManyField("users.User", related_name="publications")
    external_authors = models.CharField(
        max_length=1000,
        blank=True,
        null=True,
    )
    doc_link = models.CharField(
        max_length=1500,
        blank=True,
        null=True,
    )
    page_range = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    doi = models.CharField(
        max_length=1000,
        blank=True,
        null=True,
    )
    volume = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    def generate_apa_citation(self):
        internal_authors = list(self.internal_authors.all())
        external_authors = (
            self.external_authors.strip() if self.external_authors else ""
        )
        all_authors = (
            internal_authors + [external_authors]
            if self.kind == "internal"
            else [external_authors] + internal_authors
        )

        formatted_authors = [
            author.get_formatted_name() if isinstance(author, User) else author
            for author in all_authors
        ]

        key_author = formatted_authors[0] if formatted_authors else ""
        authors = (
            key_author
            + ", "
            + ", ".join(
                str(author) for author in formatted_authors if author != key_author
            )
            + ". "
        )

        citation_parts = [authors]

        if self.year:
            citation_parts.append(f"({self.year}).")

        citation_parts.append(f"{self.title}.")

        if self.doc_link:
            citation_parts.append(f"{self.doc_link}.")

        if self.page_range:
            citation_parts.append(f"pp. {self.page_range}.")

        if self.volume:
            citation_parts.append(f"{self.volume}.")

        citation = " ".join(citation_parts)

        return citation

    def get_apa_citation(self):
        # if not self.apa_citation:
        self.apa_citation = self.generate_apa_citation()
        self.save()
        return self.apa_citation

    def __str__(self) -> str:
        return f"Publication {self.kind} | {self.title}"

    class Meta:
        verbose_name = "Publication"
        verbose_name_plural = "Publications"
