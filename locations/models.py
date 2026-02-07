from django.db import models

from common.models import CommonModel


class Area(CommonModel):
    """
    Model Definition for Areas
    """

    class AreaTypeChoices(models.TextChoices):
        AREA_TYPE_DBCA_REGION = "dbcaregion", "DBCA Region"  # Changed from DPAW_REGION
        AREA_TYPE_DBCA_DISTRICT = (
            "dbcadistrict",
            "DBCA District",
        )  # Changed from DPAW_DISTRICT
        AREA_TYPE_IBRA_REGION = (
            "ibra",
            "IBRA Region (Interim Biogeographic Regionalisation for Australia)",
        )
        AREA_TYPE_IMCRA_REGION = (
            "imcra",
            "IMCRA Region (Integrated Marine and Coastal Regionalisation of Australia)",
        )
        AREA_TYPE_NRM_REGION = "nrm", "Natural Resource Management Region"

    name = models.CharField(
        max_length=150,
        help_text="A human-readable, short but descriptive name.",
    )

    area_type = models.CharField(
        max_length=25,
        verbose_name="Area Type",
        choices=AreaTypeChoices.choices,
    )

    class Meta:
        verbose_name = "Area"
        verbose_name_plural = "Areas"
        unique_together = (("name", "area_type"),)

    def __str__(self) -> str:
        return self.name
