"""
Django signals for the agencies app.

Handles automatic updates when Affiliation names change to ensure
data consistency across related models.
"""

from django.conf import settings
from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import Affiliation


@receiver(pre_save, sender=Affiliation)
def update_project_affiliations_on_name_change(sender, instance, **kwargs):
    """
    When an Affiliation name is changed, update all StudentProjectDetails
    and ExternalProjectDetails that reference the old name.

    This ensures that when an affiliation is renamed (e.g., adding a comma),
    all projects using that affiliation are automatically updated.
    """
    # Only proceed if this is an update (not a new instance)
    if instance.pk is None:
        return

    try:
        # Get the old instance from the database
        old_instance = Affiliation.objects.get(pk=instance.pk)
        old_name = old_instance.name
        new_name = instance.name

        # Only proceed if the name actually changed
        if old_name == new_name:
            return

        # Import here to avoid circular imports
        from projects.models import ExternalProjectDetails, StudentProjectDetails

        updated_student_count = 0
        updated_external_count = 0

        # Update StudentProjectDetails
        student_projects = StudentProjectDetails.objects.filter(
            organisation__icontains=old_name
        )

        for student_project in student_projects:
            if student_project.organisation:
                # Split by semicolon, update matching names, rejoin
                affiliations = [
                    a.strip() for a in student_project.organisation.split("; ")
                ]
                updated_affiliations = [
                    new_name if a == old_name else a for a in affiliations
                ]
                student_project.organisation = "; ".join(updated_affiliations)
                student_project.save()
                updated_student_count += 1

        # Update ExternalProjectDetails
        external_projects = ExternalProjectDetails.objects.filter(
            collaboration_with__icontains=old_name
        )

        for external_project in external_projects:
            if external_project.collaboration_with:
                # Split by semicolon, update matching names, rejoin
                affiliations = [
                    a.strip() for a in external_project.collaboration_with.split("; ")
                ]
                updated_affiliations = [
                    new_name if a == old_name else a for a in affiliations
                ]
                external_project.collaboration_with = "; ".join(updated_affiliations)
                external_project.save()
                updated_external_count += 1

        # Log the updates
        if updated_student_count > 0 or updated_external_count > 0:
            settings.LOGGER.info(
                f"Affiliation name changed from '{old_name}' to '{new_name}'. "
                f"Updated {updated_student_count} student project(s) and "
                f"{updated_external_count} external project(s)."
            )

    except Affiliation.DoesNotExist:
        # This shouldn't happen, but handle gracefully
        pass
    except Exception as e:
        settings.LOGGER.error(f"Error updating project affiliations: {str(e)}")
