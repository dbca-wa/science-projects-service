from django.db import models
from common.models import CommonModel


class ProjectCategory(CommonModel):
    """
    Science, Student, External or Core Function Project Category
    """

    class CategoryKindChoices(models.TextChoices):
        SCIENCE = "science", "Science"
        STUDENT = "student", "Student"
        EXTERNAL = "external", "External"
        COREFUNCTION = "core_function", "Core Function"

    name = models.CharField(max_length=50)
    kind = models.CharField(
        max_length=15,
        choices=CategoryKindChoices.choices,
    )

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Project Category"
        verbose_name_plural = "Project Categories"
