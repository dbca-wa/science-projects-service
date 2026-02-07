"""
Tests for caretaker views

Tests HTTP endpoints for caretaker operations.
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from adminoptions.models import AdminTask
from caretakers.models import Caretaker
from common.tests.factories import ProjectFactory, UserFactory
from common.tests.test_helpers import caretakers_urls
from documents.models import ProjectDocument
from projects.models import ProjectMember


@pytest.fixture
def api_client():
    """Provide API client"""
    return APIClient()


class TestCaretakerList:
    """Test CaretakerList view (GET/POST /api/v1/caretakers/list)"""

    @pytest.mark.django_db
    def test_list_caretakers_unauthenticated(self, api_client):
        """Test listing caretakers requires authentication"""
        # Act
        response = api_client.get(caretakers_urls.list())

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_list_caretakers_authenticated(
        self, api_client, caretaker_user, caretakee_user, caretaker_assignment
    ):
        """Test listing caretakers as authenticated user"""
        # Arrange
        api_client.force_authenticate(user=caretaker_user)

        # Act
        response = api_client.get(caretakers_urls.list())

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["reason"] == "Test caretaker assignment"

    @pytest.mark.django_db
    def test_list_caretakers_returns_all(self, api_client, db):
        """Test listing caretakers returns all relationships"""
        # Arrange
        user1 = UserFactory()
        user2 = UserFactory()
        user3 = UserFactory()

        Caretaker.objects.create(user=user1, caretaker=user2, reason="Caretaker 1")
        Caretaker.objects.create(user=user2, caretaker=user3, reason="Caretaker 2")

        api_client.force_authenticate(user=user1)

        # Act
        response = api_client.get(caretakers_urls.list())

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    @pytest.mark.django_db
    def test_create_caretaker_unauthenticated(self, api_client):
        """Test creating caretaker requires authentication"""
        # Arrange
        user1 = UserFactory()
        user2 = UserFactory()
        data = {
            "user": user1.pk,
            "caretaker": user2.pk,
            "reason": "Going on leave",
        }

        # Act
        response = api_client.post(caretakers_urls.list(), data)

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_create_caretaker_authenticated(
        self, api_client, caretaker_user, caretakee_user
    ):
        """Test creating caretaker as authenticated user"""
        # Arrange
        api_client.force_authenticate(user=caretaker_user)
        data = {
            "user": caretakee_user.pk,
            "caretaker": caretaker_user.pk,
            "reason": "Going on leave",
        }

        # Act
        response = api_client.post(caretakers_urls.list(), data)

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert Caretaker.objects.count() == 1
        assert response.data["reason"] == "Going on leave"

    @pytest.mark.django_db
    def test_create_caretaker_invalid_data(self, api_client, caretaker_user):
        """Test creating caretaker with invalid data"""
        # Arrange
        api_client.force_authenticate(user=caretaker_user)
        data = {
            "user": caretaker_user.pk,
            "caretaker": caretaker_user.pk,  # Self-caretaking
            "reason": "Invalid",
        }

        # Act
        response = api_client.post(caretakers_urls.list(), data)

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestCaretakerDetail:
    """Test CaretakerDetail view (GET/PUT/DELETE /api/v1/caretakers/<id>/)"""

    @pytest.mark.django_db
    def test_get_caretaker_unauthenticated(self, api_client, caretaker_assignment):
        """Test getting caretaker requires authentication"""
        # Act
        response = api_client.get(caretakers_urls.detail(caretaker_assignment.pk))

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_get_caretaker_authenticated(
        self, api_client, caretaker_user, caretaker_assignment
    ):
        """Test getting caretaker as authenticated user"""
        # Arrange
        api_client.force_authenticate(user=caretaker_user)

        # Act
        response = api_client.get(caretakers_urls.detail(caretaker_assignment.pk))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["reason"] == "Test caretaker assignment"

    @pytest.mark.django_db
    def test_get_caretaker_not_found(self, api_client, caretaker_user):
        """Test getting non-existent caretaker"""
        # Arrange
        api_client.force_authenticate(user=caretaker_user)

        # Act
        response = api_client.get(caretakers_urls.detail(99999))

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_update_caretaker_unauthenticated(self, api_client, caretaker_assignment):
        """Test updating caretaker requires authentication"""
        # Arrange
        data = {"reason": "Updated reason"}

        # Act
        response = api_client.put(caretakers_urls.detail(caretaker_assignment.pk), data)

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_update_caretaker_authenticated(
        self, api_client, caretaker_user, caretaker_assignment
    ):
        """Test updating caretaker as authenticated user"""
        # Arrange
        api_client.force_authenticate(user=caretaker_user)
        data = {"reason": "Updated reason"}

        # Act
        response = api_client.put(caretakers_urls.detail(caretaker_assignment.pk), data)

        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        caretaker_assignment.refresh_from_db()
        assert caretaker_assignment.reason == "Updated reason"

    @pytest.mark.django_db
    def test_update_caretaker_partial_update(
        self, api_client, caretaker_user, caretaker_assignment
    ):
        """Test updating caretaker with partial data"""
        # Arrange
        api_client.force_authenticate(user=caretaker_user)
        data = {"notes": "Updated notes"}

        # Act
        response = api_client.put(caretakers_urls.detail(caretaker_assignment.pk), data)

        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        caretaker_assignment.refresh_from_db()
        assert caretaker_assignment.notes == "Updated notes"

    @pytest.mark.django_db
    def test_delete_caretaker_unauthenticated(self, api_client, caretaker_assignment):
        """Test deleting caretaker requires authentication"""
        # Act
        response = api_client.delete(caretakers_urls.detail(caretaker_assignment.pk))

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_delete_caretaker_authenticated(
        self, api_client, caretaker_user, caretaker_assignment
    ):
        """Test deleting caretaker as authenticated user"""
        # Arrange
        api_client.force_authenticate(user=caretaker_user)

        # Act
        response = api_client.delete(caretakers_urls.detail(caretaker_assignment.pk))

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Caretaker.objects.count() == 0


class TestCaretakerRequestList:
    """Test CaretakerRequestList view (GET /api/v1/caretakers/requests/)"""

    @pytest.mark.django_db
    def test_get_pending_requests_unauthenticated(self, api_client):
        """Test getting pending requests requires authentication"""
        # Act
        response = api_client.get(caretakers_urls.path("requests"))

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_get_pending_requests_requires_user_id(self, api_client, caretaker_user):
        """Test getting pending requests requires user_id parameter"""
        # Arrange
        api_client.force_authenticate(user=caretaker_user)

        # Act
        response = api_client.get(caretakers_urls.path("requests"))

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "user_id" in response.data["error"]

    @pytest.mark.django_db
    def test_get_pending_requests_for_user(self, api_client, db):
        """Test getting pending caretaker requests for a user"""
        # Arrange
        user1 = UserFactory()
        user2 = UserFactory()

        AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            primary_user=user2,
            secondary_users=[user1.pk],
            requester=user2,
            reason="Need caretaker",
        )

        api_client.force_authenticate(user=user1)

        # Act
        response = api_client.get(
            f"{caretakers_urls.path('requests')}?user_id={user1.pk}"
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["primary_user"]["id"] == user2.pk

    @pytest.mark.django_db
    def test_get_pending_requests_excludes_non_pending(self, api_client, db):
        """Test getting pending requests excludes non-pending requests"""
        # Arrange
        user1 = UserFactory()
        user2 = UserFactory()

        # Create approved task (should be excluded)
        AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.APPROVED,
            primary_user=user2,
            secondary_users=[user1.pk],
            requester=user2,
            reason="Approved request",
        )

        api_client.force_authenticate(user=user1)

        # Act
        response = api_client.get(
            f"{caretakers_urls.path('requests')}?user_id={user1.pk}"
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0


class TestApproveCaretakerRequest:
    """Test ApproveCaretakerRequest view (POST /api/v1/caretakers/requests/<id>/approve/)"""

    @pytest.mark.django_db
    def test_approve_request_unauthenticated(self, api_client, db):
        """Test approving request requires authentication"""
        # Arrange
        user1 = UserFactory()
        user2 = UserFactory()
        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            primary_user=user1,
            secondary_users=[user2.pk],
            requester=user1,
            reason="Need caretaker",
        )

        # Act
        response = api_client.post(caretakers_urls.path("requests", task.pk, "approve"))

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_approve_request_creates_caretaker(self, api_client, db):
        """Test approving request creates caretaker relationship"""
        # Arrange
        user1 = UserFactory()
        user2 = UserFactory()
        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            primary_user=user1,
            secondary_users=[user2.pk],
            requester=user1,
            reason="Need caretaker",
        )

        api_client.force_authenticate(user=user2)

        # Act
        response = api_client.post(caretakers_urls.path("requests", task.pk, "approve"))

        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert Caretaker.objects.count() == 1

        caretaker = Caretaker.objects.first()
        assert caretaker.user == user1
        assert caretaker.caretaker == user2

        task.refresh_from_db()
        assert task.status == AdminTask.TaskStatus.FULFILLED

    @pytest.mark.django_db
    def test_approve_request_only_by_requested_caretaker(self, api_client, db):
        """Test only requested caretaker can approve"""
        # Arrange
        user1 = UserFactory()
        user2 = UserFactory()
        other_user = UserFactory()

        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            primary_user=user1,
            secondary_users=[user2.pk],
            requester=user1,
            reason="Need caretaker",
        )

        api_client.force_authenticate(user=other_user)

        # Act
        response = api_client.post(caretakers_urls.path("requests", task.pk, "approve"))

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestRejectCaretakerRequest:
    """Test RejectCaretakerRequest view (POST /api/v1/caretakers/requests/<id>/reject/)"""

    @pytest.mark.django_db
    def test_reject_request_unauthenticated(self, api_client, db):
        """Test rejecting request requires authentication"""
        # Arrange
        user1 = UserFactory()
        user2 = UserFactory()
        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            primary_user=user1,
            secondary_users=[user2.pk],
            requester=user1,
            reason="Need caretaker",
        )

        # Act
        response = api_client.post(caretakers_urls.path("requests", task.pk, "reject"))

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_reject_request_does_not_create_caretaker(self, api_client, db):
        """Test rejecting request does not create caretaker"""
        # Arrange
        user1 = UserFactory()
        user2 = UserFactory()
        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            primary_user=user1,
            secondary_users=[user2.pk],
            requester=user1,
            reason="Need caretaker",
        )

        api_client.force_authenticate(user=user2)

        # Act
        response = api_client.post(caretakers_urls.path("requests", task.pk, "reject"))

        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert Caretaker.objects.count() == 0

        task.refresh_from_db()
        assert task.status == AdminTask.TaskStatus.REJECTED


class TestCaretakerTasksForUser:
    """Test CaretakerTasksForUser view (GET /api/v1/caretakers/tasks/<id>/)"""

    @pytest.mark.django_db
    def test_get_tasks_unauthenticated(self, api_client, caretaker_user):
        """Test getting tasks requires authentication"""
        # Act
        response = api_client.get(caretakers_urls.path("tasks", caretaker_user.pk))

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_get_tasks_no_assignments(self, api_client, caretaker_user):
        """Test getting tasks with no caretaker assignments"""
        # Arrange
        api_client.force_authenticate(user=caretaker_user)

        # Act
        response = api_client.get(caretakers_urls.path("tasks", caretaker_user.pk))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["all"]) == 0
        assert len(response.data["directorate"]) == 0
        assert len(response.data["ba"]) == 0
        assert len(response.data["lead"]) == 0
        assert len(response.data["team"]) == 0

    @pytest.mark.django_db
    def test_get_tasks_with_directorate_documents(
        self, api_client, db, directorate_user
    ):
        """Test getting tasks returns directorate documents"""
        # Arrange
        caretaker = UserFactory()
        Caretaker.objects.create(user=directorate_user, caretaker=caretaker)

        project = ProjectFactory()
        doc = ProjectDocument.objects.create(
            project=project,
            kind="concept",
            status=ProjectDocument.StatusChoices.INAPPROVAL,
            project_lead_approval_granted=True,
            business_area_lead_approval_granted=True,
            directorate_approval_granted=False,
        )

        api_client.force_authenticate(user=caretaker)

        # Act
        response = api_client.get(caretakers_urls.path("tasks", caretaker.pk))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["directorate"]) == 1
        assert response.data["directorate"][0]["id"] == doc.pk

    @pytest.mark.django_db
    def test_get_tasks_with_lead_documents(self, api_client, db):
        """Test getting tasks returns project lead documents"""
        # Arrange
        project_lead = UserFactory()
        caretaker = UserFactory()
        project = ProjectFactory()

        ProjectMember.objects.create(
            project=project,
            user=project_lead,
            is_leader=True,
            role="supervising",
        )

        Caretaker.objects.create(user=project_lead, caretaker=caretaker)

        doc = ProjectDocument.objects.create(
            project=project,
            kind="concept",
            status=ProjectDocument.StatusChoices.INAPPROVAL,
            project_lead_approval_granted=False,
        )

        api_client.force_authenticate(user=caretaker)

        # Act
        response = api_client.get(caretakers_urls.path("tasks", caretaker.pk))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["lead"]) == 1
        assert response.data["lead"][0]["id"] == doc.pk


class TestCheckCaretaker:
    """Test CheckCaretaker view (GET /api/v1/caretakers/check/)"""

    @pytest.mark.django_db
    def test_check_caretaker_unauthenticated(self, api_client):
        """Test checking caretaker requires authentication"""
        # Act
        response = api_client.get(caretakers_urls.path("check"))

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_check_caretaker_no_caretaker(self, api_client, caretaker_user):
        """Test checking caretaker when user has no caretaker"""
        # Arrange
        api_client.force_authenticate(user=caretaker_user)

        # Act
        response = api_client.get(caretakers_urls.path("check"))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["caretaker_object"] is None
        assert response.data["caretaker_request_object"] is None
        assert response.data["become_caretaker_request_object"] is None

    @pytest.mark.django_db
    def test_check_caretaker_with_active_caretaker(
        self, api_client, caretaker_user, caretakee_user, caretaker_assignment
    ):
        """Test checking caretaker when user has active caretaker"""
        # Arrange
        api_client.force_authenticate(user=caretakee_user)

        # Act
        response = api_client.get(caretakers_urls.path("check"))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["caretaker_object"] is not None
        assert response.data["caretaker_object"]["caretaker"]["id"] == caretaker_user.pk

    @pytest.mark.django_db
    def test_check_caretaker_with_pending_request(self, api_client, db):
        """Test checking caretaker when user has pending request"""
        # Arrange
        user1 = UserFactory()
        user2 = UserFactory()

        AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            primary_user=user1,
            secondary_users=[user2.pk],
            requester=user1,
            reason="Pending request",
        )

        api_client.force_authenticate(user=user1)

        # Act
        response = api_client.get(caretakers_urls.path("check"))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["caretaker_request_object"] is not None


class TestAdminSetCaretaker:
    """Test AdminSetCaretaker view (POST /api/v1/caretakers/admin-set/)"""

    @pytest.mark.django_db
    def test_admin_set_caretaker_unauthenticated(self, api_client):
        """Test admin set caretaker requires authentication"""
        # Act
        response = api_client.post(caretakers_urls.path("admin-set"), {})

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_admin_set_caretaker_requires_admin(
        self, api_client, caretaker_user, caretakee_user
    ):
        """Test admin set caretaker requires admin permissions"""
        # Arrange
        api_client.force_authenticate(user=caretaker_user)
        data = {
            "userPk": caretakee_user.pk,
            "caretakerPk": caretaker_user.pk,
            "reason": "Admin set caretaker",
        }

        # Act
        response = api_client.post(caretakers_urls.path("admin-set"), data)

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_admin_set_caretaker_as_admin(self, api_client, db):
        """Test admin set caretaker as admin user"""
        # Arrange
        admin_user = UserFactory(is_superuser=True, is_staff=True)
        user1 = UserFactory()
        user2 = UserFactory()

        api_client.force_authenticate(user=admin_user)
        data = {
            "userPk": user1.pk,
            "caretakerPk": user2.pk,
            "reason": "Admin set caretaker",
        }

        # Act
        response = api_client.post(caretakers_urls.path("admin-set"), data)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert Caretaker.objects.count() == 1

    @pytest.mark.django_db
    def test_admin_set_caretaker_validates_data(self, api_client, db):
        """Test admin set caretaker validates required data"""
        # Arrange
        admin_user = UserFactory(is_superuser=True, is_staff=True)
        user1 = UserFactory()
        user2 = UserFactory()

        api_client.force_authenticate(user=admin_user)

        # Act & Assert - Missing userPk
        response = api_client.post(
            caretakers_urls.path("admin-set"),
            {"caretakerPk": user2.pk, "reason": "Test"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Act & Assert - Missing caretakerPk
        response = api_client.post(
            caretakers_urls.path("admin-set"),
            {"userPk": user1.pk, "reason": "Test"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Act & Assert - Missing reason
        response = api_client.post(
            caretakers_urls.path("admin-set"),
            {"userPk": user1.pk, "caretakerPk": user2.pk},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_admin_set_caretaker_prevents_self_caretaking(self, api_client, db):
        """Test admin set caretaker prevents self-caretaking"""
        # Arrange
        admin_user = UserFactory(is_superuser=True, is_staff=True)
        user1 = UserFactory()

        api_client.force_authenticate(user=admin_user)
        data = {
            "userPk": user1.pk,
            "caretakerPk": user1.pk,
            "reason": "Self caretaking",
        }

        # Act
        response = api_client.post(caretakers_urls.path("admin-set"), data)

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
