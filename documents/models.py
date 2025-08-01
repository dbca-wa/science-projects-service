# region Imports ===================================
from django.db import models
from common.models import CommonModel
from django.core.validators import MinValueValidator
from bs4 import BeautifulSoup
from rest_framework import serializers

# endregion ==================================


# region AR ===================================
class SimpleDocSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ["pk"]


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

    dm_sign = models.TextField(
        verbose_name="Director's Message Sign off",
        blank=True,
        null=True,
        help_text="Sign off",
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

    pdf_generation_in_progress = models.BooleanField(default=False)

    is_published = models.BooleanField(
        default=False,
    )

    def save(self, *args, **kwargs):
        if not self.dm_sign:
            self.dm_sign = (
                '<p class="editor-p-light" dir="ltr">'
                '<span style="white-space: pre-wrap;">Dr Margaret Byrne</span>'
                "<br>"
                '<span style="white-space: pre-wrap;">Executive Director, Biodiversity and Conservation Science</span>'
                "<br>"
                f'<span style="white-space: pre-wrap;">October {self.year}</span>'
                "</p>"
            )
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"(ID: {self.pk}) ARAR - {self.year}"

    class Meta:
        verbose_name = "Annual Report"
        verbose_name_plural = "Annual Reports"


# endregion ==================================


# region Project Documents & Endorsement ===================================
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

    ae_endorsement_required = models.BooleanField(
        default=False,
        help_text="Whether Animal Ethics Committee Endorsement is Required.",
    )

    ae_endorsement_provided = models.BooleanField(
        default=False,
        help_text="The Animal Ethics Committee's endorsement of the planned direct interaction with animals. Approval process is currently handled outside of SPMS.",
    )

    no_specimens = models.TextField(
        blank=True,
        null=True,
        help_text="Estimate the number of collected vouchered specimens. Provide any additional info required for the Harbarium Curator's endorsement.",
    )

    data_management = models.TextField(
        blank=True,
        null=True,
        help_text="Describe how and where data will be maintained, archived, cataloged. Read DBCA guideline 16.",
    )

    def __str__(self) -> str:
        return f"ENDORSEMENTS - {self.project_plan}"

    class Meta:
        verbose_name = "Endorsement"
        verbose_name_plural = "Endorsements"


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

    def get_serializer_class(self, obj):
        class DynamicSerializer(SimpleDocSerializer):
            class Meta(SimpleDocSerializer.Meta):
                model = obj

        return DynamicSerializer

    def has_project_document_data(self):
        related_data = False
        if self.kind == ProjectDocument.CategoryKindChoices.CONCEPTPLAN:
            related_data = self.concept_plan_details.filter(document=self.pk).exists()
        elif self.kind == ProjectDocument.CategoryKindChoices.PROJECTPLAN:
            related_data = self.project_plan_details.filter(document=self.pk).exists()
        elif self.kind == ProjectDocument.CategoryKindChoices.PROGRESSREPORT:
            related_data = self.progress_report_details.filter(
                document=self.pk
            ).exists()
        elif self.kind == ProjectDocument.CategoryKindChoices.STUDENTREPORT:
            related_data = self.student_report_details.filter(document=self.pk).exists()
        elif self.kind == ProjectDocument.CategoryKindChoices.PROJECTCLOSURE:
            related_data = self.project_closure_details.filter(
                document=self.pk
            ).exists()
        return related_data

    def __str__(self) -> str:
        return f"({self.pk}) {self.created_at.year} | {self.kind.capitalize()} - {self.project}"

    class Meta:
        verbose_name = "Project Document"
        verbose_name_plural = "Project Documents"


class ConceptPlan(models.Model):
    """
    Concept Plan Definition
    """

    document = models.ForeignKey(
        "documents.ProjectDocument",
        on_delete=models.CASCADE,
        related_name="concept_plan_details",
    )

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="concept_plan",
    )

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
        default='<table class="table-light">\
					<colgroup>\
						<col>\
						<col>\
						<col>\
						<col>\
					</colgroup>\
					<tbody>\
						<tr>\
							<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
								<p class="editor-p-light" dir="ltr">\
									<span style="white-space: pre-wrap;">Role</span>\
								</p>\
							</th>\
							<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
								<p class="editor-p-light" dir="ltr">\
									<span style="white-space: pre-wrap;">Year 1</span>\
								</p>\
							</th>\
							<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
								<p class="editor-p-light" dir="ltr">\
									<span style="white-space: pre-wrap;">Year 2</span>\
								</p>\
							</th>\
							<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
								<p class="editor-p-light" dir="ltr">\
									<span style="white-space: pre-wrap;">Year 3</span>\
								</p>\
							</th>\
						</tr>\
						<tr>\
							<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
								<p class="editor-p-light" dir="ltr">\
									<span style="white-space: pre-wrap;">Scientist</span>\
								</p>\
							</th>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
						</tr>\
						<tr>\
							<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
								<p class="editor-p-light" dir="ltr">\
									<span style="white-space: pre-wrap;">Technical</span>\
								</p>\
							</th>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
						</tr>\
						<tr>\
							<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
								<p class="editor-p-light" dir="ltr">\
									<span style="white-space: pre-wrap;">Volunteer</span>\
								</p>\
							</th>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
						</tr>\
						<tr>\
							<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
								<p class="editor-p-light" dir="ltr">\
									<span style="white-space: pre-wrap;">Collaborator</span>\
								</p>\
							</th>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
						</tr>\
					</tbody>\
				</table>',
        # json.dumps(
        #     [
        #         ["Role", "Year 1", "Year 2", "Year 3"],
        #         ["Scientist", "", "", ""],
        #         ["Technical", "", "", ""],
        #         ["Volunteer", "", "", ""],
        #         ["Collaborator", "", "", ""],
        #     ],
        #     cls=DjangoJSONEncoder,
        # ),
    )

    budget = models.TextField(
        blank=True,
        null=True,
        help_text="Indicate the operating budget for the first three years, or for a time span appropriate for the Project's life time.",
        default='<table class="table-light"><colgroup>\
				<col>\
				<col>\
				<col>\
				<col>\
			</colgroup>\
			<tbody>\
				<tr>\
					<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
						<p class="editor-p-light" dir="ltr">\
							<span style="white-space: pre-wrap;">Source</span>\
						</p>\
					</th>\
					<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
						<p class="editor-p-light" dir="ltr">\
							<span style="white-space: pre-wrap;">Year 1</span>\
						</p>\
					</th>\
					<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
						<p class="editor-p-light" dir="ltr">\
							<span style="white-space: pre-wrap;">Year 2</span>\
						</p>\
					</th>\
					<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
						<p class="editor-p-light" dir="ltr">\
							<span style="white-space: pre-wrap;">Year 3</span>\
						</p>\
					</th>\
				</tr>\
				<tr>\
					<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
						<p class="editor-p-light" dir="ltr">\
							<span style="white-space: pre-wrap;">Consolidated Funds (DBCA)</span>\
						</p>\
					</th>\
					<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
					<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
					<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
				</tr>\
				<tr>\
					<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
						<p class="editor-p-light" dir="ltr">\
							<span style="white-space: pre-wrap;">External Funding</span>\
						</p>\
					</th>\
					<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
					<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
					<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
				</tr>\
			</tbody>\
		</table>',
    )

    def extract_inner_text(self, html_string):
        # Parse the HTML using BeautifulSoup
        soup = BeautifulSoup(html_string, "html.parser")
        # Extract the text content
        inner_text = soup.get_text(separator=" ", strip=True)

        return inner_text

    def __str__(self) -> str:
        title = self.document.project.title
        title = self.extract_inner_text(title)
        if len(title) > 50:
            title = title[:50] + "..."
        return f"(CONCEPT PLAN) {title}"

    class Meta:
        verbose_name = "Concept Plan"
        verbose_name_plural = "Concept Plans"


