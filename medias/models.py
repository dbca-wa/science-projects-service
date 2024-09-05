# region IMPORTS =====================================================================================================

from django.db import models
from common.models import CommonModel
from django.db.models import UniqueConstraint
from django.core.validators import MinValueValidator, MaxValueValidator

# endregion ===========================================================================================================


# region AR MEDIA MODELS ======================================================================================================


class ProjectDocumentPDF(CommonModel):

    file = models.FileField(upload_to="project_documents/", null=True, blank=True)
    size = models.PositiveIntegerField(default=0)  # New size field
    document = models.OneToOneField(
        "documents.ProjectDocument",
        on_delete=models.CASCADE,
        related_name="pdf",
    )
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="pdfs",
    )

    def __str__(self) -> str:
        return f"PDF for {self.document.kind} - {self.project.title}"

    def save(self, *args, **kwargs):
        if self.file:
            self.size = self.file.size
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Project Document PDF"
        verbose_name_plural = "Project Document PDFs"


class AnnualReportMedia(CommonModel):
    """
    Model Images for Report Media
    """

    class MediaTypes(models.TextChoices):
        COVER = "cover", "Cover"
        REAR_COVER = "rear_cover", "Rear Cover"
        SDCHART = "sdchart", "Service Delivery Chart"
        SDCHAPTER = "service_delivery", "Service Delivery"
        RESEARCHCHAPTER = "research", "Research"
        PARTNERSHIPSCHAPTER = "partnerships", "Partnerships"
        COLLABORATIONSCHAPTER = "collaborations", "Collaborations"
        STUDENTPROJECTSCHAPTER = "student_projects", "Student Projects"
        PUBLICATIONSCHAPTER = "publications", "Publications"

    file = models.ImageField(upload_to="annual_reports/images/", null=True, blank=True)
    size = models.PositiveIntegerField(default=0)  # New size field
    kind = models.CharField(
        max_length=140,
        choices=MediaTypes.choices,
    )
    report = models.ForeignKey(
        "documents.AnnualReport",
        on_delete=models.CASCADE,
        related_name="media",
    )
    uploader = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="annual_report_media_uploaded",
    )

    def __str__(self) -> str:
        return f"({self.report.year}) {self.kind.capitalize()} Annual Report Media"

    def save(self, *args, **kwargs):
        if self.file:
            self.size = self.file.size
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Annual Report Image"
        verbose_name_plural = "Annual Report Images"
        # Ensures there is only one kind of media per report/year (cannot have two rear covers etc.)
        constraints = [
            UniqueConstraint(
                name="unique_media_per_kind_per_year",
                fields=["kind", "report"],
            )
        ]


class LegacyAnnualReportPDF(CommonModel):
    """
    PDF for Older Published Reports
    """

    file = models.FileField(
        upload_to="annual_reports/legacy/pdfs/", null=True, blank=True
    )
    size = models.PositiveIntegerField(default=0)  # New size field
    year = models.PositiveBigIntegerField(
        validators=[MinValueValidator(2005), MaxValueValidator(2019)]
    )
    creator = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="legacy_annual_report_pdf_generated",
    )

    def save(self, *args, **kwargs):
        if self.file:
            self.size = self.file.size
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"({self.year}) Annual Report PDF"

    class Meta:
        verbose_name = "Legacy Annual Report PDF"
        verbose_name_plural = "Legacy Annual Report PDFs"


class AnnualReportPDF(CommonModel):  #  The latest pdf for a given annual report
    """
    PDF for Report Media
    """

    file = models.FileField(upload_to="annual_reports/pdfs/", null=True, blank=True)
    size = models.PositiveIntegerField(default=0)  # New size field
    report = models.OneToOneField(
        "documents.AnnualReport",
        on_delete=models.CASCADE,
        related_name="pdf",
    )
    creator = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="annual_report_pdf_generated",
    )

    def save(self, *args, **kwargs):
        if self.file:
            self.size = self.file.size
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"({self.report.year}) Annual Report PDF"

    class Meta:
        verbose_name = "Annual Report PDF"
        verbose_name_plural = "Annual Report PDFs"


