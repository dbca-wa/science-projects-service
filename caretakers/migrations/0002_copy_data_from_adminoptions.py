# Generated migration for copying caretaker data from adminoptions to caretakers
# NOTE: This migration is now a no-op because:
# 1. Data migration is handled by management command: migrate_caretaker_data
# 2. The adminoptions.Caretaker model will be deleted in a later migration
# 3. This migration is kept for historical purposes

from django.db import migrations


def noop_forward(apps, schema_editor):
    """
    No-op: Data migration is handled by management command.
    Run: python manage.py migrate_caretaker_data
    """
    pass


def noop_backward(apps, schema_editor):
    """
    No-op: Cannot reverse data migration.
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('caretakers', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            noop_forward,
            noop_backward,
        ),
    ]