class ProjectPlan(models.Model):
    """
    Project Plan Definition
    """

    document = models.ForeignKey(
        "documents.ProjectDocument",
        on_delete=models.CASCADE,
        related_name="project_plan_details",
    )

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="project_plan",
    )

    background = models.TextField(
        blank=True,
        null=True,
        default="<p></p>",
        help_text="Describe project background (SPP C16) including a literature review",
    )

    aims = models.TextField(
        blank=True,
        null=True,
        default="<p></p>",
        help_text="List project aims",
    )

    outcome = models.TextField(
        blank=True,
        null=True,
        default="<p></p>",
        help_text="Describe expected project outcome",
    )

    knowledge_transfer = models.TextField(
        blank=True,
        null=True,
        default="<p></p>",
        help_text="Anticipated users of the knowledge to be gained, and technology transfer strategy",
    )

    project_tasks = models.TextField(
        blank=True,
        null=True,
        default="<p></p>",
        help_text="Major tasks, milestones and outputs. Indicate delivery time frame for each task.",
    )

    listed_references = (
        models.TextField(  # changed from references as it is a reserved word
            blank=True,
            null=True,
            default="<p></p>",
            help_text="Paste in the bibliography of your literature research",
        )
    )

    methodology = models.TextField(
        blank=True,
        null=True,
        default="<p></p>",
        help_text="Describe the study design and statistical analysis.",
    )

    operating_budget = models.TextField(
        blank=True,
        null=True,
        help_text="Estimated budget: consolidated DBCA funds",
        default='<table class="table-light">\
					<colgroup>\
						<col>\
						<col>\
						<col>\
						<col>\
					</colgroup>\
					<tbody>\
						<tr>\
							<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
								<p class="editor-p-light" dir="ltr">\
									<span style="white-space: pre-wrap;">Source</span>\
								</p>\
							</th>\
							<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
								<p class="editor-p-light" dir="ltr">\
									<span style="white-space: pre-wrap;">Year 1</span>\
								</p>\
							</th>\
							<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
								<p class="editor-p-light" dir="ltr">\
									<span style="white-space: pre-wrap;">Year 2</span>\
								</p>\
							</th>\
							<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
								<p class="editor-p-light" dir="ltr">\
									<span style="white-space: pre-wrap;">Year 3</span>\
								</p>\
							</th>\
						</tr>\
						<tr>\
							<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
								<p class="editor-p-light" dir="ltr">\
									<span style="white-space: pre-wrap;">FTE Scientist</span>\
								</p>\
							</th>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
						</tr>\
						<tr>\
							<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
								<p class="editor-p-light" dir="ltr">\
									<span style="white-space: pre-wrap;">FTE Technical</span>\
								</p>\
							</th>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
						</tr>\
						<tr>\
							<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
								<p class="editor-p-light" dir="ltr">\
									<span style="white-space: pre-wrap;">Equipment</span>\
								</p>\
							</th>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
						</tr>\
						<tr>\
							<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
								<p class="editor-p-light" dir="ltr">\
									<span style="white-space: pre-wrap;">Vehicle</span>\
								</p>\
							</th>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
						</tr>\
						<tr>\
							<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
								<p class="editor-p-light" dir="ltr">\
									<span style="white-space: pre-wrap;">Travel</span>\
								</p>\
							</th>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
						</tr>\
						<tr>\
							<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
								<p class="editor-p-light" dir="ltr">\
									<span style="white-space: pre-wrap;">Other</span>\
								</p>\
							</th>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
						</tr>\
						<tr>\
							<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
								<p class="editor-p-light" dir="ltr">\
									<span style="white-space: pre-wrap;">Total</span>\
								</p>\
							</th>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
						</tr>\
					</tbody>\
				</table>',
    )

    operating_budget_external = models.TextField(
        blank=True,
        null=True,
        help_text="Estimated budget: external funds",
        default='<table class="table-light">\
					<colgroup>\
						<col>\
						<col>\
						<col>\
						<col>\
					</colgroup>\
					<tbody>\
						<tr>\
							<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
								<p class="editor-p-light" dir="ltr">\
									<span style="white-space: pre-wrap;">Source</span>\
								</p>\
							</th>\
							<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
								<p class="editor-p-light" dir="ltr">\
									<span style="white-space: pre-wrap;">Year 1</span>\
								</p>\
							</th>\
							<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
								<p class="editor-p-light" dir="ltr">\
									<span style="white-space: pre-wrap;">Year 2</span>\
								</p>\
							</th>\
							<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
								<p class="editor-p-light" dir="ltr">\
									<span style="white-space: pre-wrap;">Year 3</span>\
								</p>\
							</th>\
						</tr>\
						<tr>\
							<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
								<p class="editor-p-light" dir="ltr">\
									<span style="white-space: pre-wrap;">Salaries, Wages, Overtime</span>\
								</p>\
							</th>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
						</tr>\
						<tr>\
							<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
								<p class="editor-p-light" dir="ltr">\
									<span style="white-space: pre-wrap;">Overheads</span>\
								</p>\
							</th>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
						</tr>\
						<tr>\
							<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
								<p class="editor-p-light" dir="ltr">\
									<span style="white-space: pre-wrap;">Equipment</span>\
								</p>\
							</th>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
						</tr>\
						<tr>\
							<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
								<p class="editor-p-light" dir="ltr">\
									<span style="white-space: pre-wrap;">Vehicle</span>\
								</p>\
							</th>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
						</tr>\
						<tr>\
							<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
								<p class="editor-p-light" dir="ltr">\
									<span style="white-space: pre-wrap;">Travel</span>\
								</p>\
							</th>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
						</tr>\
						<tr>\
							<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
								<p class="editor-p-light" dir="ltr">\
									<span style="white-space: pre-wrap;">Other</span>\
								</p>\
							</th>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
						</tr>\
						<tr>\
							<th class="table-cell-light table-cell-header-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start; background-color: rgb(242, 243, 245);">\
								<p class="editor-p-light" dir="ltr">\
									<span style="white-space: pre-wrap;">Total</span>\
								</p>\
							</th>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
							<td class="table-cell-light" style="border: 1px solid black; width: 175px; vertical-align: top; text-align: start;"></td>\
						</tr>\
					</tbody>\
				</table>',
    )

    related_projects = models.TextField(
        blank=True,
        null=True,
        default="<p></p>",
        help_text="Name related SPPs and the extent you have consulted with their project leaders",
    )

    def extract_inner_text(self, html_string):
        # Parse the HTML using BeautifulSoup
        soup = BeautifulSoup(html_string, "html.parser")
        # Extract the text content
        inner_text = soup.get_text(separator=" ", strip=True)

        return inner_text

    def __str__(self) -> str:
        title = self.document.project.title
        title = self.extract_inner_text(title)
        if len(title) > 50:
            title = title[:50] + "..."
        return f"(PROJECT PLAN) {title}"

    class Meta:
        verbose_name = "Project Plan"
        verbose_name_plural = "Project Plans"


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
        on_delete=models.CASCADE,
        help_text="The annual report publishing this Report",
    )

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="progress_reports",
    )

    year = models.PositiveIntegerField(
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

    def extract_inner_text(self, html_string):
        # Parse the HTML using BeautifulSoup
        soup = BeautifulSoup(html_string, "html.parser")
        # Extract the text content
        inner_text = soup.get_text(separator=" ", strip=True)

        return inner_text

    def __str__(self) -> str:
        title = self.document.project.title
        title = self.extract_inner_text(title)
        if len(title) > 50:
            title = title[:50] + "..."
        return f"PROGRESS REPORT ({self.year}) | {title}"

    class Meta:
        verbose_name = "Progress Report"
        verbose_name_plural = "Progress Reports"
        unique_together = ("report", "project")


class StudentReport(models.Model):
    """
    Model Definition for info specific to Student Projects
    """

    document = models.ForeignKey(
        "documents.ProjectDocument",
        on_delete=models.CASCADE,
        related_name="student_report_details",
    )

    report = models.ForeignKey(
        "documents.AnnualReport",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="The annual report publishing this StudentReport",
    )

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="student_reports",
    )

    progress_report = models.TextField(
        blank=True,
        null=True,
        help_text="Report progress made this year in max. 150 words.",
    )

    year = models.PositiveIntegerField(
        help_text="The year on which this progress report reports on with four digits, e.g. 2014 for FY 2013/14.",
    )

    def extract_inner_text(self, html_string):
        # Parse the HTML using BeautifulSoup
        soup = BeautifulSoup(html_string, "html.parser")
        # Extract the text content
        inner_text = soup.get_text(separator=" ", strip=True)

        return inner_text

    def __str__(self) -> str:
        title = self.document.project.title
        title = self.extract_inner_text(title)
        if len(title) > 50:
            title = title[:50] + "..."
        return f"STUDENT REPORT ({self.year}) | {title}"

    class Meta:
        verbose_name = "Student Report"
        verbose_name_plural = "Student Reports"
        unique_together = ("report", "project")


