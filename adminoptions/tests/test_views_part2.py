"""
Tests for adminoptions views - Part 2
(AdminTaskDetail)
"""
import pytest
from unittest.mock import Mock, patch
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from adminoptions.models import AdminOptions, AdminTask, GuideSection, ContentField
from caretakers.models import Caretaker
from projects.models import Project, ProjectMember
from documents.models import ProjectDocument
from communications.models import Comment


# NOTE: Tests for duplicate caretaker views removed (Caretakers, CaretakerDetail, CheckCaretaker, PendingCaretakerTasks)
# These views were duplicates of the caretakers app and have been removed from adminoptions
# Use tests in backend/caretakers/tests/ instead


class TestAdminTaskDetail:
    """Tests for AdminTaskDetail view"""

    def test_get_admin_task_detail(self, api_client, user, admin_task_delete_project, db):
        """Test getting admin task detail"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(f'/api/v1/adminoptions/tasks/{admin_task_delete_project.id}')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == admin_task_delete_project.id

    def test_put_admin_task_detail(self, api_client, user, admin_task_delete_project, db):
        """Test updating admin task"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {
            'notes': 'Updated notes',
        }
        
        # Act
        response = api_client.put(
            f'/api/v1/adminoptions/tasks/{admin_task_delete_project.id}',
            data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data['notes'] == 'Updated notes'

    def test_delete_admin_task(self, api_client, user, admin_task_delete_project, db):
        """Test deleting admin task"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.delete(f'/api/v1/adminoptions/tasks/{admin_task_delete_project.id}')
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not AdminTask.objects.filter(id=admin_task_delete_project.id).exists()

    def test_get_admin_task_detail_not_found(self, api_client, user, db):
        """Test getting non-existent admin task"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get('/api/v1/adminoptions/tasks/999')
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

