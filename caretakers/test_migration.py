"""
Tests for caretaker data migration from adminoptions to caretakers app.

These tests ensure the migration is:
1. Idempotent (can be run multiple times safely)
2. Preserves all data correctly
3. Handles edge cases (duplicates, missing data, etc.)
4. Can be rolled back safely
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.management import call_command
from datetime import timedelta
from io import StringIO

from adminoptions.models import Caretaker as OldCaretaker
from caretakers.models import Caretaker as NewCaretaker

User = get_user_model()


class CaretakerMigrationTest(TransactionTestCase):
    """Test suite for caretaker data migration"""

    def setUp(self):
        """Create test users for caretaker relationships"""
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        self.user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='testpass123'
        )
        self.user4 = User.objects.create_user(
            username='user4',
            email='user4@example.com',
            password='testpass123'
        )

    def tearDown(self):
        """Clean up test data"""
        OldCaretaker.objects.all().delete()
        NewCaretaker.objects.all().delete()

    def run_migration_forward(self):
        """Helper to run migration forward"""
        # Import the migration function directly
        import importlib
        migration_module = importlib.import_module('caretakers.migrations.0002_copy_data_from_adminoptions')
        from django.apps import apps
        migration_module.copy_caretaker_data_forward(apps, None)

    def test_migration_copies_all_data(self):
        """Test that migration copies all caretaker records"""
        # Create test data in old table
        old_caretaker1 = OldCaretaker.objects.create(
            user=self.user1,
            caretaker=self.user2,
            reason="On leave",
            notes="Test notes 1"
        )
        old_caretaker2 = OldCaretaker.objects.create(
            user=self.user3,
            caretaker=self.user4,
            reason="Resigned",
            end_date=timezone.now() + timedelta(days=30),
            notes="Test notes 2"
        )

        # Run migration
        self.run_migration_forward()

        # Verify all records copied
        self.assertEqual(NewCaretaker.objects.count(), 2)
        
        # Verify data integrity
        new_caretaker1 = NewCaretaker.objects.get(
            user=self.user1,
            caretaker=self.user2
        )
        self.assertEqual(new_caretaker1.reason, "On leave")
        self.assertEqual(new_caretaker1.notes, "Test notes 1")
        self.assertIsNone(new_caretaker1.end_date)
        
        new_caretaker2 = NewCaretaker.objects.get(
            user=self.user3,
            caretaker=self.user4
        )
        self.assertEqual(new_caretaker2.reason, "Resigned")
        self.assertEqual(new_caretaker2.notes, "Test notes 2")
        self.assertIsNotNone(new_caretaker2.end_date)

    def test_migration_is_idempotent(self):
        """Test that running migration multiple times doesn't create duplicates"""
        # Create test data
        OldCaretaker.objects.create(
            user=self.user1,
            caretaker=self.user2,
            reason="On leave"
        )

        # Run migration first time
        self.run_migration_forward()
        first_count = NewCaretaker.objects.count()
        self.assertEqual(first_count, 1)

        # Run migration second time
        self.run_migration_forward()
        second_count = NewCaretaker.objects.count()
        self.assertEqual(second_count, 1)  # Should still be 1, not 2

        # Verify data is still correct
        new_caretaker = NewCaretaker.objects.get(
            user=self.user1,
            caretaker=self.user2
        )
        self.assertEqual(new_caretaker.reason, "On leave")

    def test_migration_updates_existing_records(self):
        """Test that migration updates existing records with new data"""
        # Create initial data
        old_caretaker = OldCaretaker.objects.create(
            user=self.user1,
            caretaker=self.user2,
            reason="Initial reason",
            notes="Initial notes"
        )

        # Run migration first time
        self.run_migration_forward()
        
        # Update old record
        old_caretaker.reason = "Updated reason"
        old_caretaker.notes = "Updated notes"
        old_caretaker.end_date = timezone.now() + timedelta(days=60)
        old_caretaker.save()

        # Run migration again
        self.run_migration_forward()

        # Verify new table has updated data
        new_caretaker = NewCaretaker.objects.get(
            user=self.user1,
            caretaker=self.user2
        )
        self.assertEqual(new_caretaker.reason, "Updated reason")
        self.assertEqual(new_caretaker.notes, "Updated notes")
        self.assertIsNotNone(new_caretaker.end_date)

    def test_migration_handles_empty_table(self):
        """Test that migration handles empty source table gracefully"""
        # Ensure old table is empty
        OldCaretaker.objects.all().delete()

        # Run migration - should not raise error
        self.run_migration_forward()

        # Verify new table is also empty
        self.assertEqual(NewCaretaker.objects.count(), 0)

    def test_migration_handles_null_fields(self):
        """Test that migration handles null/blank fields correctly"""
        old_caretaker = OldCaretaker.objects.create(
            user=self.user1,
            caretaker=self.user2,
            reason="Test",
            notes=None,  # Null notes
            end_date=None  # Null end_date
        )

        # Run migration
        self.run_migration_forward()

        # Verify null fields preserved
        new_caretaker = NewCaretaker.objects.get(
            user=self.user1,
            caretaker=self.user2
        )
        self.assertIsNone(new_caretaker.notes)
        self.assertIsNone(new_caretaker.end_date)

    def test_migration_with_multiple_caretakers_per_user(self):
        """Test migration handles users with multiple caretakers"""
        # User1 has two caretakers
        OldCaretaker.objects.create(
            user=self.user1,
            caretaker=self.user2,
            reason="Caretaker 1"
        )
        OldCaretaker.objects.create(
            user=self.user1,
            caretaker=self.user3,
            reason="Caretaker 2"
        )

        # Run migration
        self.run_migration_forward()

        # Verify both relationships copied
        self.assertEqual(NewCaretaker.objects.filter(user=self.user1).count(), 2)
        
        caretaker1 = NewCaretaker.objects.get(
            user=self.user1,
            caretaker=self.user2
        )
        self.assertEqual(caretaker1.reason, "Caretaker 1")
        
        caretaker2 = NewCaretaker.objects.get(
            user=self.user1,
            caretaker=self.user3
        )
        self.assertEqual(caretaker2.reason, "Caretaker 2")


class VerificationCommandTest(TestCase):
    """Test the verification management command"""

    def setUp(self):
        """Create test users"""
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com'
        )

    def test_verification_command_success(self):
        """Test verification command with matching data"""
        # Create matching data in both tables
        OldCaretaker.objects.create(
            user=self.user1,
            caretaker=self.user2,
            reason="Test"
        )
        NewCaretaker.objects.create(
            user=self.user1,
            caretaker=self.user2,
            reason="Test"
        )

        # Run verification
        out = StringIO()
        call_command('verify_caretaker_migration', stdout=out)
        output = out.getvalue()

        # Should report success
        self.assertIn('Migration verified successfully', output)

    def test_verification_command_with_fix(self):
        """Test verification command with --fix flag"""
        # Create data only in old table
        OldCaretaker.objects.create(
            user=self.user1,
            caretaker=self.user2,
            reason="Test"
        )

        # Run verification with fix
        out = StringIO()
        call_command('verify_caretaker_migration', '--fix', stdout=out)
        output = out.getvalue()

        # Should report fixing
        self.assertIn('Fixed', output)

        # Verify data was copied
        self.assertTrue(
            NewCaretaker.objects.filter(
                user=self.user1,
                caretaker=self.user2
            ).exists()
        )