# endregion ===========================================================================================================


# region PROJECT MODELS ======================================================================================================


class AECEndorsementPDF(CommonModel):  #  The latest pdf for a given annual report
    """
    PDF for AEC Endorsements
    """

    file = models.FileField(upload_to="aec_endorsements/", null=True, blank=True)
    size = models.PositiveIntegerField(default=0)  # New size field
    endorsement = models.OneToOneField(
        "documents.Endorsement",
        on_delete=models.CASCADE,
        related_name="aec_pdf",
    )
    creator = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="aec_endorsement_pdfs_uploaded",
    )

    def __str__(self) -> str:
        return f" AEC PDF ({self.endorsement})"

    def save(self, *args, **kwargs):
        if self.file:
            self.size = self.file.size
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "AEC PDF"
        verbose_name_plural = "AEC PDFs"


class ProjectPhoto(CommonModel):
    """
    Model Definition for Project Photos
    """

    file = models.ImageField(upload_to="projects/", blank=True, null=True)
    project = models.OneToOneField(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="image",
    )
    uploader = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="project_photos_uploaded",
    )
    size = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        if self.file:
            self.size = self.file.size
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return "Project Photo File"

    class Meta:
        verbose_name = "Project Image"
        verbose_name_plural = "Project Images"


class ProjectPlanMethodologyPhoto(CommonModel):
    """
    Model Definition for Project Plan Methodology Photos
    """

    file = models.ImageField(upload_to="methodology_images/", blank=True, null=True)
    size = models.PositiveIntegerField(default=0)
    project_plan = models.OneToOneField(
        "documents.ProjectPlan",
        on_delete=models.CASCADE,
        related_name="methodology_image",
    )
    uploader = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="methodology_photos_uploaded",
    )

    def __str__(self) -> str:
        return f"Methodology Image File: {self.file}"

    def save(self, *args, **kwargs):
        if self.file:
            self.size = self.file.size
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Methodology Image File"
        verbose_name_plural = "Methodology Image Files"


# endregion ===========================================================================================================


# region Business Area / Agency Photos Models ======================================================================================================


class BusinessAreaPhoto(CommonModel):
    """
    Model Definition for BusinessArea Photos
    """

    file = models.ImageField(upload_to="business_areas/", blank=True, null=True)
    size = models.PositiveIntegerField(default=0)  # New size field

    business_area = models.OneToOneField(
        "agencies.BusinessArea",
        on_delete=models.CASCADE,
        related_name="image",
    )
    uploader = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="business_area_photos_uploaded",
    )

    def __str__(self) -> str:
        return "Business Area Photo File"

    def save(self, *args, **kwargs):
        if self.file:
            self.size = self.file.size
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Business Area Image"
        verbose_name_plural = "Business Area Images"


class AgencyImage(CommonModel):
    """
    Model Definition for Agency Photos (DBCA's image)
    """

    file = models.ImageField(upload_to="agencies/")
    size = models.PositiveIntegerField(default=0)  # New size field
    agency = models.OneToOneField(
        "agencies.Agency",
        on_delete=models.CASCADE,
        related_name="image",
    )

    def __str__(self) -> str:
        return "Agency Photo File"

    def save(self, *args, **kwargs):
        if self.file:
            self.size = self.file.size
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Agency Image"
        verbose_name_plural = "Agency Images"


# endregion ===========================================================================================================


# region User Avatar Model ======================================================================================================


class UserAvatar(CommonModel):
    """
    Model Definition for User Photos
    """

    file = models.ImageField(upload_to="user_avatars/", blank=True, null=True)
    size = models.PositiveIntegerField(default=0)
    user = models.OneToOneField(
        "users.User",
        on_delete=models.CASCADE,
        related_name="avatar",
    )

    def __str__(self) -> str:
        return f"User: {self.user} | {self.file.name}"

    def save(self, *args, **kwargs):
        if self.file:
            self.size = self.file.size
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "User Avatar Image"
        verbose_name_plural = "User Avatar Images"


# endregion ===========================================================================================================
