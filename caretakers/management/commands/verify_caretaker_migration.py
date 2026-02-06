"""
Management command to verify caretaker data migration.

Usage:
    python manage.py verify_caretaker_migration
    python manage.py verify_caretaker_migration --fix  # Fix any discrepancies
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from adminoptions.models import Caretaker as OldCaretaker
from caretakers.models import Caretaker as NewCaretaker


class Command(BaseCommand):
    help = 'Verify caretaker data migration from adminoptions to caretakers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Fix any discrepancies found',
        )

    def handle(self, *args, **options):
        fix_mode = options['fix']
        
        self.stdout.write(self.style.MIGRATE_HEADING(
            '\n=== Caretaker Migration Verification ==='
        ))
        
        # Count records
        old_count = OldCaretaker.objects.count()
        new_count = NewCaretaker.objects.count()
        
        self.stdout.write(f'\nOld table (adminoptions_caretaker): {old_count} records')
        self.stdout.write(f'New table (caretakers_caretaker): {new_count} records')
        
        if old_count == 0:
            self.stdout.write(self.style.WARNING(
                '\n⚠ Old table is empty - nothing to verify'
            ))
            return
        
        # Check for missing records
        missing_in_new = []
        data_mismatches = []
        
        for old_caretaker in OldCaretaker.objects.all():
            try:
                new_caretaker = NewCaretaker.objects.get(
                    user_id=old_caretaker.user_id,
                    caretaker_id=old_caretaker.caretaker_id,
                )
                
                # Verify data matches
                mismatches = []
                if new_caretaker.reason != old_caretaker.reason:
                    mismatches.append(f"reason: '{old_caretaker.reason}' != '{new_caretaker.reason}'")
                if new_caretaker.notes != old_caretaker.notes:
                    mismatches.append(f"notes: '{old_caretaker.notes}' != '{new_caretaker.notes}'")
                if new_caretaker.end_date != old_caretaker.end_date:
                    mismatches.append(f"end_date: {old_caretaker.end_date} != {new_caretaker.end_date}")
                
                if mismatches:
                    data_mismatches.append({
                        'old': old_caretaker,
                        'new': new_caretaker,
                        'mismatches': mismatches
                    })
                    
            except NewCaretaker.DoesNotExist:
                missing_in_new.append(old_caretaker)
        
        # Check for extra records in new table
        extra_in_new = []
        for new_caretaker in NewCaretaker.objects.all():
            if not OldCaretaker.objects.filter(
                user_id=new_caretaker.user_id,
                caretaker_id=new_caretaker.caretaker_id,
            ).exists():
                extra_in_new.append(new_caretaker)
        
        # Report findings
        self.stdout.write('\n' + '='*60)
        
        if not missing_in_new and not data_mismatches and not extra_in_new:
            self.stdout.write(self.style.SUCCESS(
                '\n✓ Migration verified successfully!'
            ))
            self.stdout.write(self.style.SUCCESS(
                f'✓ All {old_count} records match perfectly'
            ))
            return
        
        # Report issues
        has_issues = False
        
        if missing_in_new:
            has_issues = True
            self.stdout.write(self.style.ERROR(
                f'\n✗ {len(missing_in_new)} records missing in new table:'
            ))
            for caretaker in missing_in_new[:5]:  # Show first 5
                self.stdout.write(f'  - ID {caretaker.id}: {caretaker.user} -> {caretaker.caretaker}')
            if len(missing_in_new) > 5:
                self.stdout.write(f'  ... and {len(missing_in_new) - 5} more')
        
        if data_mismatches:
            has_issues = True
            self.stdout.write(self.style.WARNING(
                f'\n⚠ {len(data_mismatches)} records have data mismatches:'
            ))
            for mismatch in data_mismatches[:5]:  # Show first 5
                old = mismatch['old']
                self.stdout.write(f'  - ID {old.id}: {old.user} -> {old.caretaker}')
                for diff in mismatch['mismatches']:
                    self.stdout.write(f'    {diff}')
            if len(data_mismatches) > 5:
                self.stdout.write(f'  ... and {len(data_mismatches) - 5} more')
        
        if extra_in_new:
            has_issues = True
            self.stdout.write(self.style.WARNING(
                f'\n⚠ {len(extra_in_new)} extra records in new table (not in old):'
            ))
            for caretaker in extra_in_new[:5]:  # Show first 5
                self.stdout.write(f'  - ID {caretaker.id}: {caretaker.user} -> {caretaker.caretaker}')
            if len(extra_in_new) > 5:
                self.stdout.write(f'  ... and {len(extra_in_new) - 5} more')
        
        # Fix mode
        if fix_mode and has_issues:
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.MIGRATE_HEADING('\n=== Fixing Issues ==='))
            
            with transaction.atomic():
                fixed_count = 0
                
                # Copy missing records
                for old_caretaker in missing_in_new:
                    NewCaretaker.objects.create(
                        id=old_caretaker.id,
                        user_id=old_caretaker.user_id,
                        caretaker_id=old_caretaker.caretaker_id,
                        end_date=old_caretaker.end_date,
                        reason=old_caretaker.reason,
                        notes=old_caretaker.notes,
                        created_at=old_caretaker.created_at,
                        updated_at=old_caretaker.updated_at,
                    )
                    fixed_count += 1
                
                # Update mismatched records
                for mismatch in data_mismatches:
                    old = mismatch['old']
                    new = mismatch['new']
                    new.reason = old.reason
                    new.notes = old.notes
                    new.end_date = old.end_date
                    new.created_at = old.created_at
                    new.updated_at = old.updated_at
                    new.save()
                    fixed_count += 1
                
                self.stdout.write(self.style.SUCCESS(
                    f'\n✓ Fixed {fixed_count} issues'
                ))
        
        elif has_issues:
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.WARNING(
                '\nRun with --fix flag to automatically fix these issues'
            ))
            self.stdout.write('Example: python manage.py verify_caretaker_migration --fix')
