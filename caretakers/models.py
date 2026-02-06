# region Imports
from django.db import models
from django.core.cache import cache
from common.models import CommonModel

# endregion


class Caretaker(CommonModel):
    """
    Represents a caretaker relationship where one user manages
    projects/documents on behalf of another user.
    """
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="caretakers",
        help_text="The user being caretaken for"
    )
    
    caretaker = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="caretaking_for",
        help_text="The user acting as caretaker"
    )
    
    end_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When caretaker relationship expires"
    )
    
    reason = models.TextField(
        blank=True,
        null=True,
        help_text="Reason for caretaker request"
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes"
    )
    
    class Meta:
        verbose_name = "Caretaker"
        verbose_name_plural = "Caretakers"
        unique_together = [["user", "caretaker"]]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["caretaker"]),
            models.Index(fields=["end_date"]),
        ]

    
    def __str__(self):
        return f"{self.caretaker} caretaking for {self.user}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._clear_cache()
    
    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self._clear_cache()
    
    def _clear_cache(self):
        """Clear cache for both users"""
        cache.delete(f"caretakers_{self.user.pk}")
        cache.delete(f"caretaking_{self.user.pk}")
        cache.delete(f"caretakers_{self.caretaker.pk}")
        cache.delete(f"caretaking_{self.caretaker.pk}")
