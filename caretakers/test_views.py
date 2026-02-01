"""
Tests for caretaker views.

Tests the new caretaker views in the caretakers app.
"""

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status

from users.models import User
from adminoptions.models import AdminTask
from caretakers.models import Caretaker


class CaretakerListViewTest(TestCase):
    """Test CaretakerList view (GET/POST /api/v1/caretakers/)"""

    def setUp(self):
        """Create test users and client"""
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="testpass123",
        )
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="testpass123",
        )
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
        )

    def test_list_caretakers_authenticated(self):
        """Test listing caretakers requires authentication"""
        # Create a caretaker
        Caretaker.objects.create(
            user=self.user1,
            caretaker=self.user2,
            reason="Test caretaker",
        )

        # Try without authentication (DRF returns 403 Forbidden)
        response = self.client.get("/api/v1/caretakers/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Try with authentication
        self.client.force_authenticate(user=self.user1)
        response = self.client.get("/api/v1/caretakers/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_caretakers_returns_all(self):
        """Test listing caretakers returns all caretaker relationships"""
        # Create multiple caretakers
        Caretaker.objects.create(
            user=self.user1,
            caretaker=self.user2,
            reason="Caretaker 1",
        )
        Caretaker.objects.create(
            user=self.user2,
            caretaker=self.user1,
            reason="Caretaker 2",
        )

        self.client.force_authenticate(user=self.user1)
        response = self.client.get("/api/v1/caretakers/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_create_caretaker_authenticated(self):
        """Test creating a caretaker requires authentication"""
        data = {
            "user": self.user1.pk,
            "caretaker": self.user2.pk,
            "reason": "Going on leave",
        }

        # Try without authentication (DRF returns 403 Forbidden)
        response = self.client.post("/api/v1/caretakers/", data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Try with authentication
        self.client.force_authenticate(user=self.user1)
        response = self.client.post("/api/v1/caretakers/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Caretaker.objects.count(), 1)


class CaretakerDetailViewTest(TestCase):
    """Test CaretakerDetail view (GET/PUT/DELETE /api/v1/caretakers/<id>/)"""

    def setUp(self):
        """Create test users and caretaker"""
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="testpass123",
        )
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="testpass123",
        )
        self.caretaker = Caretaker.objects.create(
            user=self.user1,
            caretaker=self.user2,
            reason="Test caretaker",
        )

    def test_get_caretaker_authenticated(self):
        """Test getting a caretaker requires authentication"""
        # Try without authentication (DRF returns 403 Forbidden)
        response = self.client.get(f"/api/v1/caretakers/{self.caretaker.pk}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Try with authentication
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f"/api/v1/caretakers/{self.caretaker.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["reason"], "Test caretaker")

    def test_update_caretaker_authenticated(self):
        """Test updating a caretaker requires authentication"""
        data = {"reason": "Updated reason"}

        # Try without authentication (DRF returns 403 Forbidden)
        response = self.client.put(
            f"/api/v1/caretakers/{self.caretaker.pk}/", data
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Try with authentication
        self.client.force_authenticate(user=self.user1)
        response = self.client.put(
            f"/api/v1/caretakers/{self.caretaker.pk}/", data
        )
        # DRF returns 202 Accepted for successful updates
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.caretaker.refresh_from_db()
        self.assertEqual(self.caretaker.reason, "Updated reason")

    def test_delete_caretaker_authenticated(self):
        """Test deleting a caretaker requires authentication"""
        # Try without authentication (DRF returns 403 Forbidden)
        response = self.client.delete(f"/api/v1/caretakers/{self.caretaker.pk}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Try with authentication
        self.client.force_authenticate(user=self.user1)
        response = self.client.delete(f"/api/v1/caretakers/{self.caretaker.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Caretaker.objects.count(), 0)


class CaretakerRequestListViewTest(TestCase):
    """Test CaretakerRequestList view (GET /api/v1/caretakers/requests/)"""

    def setUp(self):
        """Create test users and requests"""
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="testpass123",
        )
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="testpass123",
        )

    def test_get_pending_requests_requires_user_id(self):
        """Test getting pending requests requires user_id parameter"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get("/api/v1/caretakers/requests/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("user_id", response.data["error"])

    def test_get_pending_requests_for_user(self):
        """Test getting pending caretaker requests for a user"""
        # Create a pending request where user2 wants user1 to be their caretaker
        AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            primary_user=self.user2,
            secondary_users=[self.user1.pk],
            requester=self.user2,
            reason="Need caretaker",
        )

        self.client.force_authenticate(user=self.user1)
        response = self.client.get(
            f"/api/v1/caretakers/requests/?user_id={self.user1.pk}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["primary_user"]["id"], self.user2.pk)


class ApproveCaretakerRequestViewTest(TestCase):
    """Test ApproveCaretakerRequest view (POST /api/v1/caretakers/requests/<id>/approve/)"""

    def setUp(self):
        """Create test users and request"""
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="testpass123",
        )
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="testpass123",
        )
        self.task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            primary_user=self.user1,
            secondary_users=[self.user2.pk],
            requester=self.user1,
            reason="Need caretaker",
        )

    def test_approve_request_requires_authentication(self):
        """Test approving a request requires authentication"""
        # DRF returns 403 Forbidden when not authenticated
        response = self.client.post(
            f"/api/v1/caretakers/requests/{self.task.pk}/approve/"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_approve_request_creates_caretaker(self):
        """Test approving a request creates a caretaker relationship"""
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(
            f"/api/v1/caretakers/requests/{self.task.pk}/approve/"
        )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        # Verify caretaker was created
        self.assertEqual(Caretaker.objects.count(), 1)
        caretaker = Caretaker.objects.first()
        self.assertEqual(caretaker.user, self.user1)
        self.assertEqual(caretaker.caretaker, self.user2)

        # Verify task is fulfilled
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, AdminTask.TaskStatus.FULFILLED)

    def test_approve_request_only_by_requested_caretaker(self):
        """Test only the requested caretaker can approve"""
        # Try to approve as a different user
        other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="testpass123",
        )
        self.client.force_authenticate(user=other_user)
        response = self.client.post(
            f"/api/v1/caretakers/requests/{self.task.pk}/approve/"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class RejectCaretakerRequestViewTest(TestCase):
    """Test RejectCaretakerRequest view (POST /api/v1/caretakers/requests/<id>/reject/)"""

    def setUp(self):
        """Create test users and request"""
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="testpass123",
        )
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="testpass123",
        )
        self.task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            primary_user=self.user1,
            secondary_users=[self.user2.pk],
            requester=self.user1,
            reason="Need caretaker",
        )

    def test_reject_request_requires_authentication(self):
        """Test rejecting a request requires authentication"""
        # DRF returns 403 Forbidden when not authenticated
        response = self.client.post(
            f"/api/v1/caretakers/requests/{self.task.pk}/reject/"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_reject_request_does_not_create_caretaker(self):
        """Test rejecting a request does not create a caretaker relationship"""
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(
            f"/api/v1/caretakers/requests/{self.task.pk}/reject/"
        )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        # Verify no caretaker was created
        self.assertEqual(Caretaker.objects.count(), 0)

        # Verify task is rejected
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, AdminTask.TaskStatus.REJECTED)


class CheckCaretakerViewTest(TestCase):
    """Test CheckCaretaker view (GET /api/v1/caretakers/check/)"""

    def setUp(self):
        """Create test users"""
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="testpass123",
        )
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="testpass123",
        )

    def test_check_caretaker_requires_authentication(self):
        """Test checking caretaker status requires authentication"""
        # DRF returns 403 Forbidden when not authenticated
        response = self.client.get("/api/v1/caretakers/check/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_check_caretaker_with_no_caretaker(self):
        """Test checking caretaker status when user has no caretaker"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get("/api/v1/caretakers/check/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["caretaker_object"])
        self.assertIsNone(response.data["caretaker_request_object"])

    def test_check_caretaker_with_active_caretaker(self):
        """Test checking caretaker status when user has an active caretaker"""
        Caretaker.objects.create(
            user=self.user1,
            caretaker=self.user2,
            reason="Active caretaker",
        )

        self.client.force_authenticate(user=self.user1)
        response = self.client.get("/api/v1/caretakers/check/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data["caretaker_object"])
        self.assertEqual(
            response.data["caretaker_object"]["caretaker"]["id"], self.user2.pk
        )

    def test_check_caretaker_with_pending_request(self):
        """Test checking caretaker status when user has a pending request"""
        AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            primary_user=self.user1,
            secondary_users=[self.user2.pk],
            requester=self.user1,
            reason="Pending request",
        )

        self.client.force_authenticate(user=self.user1)
        response = self.client.get("/api/v1/caretakers/check/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data["caretaker_request_object"])


class AdminSetCaretakerViewTest(TestCase):
    """Test AdminSetCaretaker view (POST /api/v1/caretakers/admin-set/)"""

    def setUp(self):
        """Create test users"""
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="testpass123",
        )
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="testpass123",
        )
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
        )

    def test_admin_set_caretaker_requires_admin(self):
        """Test admin set caretaker requires admin permissions"""
        data = {
            "userPk": self.user1.pk,
            "caretakerPk": self.user2.pk,
            "reason": "Admin set caretaker",
        }

        # Try as regular user (DRF returns 403 Forbidden for non-admin)
        self.client.force_authenticate(user=self.user1)
        response = self.client.post("/api/v1/caretakers/admin-set/", data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Try as admin
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post("/api/v1/caretakers/admin-set/", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Caretaker.objects.count(), 1)

    def test_admin_set_caretaker_validates_data(self):
        """Test admin set caretaker validates required data"""
        self.client.force_authenticate(user=self.admin_user)

        # Missing userPk
        response = self.client.post(
            "/api/v1/caretakers/admin-set/",
            {"caretakerPk": self.user2.pk, "reason": "Test"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Missing caretakerPk
        response = self.client.post(
            "/api/v1/caretakers/admin-set/",
            {"userPk": self.user1.pk, "reason": "Test"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Missing reason
        response = self.client.post(
            "/api/v1/caretakers/admin-set/",
            {"userPk": self.user1.pk, "caretakerPk": self.user2.pk},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_set_caretaker_prevents_self_caretaking(self):
        """Test admin set caretaker prevents user from being their own caretaker"""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            "userPk": self.user1.pk,
            "caretakerPk": self.user1.pk,
            "reason": "Self caretaking",
        }
        response = self.client.post("/api/v1/caretakers/admin-set/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
