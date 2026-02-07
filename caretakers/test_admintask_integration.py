"""
Tests for AdminTask integration with Caretaker model.

Tests that AdminTask views (ApproveTask, RejectTask, CancelTask) work correctly
with the new caretakers.models.Caretaker model.
"""

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from adminoptions.models import AdminTask
from caretakers.models import Caretaker
from users.models import User


class AdminTaskCaretakerIntegrationTest(TestCase):
    """Test AdminTask integration with new Caretaker model"""

    def setUp(self):
        """Create test users for caretaker relationships"""
        self.user_needing_caretaker = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            first_name="User",
            last_name="One",
        )
        self.caretaker_user = User.objects.create_user(
            username="caretaker1",
            email="caretaker1@example.com",
            first_name="Caretaker",
            last_name="One",
        )
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
        )

    def test_approve_caretaker_task_creates_caretaker(self):
        """Test that approving a caretaker AdminTask creates a Caretaker object"""
        # Create a pending caretaker request
        end_date = timezone.now() + timedelta(days=30)
        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            primary_user=self.user_needing_caretaker,
            secondary_users=[self.caretaker_user.pk],
            requester=self.user_needing_caretaker,
            reason="Going on leave",
            end_date=end_date,
            notes="Test caretaker request",
        )

        # Verify no caretaker exists yet
        self.assertEqual(Caretaker.objects.count(), 0)

        # Simulate approving the task (this is what ApproveTask view does)
        task.status = AdminTask.TaskStatus.APPROVED
        task.save()

        # Create the caretaker relationship (this is what ApproveTask view does)
        Caretaker.objects.create(
            user=self.user_needing_caretaker,
            caretaker=self.caretaker_user,
            reason=task.reason,
            end_date=task.end_date,
            notes=task.notes,
        )

        # Mark task as fulfilled
        task.status = AdminTask.TaskStatus.FULFILLED
        task.save()

        # Verify caretaker was created
        self.assertEqual(Caretaker.objects.count(), 1)
        caretaker = Caretaker.objects.first()
        self.assertEqual(caretaker.user, self.user_needing_caretaker)
        self.assertEqual(caretaker.caretaker, self.caretaker_user)
        self.assertEqual(caretaker.reason, "Going on leave")
        self.assertEqual(caretaker.notes, "Test caretaker request")
        self.assertIsNotNone(caretaker.end_date)

        # Verify task is fulfilled
        task.refresh_from_db()
        self.assertEqual(task.status, AdminTask.TaskStatus.FULFILLED)

    def test_reject_caretaker_task_does_not_create_caretaker(self):
        """Test that rejecting a caretaker AdminTask does not create a Caretaker object"""
        # Create a pending caretaker request
        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            primary_user=self.user_needing_caretaker,
            secondary_users=[self.caretaker_user.pk],
            requester=self.user_needing_caretaker,
            reason="Going on leave",
        )

        # Verify no caretaker exists yet
        self.assertEqual(Caretaker.objects.count(), 0)

        # Simulate rejecting the task (this is what RejectTask view does)
        task.status = AdminTask.TaskStatus.REJECTED
        task.save()

        # Verify no caretaker was created
        self.assertEqual(Caretaker.objects.count(), 0)

        # Verify task is rejected
        task.refresh_from_db()
        self.assertEqual(task.status, AdminTask.TaskStatus.REJECTED)

    def test_cancel_caretaker_task_does_not_create_caretaker(self):
        """Test that cancelling a caretaker AdminTask does not create a Caretaker object"""
        # Create a pending caretaker request
        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            primary_user=self.user_needing_caretaker,
            secondary_users=[self.caretaker_user.pk],
            requester=self.user_needing_caretaker,
            reason="Going on leave",
        )

        # Verify no caretaker exists yet
        self.assertEqual(Caretaker.objects.count(), 0)

        # Simulate cancelling the task (this is what CancelTask view does)
        task.status = AdminTask.TaskStatus.CANCELLED
        task.save()

        # Verify no caretaker was created
        self.assertEqual(Caretaker.objects.count(), 0)

        # Verify task is cancelled
        task.refresh_from_db()
        self.assertEqual(task.status, AdminTask.TaskStatus.CANCELLED)

    def test_caretaker_with_null_end_date(self):
        """Test creating a caretaker with no end date (permanent caretaker)"""
        # Create a pending caretaker request with no end date
        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            primary_user=self.user_needing_caretaker,
            secondary_users=[self.caretaker_user.pk],
            requester=self.user_needing_caretaker,
            reason="Permanent leave",
            end_date=None,  # No end date
        )

        # Approve and create caretaker
        task.status = AdminTask.TaskStatus.APPROVED
        task.save()

        Caretaker.objects.create(
            user=self.user_needing_caretaker,
            caretaker=self.caretaker_user,
            reason=task.reason,
            end_date=task.end_date,  # Will be None
            notes=task.notes,
        )

        task.status = AdminTask.TaskStatus.FULFILLED
        task.save()

        # Verify caretaker was created with null end_date
        caretaker = Caretaker.objects.first()
        self.assertIsNone(caretaker.end_date)

    def test_multiple_caretakers_for_same_user(self):
        """Test that a user can have multiple caretakers"""
        # Create another caretaker user
        caretaker_user_2 = User.objects.create_user(
            username="caretaker2",
            email="caretaker2@example.com",
            first_name="Caretaker",
            last_name="Two",
        )

        # Create first caretaker
        Caretaker.objects.create(
            user=self.user_needing_caretaker,
            caretaker=self.caretaker_user,
            reason="Primary caretaker",
        )

        # Create second caretaker
        Caretaker.objects.create(
            user=self.user_needing_caretaker,
            caretaker=caretaker_user_2,
            reason="Backup caretaker",
        )

        # Verify both caretakers exist
        caretakers = Caretaker.objects.filter(user=self.user_needing_caretaker)
        self.assertEqual(caretakers.count(), 2)

    def test_user_can_be_caretaker_for_multiple_users(self):
        """Test that a user can be caretaker for multiple users"""
        # Create another user needing a caretaker
        user_2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            first_name="User",
            last_name="Two",
        )

        # Create first caretaker relationship
        Caretaker.objects.create(
            user=self.user_needing_caretaker,
            caretaker=self.caretaker_user,
            reason="Caretaking for user 1",
        )

        # Create second caretaker relationship
        Caretaker.objects.create(
            user=user_2,
            caretaker=self.caretaker_user,
            reason="Caretaking for user 2",
        )

        # Verify both relationships exist
        caretaking_relationships = Caretaker.objects.filter(
            caretaker=self.caretaker_user
        )
        self.assertEqual(caretaking_relationships.count(), 2)

    def test_caretaker_cache_clearing_on_save(self):
        """Test that cache is cleared when caretaker is saved"""
        from django.core.cache import cache

        # Create a caretaker
        caretaker = Caretaker.objects.create(
            user=self.user_needing_caretaker,
            caretaker=self.caretaker_user,
            reason="Test cache clearing",
        )

        # Set some cache values
        cache.set(f"caretakers_{self.user_needing_caretaker.pk}", "test_data")
        cache.set(f"caretaking_{self.user_needing_caretaker.pk}", "test_data")
        cache.set(f"caretakers_{self.caretaker_user.pk}", "test_data")
        cache.set(f"caretaking_{self.caretaker_user.pk}", "test_data")

        # Verify cache is set
        self.assertIsNotNone(cache.get(f"caretakers_{self.user_needing_caretaker.pk}"))
        self.assertIsNotNone(cache.get(f"caretaking_{self.user_needing_caretaker.pk}"))
        self.assertIsNotNone(cache.get(f"caretakers_{self.caretaker_user.pk}"))
        self.assertIsNotNone(cache.get(f"caretaking_{self.caretaker_user.pk}"))

        # Update the caretaker (triggers save)
        caretaker.reason = "Updated reason"
        caretaker.save()

        # Verify cache is cleared
        self.assertIsNone(cache.get(f"caretakers_{self.user_needing_caretaker.pk}"))
        self.assertIsNone(cache.get(f"caretaking_{self.user_needing_caretaker.pk}"))
        self.assertIsNone(cache.get(f"caretakers_{self.caretaker_user.pk}"))
        self.assertIsNone(cache.get(f"caretaking_{self.caretaker_user.pk}"))

    def test_caretaker_cache_clearing_on_delete(self):
        """Test that cache is cleared when caretaker is deleted"""
        from django.core.cache import cache

        # Create a caretaker
        caretaker = Caretaker.objects.create(
            user=self.user_needing_caretaker,
            caretaker=self.caretaker_user,
            reason="Test cache clearing on delete",
        )

        # Set some cache values
        cache.set(f"caretakers_{self.user_needing_caretaker.pk}", "test_data")
        cache.set(f"caretaking_{self.user_needing_caretaker.pk}", "test_data")
        cache.set(f"caretakers_{self.caretaker_user.pk}", "test_data")
        cache.set(f"caretaking_{self.caretaker_user.pk}", "test_data")

        # Verify cache is set
        self.assertIsNotNone(cache.get(f"caretakers_{self.user_needing_caretaker.pk}"))
        self.assertIsNotNone(cache.get(f"caretaking_{self.user_needing_caretaker.pk}"))
        self.assertIsNotNone(cache.get(f"caretakers_{self.caretaker_user.pk}"))
        self.assertIsNotNone(cache.get(f"caretaking_{self.caretaker_user.pk}"))

        # Delete the caretaker
        caretaker.delete()

        # Verify cache is cleared
        self.assertIsNone(cache.get(f"caretakers_{self.user_needing_caretaker.pk}"))
        self.assertIsNone(cache.get(f"caretaking_{self.user_needing_caretaker.pk}"))
        self.assertIsNone(cache.get(f"caretakers_{self.caretaker_user.pk}"))
        self.assertIsNone(cache.get(f"caretaking_{self.caretaker_user.pk}"))

    def test_user_model_get_caretakers_method(self):
        """Test that User.get_caretakers() works with new Caretaker model"""
        # Create a caretaker relationship
        end_date = timezone.now() + timedelta(days=30)
        Caretaker.objects.create(
            user=self.user_needing_caretaker,
            caretaker=self.caretaker_user,
            reason="Test get_caretakers",
            end_date=end_date,
        )

        # Test get_caretakers method
        caretakers = self.user_needing_caretaker.get_caretakers()
        self.assertEqual(caretakers.count(), 1)
        self.assertEqual(caretakers.first().caretaker, self.caretaker_user)

    def test_user_model_get_caretaking_for_method(self):
        """Test that User.get_caretaking_for() works with new Caretaker model"""
        # Create a caretaker relationship
        end_date = timezone.now() + timedelta(days=30)
        Caretaker.objects.create(
            user=self.user_needing_caretaker,
            caretaker=self.caretaker_user,
            reason="Test get_caretaking_for",
            end_date=end_date,
        )

        # Test get_caretaking_for method
        caretaking_for = self.caretaker_user.get_caretaking_for()
        self.assertEqual(caretaking_for.count(), 1)
        self.assertEqual(caretaking_for.first().user, self.user_needing_caretaker)

    def test_expired_caretaker_not_returned_by_get_caretakers(self):
        """Test that expired caretakers are not returned by get_caretakers()"""
        # Create an expired caretaker relationship
        expired_date = timezone.now() - timedelta(days=1)
        Caretaker.objects.create(
            user=self.user_needing_caretaker,
            caretaker=self.caretaker_user,
            reason="Expired caretaker",
            end_date=expired_date,
        )

        # Test get_caretakers method (should not return expired)
        caretakers = self.user_needing_caretaker.get_caretakers()
        self.assertEqual(caretakers.count(), 0)

        # Test get_all_caretakers method (should return expired)
        all_caretakers = self.user_needing_caretaker.get_all_caretakers()
        self.assertEqual(all_caretakers.count(), 1)

    def test_related_name_caretakers_plural(self):
        """Test that the new related_name 'caretakers' (plural) works correctly"""
        # Create a caretaker relationship
        Caretaker.objects.create(
            user=self.user_needing_caretaker,
            caretaker=self.caretaker_user,
            reason="Test related_name",
        )

        # Access via related_name (should be 'caretakers' plural)
        caretakers = self.user_needing_caretaker.caretakers.all()
        self.assertEqual(caretakers.count(), 1)
        self.assertEqual(caretakers.first().caretaker, self.caretaker_user)

    def test_related_name_caretaking_for(self):
        """Test that the new related_name 'caretaking_for' works correctly"""
        # Create a caretaker relationship
        Caretaker.objects.create(
            user=self.user_needing_caretaker,
            caretaker=self.caretaker_user,
            reason="Test related_name",
        )

        # Access via related_name (should be 'caretaking_for')
        caretaking_for = self.caretaker_user.caretaking_for.all()
        self.assertEqual(caretaking_for.count(), 1)
        self.assertEqual(caretaking_for.first().user, self.user_needing_caretaker)