class ProjectClosure(models.Model):
    """
    Model Definition for info specific to Project Closure
    """

    document = models.ForeignKey(
        "documents.ProjectDocument",
        on_delete=models.CASCADE,
        related_name="project_closure_details",
    )

    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="closure"
    )

    # renamed from goal_coices
    class OutcomeChoices(models.TextChoices):
        COMPLETED = "completed", "Completed with final update"
        # SUSPENDED = "suspended", "Suspended"
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

    def extract_inner_text(self, html_string):
        # Parse the HTML using BeautifulSoup
        soup = BeautifulSoup(html_string, "html.parser")
        # Extract the text content
        inner_text = soup.get_text(separator=" ", strip=True)

        return inner_text

    def __str__(self) -> str:
        title = self.document.project.title
        title = self.extract_inner_text(title)
        if len(title) > 50:
            title = title[:50] + "..."
        return f"(PROJECT CLOSURE) {title}"

    class Meta:
        verbose_name = "Project Closure"
        verbose_name_plural = "Project Closures"


# endregion ==================================


# region ================== Custom Publication Models ==================


class CustomPublication(models.Model):
    """
    Model Definition for Publication
    """

    public_profile = models.ForeignKey(
        "users.PublicStaffProfile",
        on_delete=models.CASCADE,
        related_name="custom_publications",
    )

    year = models.PositiveIntegerField(
        help_text="Year of publication",
    )

    title = models.CharField(
        max_length=1000,
        help_text="Title of the publication",
    )

    def __str__(self) -> str:
        return self.title

    class Meta:
        verbose_name = "Publication"
        verbose_name_plural = "Publications"
