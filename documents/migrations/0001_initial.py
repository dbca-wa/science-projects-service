# Generated by Django 4.2.5 on 2023-10-06 02:47

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AnnualReport",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("old_id", models.IntegerField()),
                (
                    "year",
                    models.PositiveIntegerField(
                        help_text="The publication year of this report with four digits, e.g. 2014 for the ARAR 2013-2014",
                        unique=True,
                        validators=[django.core.validators.MinValueValidator(2013)],
                        verbose_name="Report Year",
                    ),
                ),
                (
                    "dm",
                    models.TextField(
                        blank=True,
                        help_text="Directors's message (less than 10,000 words)",
                        null=True,
                        verbose_name="Director's Message",
                    ),
                ),
                (
                    "service_delivery_intro",
                    models.TextField(
                        blank=True,
                        help_text="Introductory paragraph for the Science Delivery Structure section in the ARAR",
                        null=True,
                        verbose_name="Service Deilvery Structure",
                    ),
                ),
                (
                    "research_intro",
                    models.TextField(
                        blank=True,
                        help_text="Introduction paragraph for the Research Activity section in the ARAR",
                        null=True,
                        verbose_name="Research Activities Intro",
                    ),
                ),
                (
                    "student_intro",
                    models.TextField(
                        blank=True,
                        help_text="Introduction paragraph for the Student Projects section in the ARAR",
                        null=True,
                        verbose_name="Student Projects Introduction",
                    ),
                ),
                (
                    "publications",
                    models.TextField(
                        blank=True,
                        help_text="Publications for the year",
                        null=True,
                        verbose_name="Publications and Reports",
                    ),
                ),
                (
                    "date_open",
                    models.DateField(
                        help_text="The date at which submissions are opened for this report"
                    ),
                ),
                (
                    "date_closed",
                    models.DateField(
                        help_text="The date at which submissions are closed for this report"
                    ),
                ),
                ("is_published", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "Annual Report",
                "verbose_name_plural": "Annual Reports",
            },
        ),
        migrations.CreateModel(
            name="ConceptPlan",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "background",
                    models.TextField(
                        blank=True,
                        help_text="Provide background in up to 500 words",
                        null=True,
                    ),
                ),
                (
                    "aims",
                    models.TextField(
                        blank=True,
                        help_text="List the aims in up to 500 words",
                        null=True,
                    ),
                ),
                (
                    "outcome",
                    models.TextField(
                        blank=True,
                        help_text="Summarise expected outcome in up to 500 words",
                        null=True,
                    ),
                ),
                (
                    "collaborations",
                    models.TextField(
                        blank=True,
                        help_text="List expected collaborations in up to 500 words",
                        null=True,
                    ),
                ),
                (
                    "strategic_context",
                    models.TextField(
                        blank=True,
                        help_text="Describe strategic context and management implications in up to 500 words",
                        null=True,
                    ),
                ),
                (
                    "staff_time_allocation",
                    models.TextField(
                        blank=True,
                        default='[["Role", "Year 1", "Year 2", "Year 3"], ["Scientist", "", "", ""], ["Technical", "", "", ""], ["Volunteer", "", "", ""], ["Collaborator", "", "", ""]]',
                        help_text="Summarise staff time allocation by role for the first three years, or for a time span appropriate for the Project's life time",
                        null=True,
                    ),
                ),
                (
                    "budget",
                    models.TextField(
                        blank=True,
                        default='[["Source", "Year 1", "Year 2", "Year 3"], ["Consolidated Funds (DBCA)", "", "", ""], ["External Funding", "", "", ""]]',
                        help_text="Indicate the operating budget for the first three years, or for a time span appropriate for the Project's life time.",
                        null=True,
                    ),
                ),
            ],
            options={
                "verbose_name": "Concept Plan",
                "verbose_name_plural": "Concept Plans",
            },
        ),
        migrations.CreateModel(
            name="Endorsement",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "bm_endorsement",
                    models.CharField(
                        choices=[
                            ("notrequired", "Not Required"),
                            ("required", "Required"),
                            ("denied", "Denied"),
                            ("granted", "Granted"),
                        ],
                        default="required",
                        help_text="The Biometrician's endorsement of the methodology's statistical validity.",
                        max_length=100,
                    ),
                ),
                (
                    "hc_endorsement",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("notrequired", "Not Required"),
                            ("required", "Required"),
                            ("denied", "Denied"),
                            ("granted", "Granted"),
                        ],
                        default="notrequired",
                        help_text="The Herbarium Curator's endorsement of the planned collection of voucher specimens.",
                        max_length=100,
                        null=True,
                    ),
                ),
                (
                    "ae_endorsement",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("notrequired", "Not Required"),
                            ("required", "Required"),
                            ("denied", "Denied"),
                            ("granted", "Granted"),
                        ],
                        default="notrequired",
                        help_text="The Animal Ethics Committee's endorsement of the planned direct interaction with animals. Approval process is currently handled outside of SPMS.",
                        max_length=100,
                        null=True,
                    ),
                ),
                (
                    "data_manager_endorsement",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("notrequired", "Not Required"),
                            ("required", "Required"),
                            ("denied", "Denied"),
                            ("granted", "Granted"),
                        ],
                        default="notrequired",
                        help_text="The Data Manager's endorsement of the project's data management.             The DM will help to set up Wiki pages, data catalogue permissions,             scientific sites, and advise on metadata creation.",
                        max_length=100,
                        null=True,
                    ),
                ),
                (
                    "data_management",
                    models.TextField(
                        blank=True,
                        help_text="Describe how and where data will be maintained, archived, cataloged. Read DBCA guideline 16.",
                        null=True,
                    ),
                ),
                (
                    "no_specimens",
                    models.TextField(
                        blank=True,
                        help_text="Estimate the number of collected vouchered specimens. Provide any additional info required for the Harbarium Curator's endorsement.",
                        null=True,
                    ),
                ),
            ],
            options={
                "verbose_name": "Endorsement",
                "verbose_name_plural": "Endorsements",
            },
        ),
        migrations.CreateModel(
            name="ProgressReport",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "year",
                    models.PositiveIntegerField(
                        default=2023,
                        editable=False,
                        help_text="The year on which this progress report reports on with four digits, e.g. 2014 for FY 2013/14.",
                    ),
                ),
                (
                    "is_final_report",
                    models.BooleanField(
                        default=False,
                        help_text="Whether this report is the final progress report after submitting a project closure request.",
                    ),
                ),
                (
                    "context",
                    models.TextField(
                        blank=True,
                        help_text="A shortened introduction / background for the annual activity update. Aim for 100 to 150 words.",
                        null=True,
                    ),
                ),
                (
                    "aims",
                    models.TextField(
                        blank=True,
                        help_text="A bullet point list of aims for the annual activity update. Aim for 100 to 150 words. One bullet point per aim.",
                        null=True,
                    ),
                ),
                (
                    "progress",
                    models.TextField(
                        blank=True,
                        help_text="Current progress and achievements for the annual activity update. Aim for 100 to 150 words. One bullet point per achievement.",
                        null=True,
                    ),
                ),
                (
                    "implications",
                    models.TextField(
                        blank=True,
                        help_text="Management implications for the annual activity update. Aim for 100 to 150 words. One bullet point per implication.",
                        null=True,
                    ),
                ),
                (
                    "future",
                    models.TextField(
                        blank=True,
                        help_text="Future directions for the annual activity update. Aim for 100 to 150 words. One bullet point per direction.",
                        null=True,
                    ),
                ),
            ],
            options={
                "verbose_name": "Progress Report",
                "verbose_name_plural": "Progress Reports",
            },
        ),
        migrations.CreateModel(
            name="ProjectClosure",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "intended_outcome",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("completed", "Completed with final update"),
                            ("forcecompleted", "Completed w/o Final Update"),
                            ("suspended", "Suspended"),
                            ("terminated", "Terminated"),
                        ],
                        default="completed",
                        help_text="The intended project status outcome of this closure",
                        max_length=300,
                        null=True,
                    ),
                ),
                (
                    "reason",
                    models.TextField(
                        blank=True,
                        help_text="Reason for closure, provided by project team and/or program leader.",
                        null=True,
                    ),
                ),
                (
                    "scientific_outputs",
                    models.TextField(
                        blank=True,
                        help_text="List key publications and documents.",
                        null=True,
                    ),
                ),
                (
                    "knowledge_transfer",
                    models.TextField(
                        blank=True,
                        help_text="List knowledge transfer achievements.",
                        null=True,
                    ),
                ),
                (
                    "data_location",
                    models.TextField(
                        blank=True,
                        help_text="Paste links to all datasets of this project on the http://internal-data.dpaw.wa.gov.au",
                        null=True,
                    ),
                ),
                (
                    "hardcopy_location",
                    models.TextField(
                        blank=True,
                        help_text="Location of hardcopy of all project data.",
                        null=True,
                    ),
                ),
                (
                    "backup_location",
                    models.TextField(
                        blank=True,
                        help_text="Location of electronic project data.",
                        null=True,
                    ),
                ),
            ],
            options={
                "verbose_name": "Project Closure",
                "verbose_name_plural": "Project Closures",
            },
        ),
        migrations.CreateModel(
            name="ProjectDocument",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("old_id", models.IntegerField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("new", "New Document"),
                            ("revising", "Revising"),
                            ("inreview", "Review Requested"),
                            ("inapproval", "Approval Requested"),
                            ("approved", "Approved"),
                        ],
                        default="new",
                        max_length=50,
                    ),
                ),
                (
                    "kind",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("concept", "Concept Plan"),
                            ("projectplan", "Project Plan"),
                            ("progressreport", "Progress Report"),
                            ("studentreport", "Student Report"),
                            ("projectclosure", "Project Closure"),
                        ],
                        help_text="Type of document from above category kind choices",
                        null=True,
                    ),
                ),
                ("project_lead_approval_granted", models.BooleanField(default=False)),
                (
                    "business_area_lead_approval_granted",
                    models.BooleanField(default=False),
                ),
                ("directorate_approval_granted", models.BooleanField(default=False)),
                ("pdf_generation_in_progress", models.BooleanField(default=False)),
            ],
            options={
                "verbose_name": "Project Document",
                "verbose_name_plural": "Project Documents",
            },
        ),
        migrations.CreateModel(
            name="ProjectPlan",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "background",
                    models.TextField(
                        blank=True,
                        help_text="Describe project background (SPP C16) including a literature review",
                        null=True,
                    ),
                ),
                (
                    "aims",
                    models.TextField(
                        blank=True, help_text="List project aims", null=True
                    ),
                ),
                (
                    "outcome",
                    models.TextField(
                        blank=True,
                        help_text="Describe expected project outcome",
                        null=True,
                    ),
                ),
                (
                    "knowledge_transfer",
                    models.TextField(
                        blank=True,
                        help_text="Anticipated users of the knowledge to be gained, and technology transfer strategy",
                        null=True,
                    ),
                ),
                (
                    "project_tasks",
                    models.TextField(
                        blank=True,
                        help_text="Major tasks, milestones and outputs. Indicate delivery time frame for each task.",
                        null=True,
                    ),
                ),
                (
                    "listed_references",
                    models.TextField(
                        blank=True,
                        help_text="Paste in the bibliography of your literature research",
                        null=True,
                    ),
                ),
                (
                    "methodology",
                    models.TextField(
                        blank=True,
                        help_text="Describe the study design and statistical analysis.",
                        null=True,
                    ),
                ),
                (
                    "involves_plants",
                    models.BooleanField(
                        default=False,
                        help_text="Tick to indicate that this project will collect plant specimens, which will require endorsement by the Herbarium Curator.",
                    ),
                ),
                (
                    "involves_animals",
                    models.BooleanField(
                        default=False,
                        help_text="Tick to indicate that this project will involve direct interaction with animals, which will require endorsement by the Animal Ethics Committee.",
                    ),
                ),
                (
                    "operating_budget",
                    models.TextField(
                        blank=True,
                        default='[["Source", "Year 1", "Year 2", "Year 3"], ["FTE Scientist", "", "", ""], ["FTE Technical", "", "", ""], ["Equipment", "", "", ""], ["Vehicle", "", "", ""], ["Travel", "", "", ""], ["Other", "", "", ""], ["Total", "", "", ""]]',
                        help_text="Estimated budget: consolidated DBCA funds",
                        null=True,
                    ),
                ),
                (
                    "operating_budget_external",
                    models.TextField(
                        blank=True,
                        default='[["Source", "Year 1", "Year 2", "Year 3"], ["Salaries, Wages, Overtime", "", "", ""], ["Overheads", "", "", ""], ["Equipment", "", "", ""], ["Vehicle", "", "", ""], ["Travel", "", "", ""], ["Other", "", "", ""], ["Total", "", "", ""]]',
                        help_text="Estimated budget: external funds",
                        null=True,
                    ),
                ),
                (
                    "related_projects",
                    models.TextField(
                        blank=True,
                        help_text="Name related SPPs and the extent you have consulted with their project leaders",
                        null=True,
                    ),
                ),
            ],
            options={
                "verbose_name": "Project Plan",
                "verbose_name_plural": "Project Plans",
            },
        ),
        migrations.CreateModel(
            name="Publication",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=500)),
                (
                    "year",
                    models.PositiveIntegerField(
                        blank=True,
                        null=True,
                        validators=[django.core.validators.MinValueValidator(1800)],
                    ),
                ),
                (
                    "kind",
                    models.CharField(
                        choices=[("internal", "Internal"), ("external", "External")],
                        max_length=100,
                    ),
                ),
                (
                    "external_authors",
                    models.CharField(blank=True, max_length=1000, null=True),
                ),
                ("doc_link", models.CharField(blank=True, max_length=1500, null=True)),
                ("page_range", models.CharField(blank=True, max_length=100, null=True)),
                ("doi", models.CharField(blank=True, max_length=1000, null=True)),
                ("volume", models.CharField(blank=True, max_length=100, null=True)),
            ],
            options={
                "verbose_name": "Publication",
                "verbose_name_plural": "Publications",
            },
        ),
        migrations.CreateModel(
            name="StudentReport",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "progress_report",
                    models.TextField(
                        blank=True,
                        help_text="Report progress made this year in max. 150 words.",
                        null=True,
                    ),
                ),
                (
                    "year",
                    models.PositiveIntegerField(
                        default=2023,
                        editable=False,
                        help_text="The year on which this progress report reports on with four digits, e.g. 2014 for FY 2013/14.",
                    ),
                ),
                (
                    "document",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="student_report_details",
                        to="documents.projectdocument",
                    ),
                ),
                (
                    "report",
                    models.ForeignKey(
                        blank=True,
                        help_text="The annual report publishing this StudentReport",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="documents.annualreport",
                    ),
                ),
            ],
            options={
                "verbose_name": "Student Report",
                "verbose_name_plural": "Student Reports",
            },
        ),
    ]
