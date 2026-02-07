"""
Tests for adminoptions views - Part 2
(AdminTaskDetail)
"""

from rest_framework import status

from adminoptions.models import AdminTask
from common.tests.test_helpers import adminoptions_urls

# NOTE: Tests for duplicate caretaker views removed (Caretakers, CaretakerDetail, CheckCaretaker, PendingCaretakerTasks)
# These views were duplicates of the caretakers app and have been removed from adminoptions
# Use tests in backend/caretakers/tests/ instead


class TestAdminTaskDetail:
    """Tests for AdminTaskDetail view"""

    def test_get_admin_task_detail(
        self, api_client, user, admin_task_delete_project, db
    ):
        """Test getting admin task detail"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(
            adminoptions_urls.path("tasks", admin_task_delete_project.id)
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == admin_task_delete_project.id

    def test_put_admin_task_detail(
        self, api_client, user, admin_task_delete_project, db
    ):
        """Test updating admin task"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            "notes": "Updated notes",
        }

        # Act
        response = api_client.put(
            adminoptions_urls.path("tasks", admin_task_delete_project.id),
            data,
            format="json",
        )

        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data["notes"] == "Updated notes"

    def test_delete_admin_task(self, api_client, user, admin_task_delete_project, db):
        """Test deleting admin task"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.delete(
            adminoptions_urls.path("tasks", admin_task_delete_project.id)
        )

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not AdminTask.objects.filter(id=admin_task_delete_project.id).exists()

    def test_get_admin_task_detail_not_found(self, api_client, user, db):
        """Test getting non-existent admin task"""
        # Arrange
        api_client.force_authenticate(user=user)

        # Act
        response = api_client.get(adminoptions_urls.path("tasks", 999))

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
