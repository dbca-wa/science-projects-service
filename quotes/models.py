from django.db import models

from common.models import CommonModel


# DONE
class Quote(CommonModel):
    """Definition for Quotes"""

    text = models.TextField(unique=True)
    author = models.CharField(max_length=50)

    def __str__(self) -> str:
        return f"{self.pk} | {self.text}"

    class Meta:
        verbose_name = "Quote"
        verbose_name_plural = "Quotes"
