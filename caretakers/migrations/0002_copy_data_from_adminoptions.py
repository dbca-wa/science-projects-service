# Generated migration for copying caretaker data from adminoptions to caretakers

from django.db import migrations


def copy_caretaker_data_forward(apps, schema_editor):
    """
    Copy all caretaker data from adminoptions_caretaker to caretakers_caretaker.
    This is idempotent - can be run multiple times safely.
    """
    # Get the old and new models
    OldCaretaker = apps.get_model('adminoptions', 'Caretaker')
    NewCaretaker = apps.get_model('caretakers', 'Caretaker')
    
    # Get all records from old table
    old_caretakers = OldCaretaker.objects.all()
    
    print(f"\n=== Copying {old_caretakers.count()} caretaker records ===")
    
    copied_count = 0
    skipped_count = 0
    
    for old_caretaker in old_caretakers:
        # Check if this record already exists in new table
        # Use unique constraint: user + caretaker combination
        existing = NewCaretaker.objects.filter(
            user_id=old_caretaker.user_id,
            caretaker_id=old_caretaker.caretaker_id,
        ).first()
        
        if existing:
            # Update existing record to ensure data is current
            existing.end_date = old_caretaker.end_date
            existing.reason = old_caretaker.reason
            existing.notes = old_caretaker.notes
            existing.created_at = old_caretaker.created_at
            existing.updated_at = old_caretaker.updated_at
            existing.save()
            skipped_count += 1
        else:
            # Create new record
            NewCaretaker.objects.create(
                id=old_caretaker.id,  # Preserve original ID
                user_id=old_caretaker.user_id,
                caretaker_id=old_caretaker.caretaker_id,
                end_date=old_caretaker.end_date,
                reason=old_caretaker.reason,
                notes=old_caretaker.notes,
                created_at=old_caretaker.created_at,
                updated_at=old_caretaker.updated_at,
            )
            copied_count += 1
    
    print(f"✓ Copied {copied_count} new records")
    print(f"✓ Updated {skipped_count} existing records")
    print(f"✓ Total records in new table: {NewCaretaker.objects.count()}")


def copy_caretaker_data_backward(apps, schema_editor):
    """
    Reverse migration - copy data back from caretakers to adminoptions.
    This allows safe rollback if needed.
    """
    OldCaretaker = apps.get_model('adminoptions', 'Caretaker')
    NewCaretaker = apps.get_model('caretakers', 'Caretaker')
    
    new_caretakers = NewCaretaker.objects.all()
    
    print(f"\n=== Rolling back {new_caretakers.count()} caretaker records ===")
    
    copied_count = 0
    skipped_count = 0
    
    for new_caretaker in new_caretakers:
        existing = OldCaretaker.objects.filter(
            user_id=new_caretaker.user_id,
            caretaker_id=new_caretaker.caretaker_id,
        ).first()
        
        if existing:
            existing.end_date = new_caretaker.end_date
            existing.reason = new_caretaker.reason
            existing.notes = new_caretaker.notes
            existing.created_at = new_caretaker.created_at
            existing.updated_at = new_caretaker.updated_at
            existing.save()
            skipped_count += 1
        else:
            OldCaretaker.objects.create(
                id=new_caretaker.id,
                user_id=new_caretaker.user_id,
                caretaker_id=new_caretaker.caretaker_id,
                end_date=new_caretaker.end_date,
                reason=new_caretaker.reason,
                notes=new_caretaker.notes,
                created_at=new_caretaker.created_at,
                updated_at=new_caretaker.updated_at,
            )
            copied_count += 1
    
    print(f"✓ Rolled back {copied_count} records")
    print(f"✓ Updated {skipped_count} existing records")


class Migration(migrations.Migration):

    dependencies = [
        ('caretakers', '0001_initial'),
        ('adminoptions', '0001_initial'),  # Update this to the latest adminoptions migration
    ]

    operations = [
        migrations.RunPython(
            copy_caretaker_data_forward,
            copy_caretaker_data_backward,
        ),
    ]
