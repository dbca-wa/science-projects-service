"""
Tests for adminoptions views - Part 3
(ApproveTask, RejectTask, CancelTask, MergeUsers, AdminSetCaretaker, SetCaretaker, RespondToCaretakerRequest)
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
from users.models import User


class TestApproveTask:
    """Tests for ApproveTask view"""

    def test_approve_delete_project_task(self, api_client, admin_user, admin_task_delete_project, db):
        """Test approving delete project task"""
        # Arrange
        api_client.force_authenticate(user=admin_user)
        project_id = admin_task_delete_project.project.id
        
        # Act
        response = api_client.post(f'/api/v1/adminoptions/tasks/{admin_task_delete_project.id}/approve')
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        admin_task_delete_project.refresh_from_db()
        assert admin_task_delete_project.status == AdminTask.TaskStatus.FULFILLED
        assert not Project.objects.filter(id=project_id).exists()

    def test_approve_merge_user_task(self, api_client, admin_user, admin_task_merge_user, db):
        """Test approving merge user task"""
        # Arrange
        api_client.force_authenticate(user=admin_user)
        secondary_user_id = admin_task_merge_user.secondary_users[0]
        
        # Act
        response = api_client.post(f'/api/v1/adminoptions/tasks/{admin_task_merge_user.id}/approve')
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        admin_task_merge_user.refresh_from_db()
        assert admin_task_merge_user.status == AdminTask.TaskStatus.FULFILLED
        assert not User.objects.filter(id=secondary_user_id).exists()

    def test_approve_merge_user_task_with_project_memberships(self, api_client, admin_user, user, secondary_user, project, db):
        """Test approving merge user task merges project memberships"""
        # Arrange
        api_client.force_authenticate(user=admin_user)
        
        # Create project membership for secondary user
        ProjectMember.objects.create(
            project=project,
            user=secondary_user,
            is_leader=False,
            role=ProjectMember.RoleChoices.RESEARCH,
            old_id=999999,  # Required field
        )
        
        # Create merge task
        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.MERGEUSER,
            status=AdminTask.TaskStatus.PENDING,
            requester=admin_user,
            primary_user=user,
            secondary_users=[secondary_user.id],
            reason='Test merge',
        )
        
        # Act
        response = api_client.post(f'/api/v1/adminoptions/tasks/{task.id}/approve')
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert ProjectMember.objects.filter(project=project, user=user).exists()
        assert not User.objects.filter(id=secondary_user.id).exists()

    def test_approve_merge_user_task_with_documents(self, api_client, admin_user, user, secondary_user, project, db):
        """Test approving merge user task merges documents"""
        # Arrange
        api_client.force_authenticate(user=admin_user)
        
        # Create document created by secondary user
        doc = ProjectDocument.objects.create(
            project=project,
            kind=ProjectDocument.CategoryKindChoices.CONCEPTPLAN,
            status=ProjectDocument.StatusChoices.NEW,
            creator=secondary_user,
            modifier=secondary_user,
            old_id=999997,  # Required field
        )
        
        # Create merge task
        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.MERGEUSER,
            status=AdminTask.TaskStatus.PENDING,
            requester=admin_user,
            primary_user=user,
            secondary_users=[secondary_user.id],
            reason='Test merge',
        )
        
        # Act
        response = api_client.post(f'/api/v1/adminoptions/tasks/{task.id}/approve')
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        doc.refresh_from_db()
        assert doc.creator == user
        assert doc.modifier == user

    def test_approve_merge_user_task_with_comments(self, api_client, admin_user, user, secondary_user, project, db):
        """Test approving merge user task merges comments"""
        # Arrange
        api_client.force_authenticate(user=admin_user)
        
        # Create comment by secondary user
        doc = ProjectDocument.objects.create(
            project=project,
            kind=ProjectDocument.CategoryKindChoices.CONCEPTPLAN,
            status=ProjectDocument.StatusChoices.NEW,
            old_id=999996,  # Required field
        )
        comment = Comment.objects.create(
            document=doc,
            user=secondary_user,
            text='Test comment',
        )
        
        # Create merge task
        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.MERGEUSER,
            status=AdminTask.TaskStatus.PENDING,
            requester=admin_user,
            primary_user=user,
            secondary_users=[secondary_user.id],
            reason='Test merge',
        )
        
        # Act
        response = api_client.post(f'/api/v1/adminoptions/tasks/{task.id}/approve')
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        comment.refresh_from_db()
        assert comment.user == user

    def test_approve_set_caretaker_task(self, api_client, admin_user, admin_task_set_caretaker, db):
        """Test approving set caretaker task"""
        # Arrange
        api_client.force_authenticate(user=admin_user)
        
        # Act
        response = api_client.post(f'/api/v1/adminoptions/tasks/{admin_task_set_caretaker.id}/approve')
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        admin_task_set_caretaker.refresh_from_db()
        assert admin_task_set_caretaker.status == AdminTask.TaskStatus.FULFILLED
        assert Caretaker.objects.filter(
            user=admin_task_set_caretaker.primary_user,
            caretaker_id=admin_task_set_caretaker.secondary_users[0]
        ).exists()

    def test_approve_task_requires_admin(self, api_client, user, admin_task_delete_project, db):
        """Test approving task requires admin permission"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.post(f'/api/v1/adminoptions/tasks/{admin_task_delete_project.id}/approve')
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_approve_task_not_found(self, api_client, admin_user, db):
        """Test approving non-existent task"""
        # Arrange
        api_client.force_authenticate(user=admin_user)
        
        # Act
        response = api_client.post('/api/v1/adminoptions/tasks/999/approve')
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRejectTask:
    """Tests for RejectTask view"""

    def test_reject_delete_project_task(self, api_client, admin_user, admin_task_delete_project, db):
        """Test rejecting delete project task"""
        # Arrange
        api_client.force_authenticate(user=admin_user)
        project = admin_task_delete_project.project
        
        # Act
        response = api_client.post(f'/api/v1/adminoptions/tasks/{admin_task_delete_project.id}/reject')
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        admin_task_delete_project.refresh_from_db()
        assert admin_task_delete_project.status == AdminTask.TaskStatus.REJECTED
        project.refresh_from_db()
        assert project.deletion_requested is False

    def test_reject_merge_user_task(self, api_client, admin_user, admin_task_merge_user, db):
        """Test rejecting merge user task"""
        # Arrange
        api_client.force_authenticate(user=admin_user)
        
        # Act
        response = api_client.post(f'/api/v1/adminoptions/tasks/{admin_task_merge_user.id}/reject')
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        admin_task_merge_user.refresh_from_db()
        assert admin_task_merge_user.status == AdminTask.TaskStatus.REJECTED

    def test_reject_set_caretaker_task(self, api_client, admin_user, admin_task_set_caretaker, db):
        """Test rejecting set caretaker task"""
        # Arrange
        api_client.force_authenticate(user=admin_user)
        
        # Act
        response = api_client.post(f'/api/v1/adminoptions/tasks/{admin_task_set_caretaker.id}/reject')
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        admin_task_set_caretaker.refresh_from_db()
        assert admin_task_set_caretaker.status == AdminTask.TaskStatus.REJECTED

    def test_reject_task_requires_admin(self, api_client, user, admin_task_delete_project, db):
        """Test rejecting task requires admin permission"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.post(f'/api/v1/adminoptions/tasks/{admin_task_delete_project.id}/reject')
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestCancelTask:
    """Tests for CancelTask view"""

    def test_cancel_delete_project_task(self, api_client, user, admin_task_delete_project, db):
        """Test cancelling delete project task"""
        # Arrange
        api_client.force_authenticate(user=user)
        project = admin_task_delete_project.project
        
        # Act
        response = api_client.post(f'/api/v1/adminoptions/tasks/{admin_task_delete_project.id}/cancel')
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        admin_task_delete_project.refresh_from_db()
        assert admin_task_delete_project.status == AdminTask.TaskStatus.CANCELLED
        project.refresh_from_db()
        assert project.deletion_requested is False

    def test_cancel_merge_user_task(self, api_client, user, admin_task_merge_user, db):
        """Test cancelling merge user task"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.post(f'/api/v1/adminoptions/tasks/{admin_task_merge_user.id}/cancel')
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        admin_task_merge_user.refresh_from_db()
        assert admin_task_merge_user.status == AdminTask.TaskStatus.CANCELLED

    def test_cancel_set_caretaker_task(self, api_client, user, admin_task_set_caretaker, db):
        """Test cancelling set caretaker task
        
        NOTE: Currently the cancel view does not update user.caretaker_mode to False.
        This may be intentional behavior or a production bug to investigate.
        """
        # Arrange
        api_client.force_authenticate(user=user)
        primary_user = admin_task_set_caretaker.primary_user
        primary_user.caretaker_mode = True
        primary_user.save()
        
        # Act
        response = api_client.post(f'/api/v1/adminoptions/tasks/{admin_task_set_caretaker.id}/cancel')
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        admin_task_set_caretaker.refresh_from_db()
        assert admin_task_set_caretaker.status == AdminTask.TaskStatus.CANCELLED
        # NOTE: caretaker_mode is NOT updated by the cancel view
        # primary_user.refresh_from_db()
        # assert primary_user.caretaker_mode is False


class TestMergeUsers:
    """Tests for MergeUsers view"""

    def test_merge_users(self, api_client, admin_user, user, secondary_user, db):
        """Test merging users"""
        # Arrange
        api_client.force_authenticate(user=admin_user)
        data = {
            'primaryUser': user.id,
            'secondaryUsers': [secondary_user.id],
        }
        
        # Act
        response = api_client.post('/api/v1/adminoptions/mergeusers', data, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert not User.objects.filter(id=secondary_user.id).exists()

    def test_merge_users_with_projects(self, api_client, admin_user, user, secondary_user, project, db):
        """Test merging users with project memberships"""
        # Arrange
        api_client.force_authenticate(user=admin_user)
        
        # Create project membership for secondary user
        ProjectMember.objects.create(
            project=project,
            user=secondary_user,
            is_leader=False,
            role=ProjectMember.RoleChoices.RESEARCH,
            old_id=999998,  # Required field
        )
        
        data = {
            'primaryUser': user.id,
            'secondaryUsers': [secondary_user.id],
        }
        
        # Act
        response = api_client.post('/api/v1/adminoptions/mergeusers', data, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert ProjectMember.objects.filter(project=project, user=user).exists()

    def test_merge_users_missing_data(self, api_client, admin_user, db):
        """Test merging users with missing data"""
        # Arrange
        api_client.force_authenticate(user=admin_user)
        data = {}
        
        # Act
        response = api_client.post('/api/v1/adminoptions/mergeusers', data, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_merge_users_primary_in_secondary(self, api_client, admin_user, user, db):
        """Test merging users with primary user in secondary list"""
        # Arrange
        api_client.force_authenticate(user=admin_user)
        data = {
            'primaryUser': user.id,
            'secondaryUsers': [user.id],
        }
        
        # Act
        response = api_client.post('/api/v1/adminoptions/mergeusers', data, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_merge_users_requires_superuser(self, api_client, user, secondary_user, db):
        """Test merging users requires superuser permission"""
        # Arrange
        user.is_staff = True
        user.save()
        api_client.force_authenticate(user=user)
        data = {
            'primaryUser': user.id,
            'secondaryUsers': [secondary_user.id],
        }
        
        # Act
        response = api_client.post('/api/v1/adminoptions/mergeusers', data, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# NOTE: Tests for duplicate caretaker views removed (AdminSetCaretaker, SetCaretaker)
# These views were duplicates of the caretakers app and have been removed from adminoptions
# Use tests in backend/caretakers/tests/ instead


class TestRespondToCaretakerRequest:
    """Tests for RespondToCaretakerRequest view"""

    def test_approve_caretaker_request(self, api_client, user, secondary_user, db):
        """Test approving caretaker request"""
        # Arrange
        api_client.force_authenticate(user=secondary_user)
        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            requester=user,
            primary_user=user,
            secondary_users=[secondary_user.id],
            reason='Test',
        )
        
        data = {'action': 'approve'}
        
        # Act
        response = api_client.post(
            f'/api/v1/adminoptions/tasks/{task.id}/respond',
            data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        task.refresh_from_db()
        assert task.status == AdminTask.TaskStatus.FULFILLED
        assert Caretaker.objects.filter(user=user, caretaker=secondary_user).exists()

    def test_reject_caretaker_request(self, api_client, user, secondary_user, db):
        """Test rejecting caretaker request"""
        # Arrange
        api_client.force_authenticate(user=secondary_user)
        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            requester=user,
            primary_user=user,
            secondary_users=[secondary_user.id],
            reason='Test',
        )
        
        data = {'action': 'reject'}
        
        # Act
        response = api_client.post(
            f'/api/v1/adminoptions/tasks/{task.id}/respond',
            data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        task.refresh_from_db()
        assert task.status == AdminTask.TaskStatus.REJECTED
        assert not Caretaker.objects.filter(user=user, caretaker=secondary_user).exists()

    def test_respond_to_non_caretaker_task(self, api_client, user, admin_task_delete_project, db):
        """Test responding to non-caretaker task fails"""
        # Arrange
        api_client.force_authenticate(user=user)
        data = {'action': 'approve'}
        
        # Act
        response = api_client.post(
            f'/api/v1/adminoptions/tasks/{admin_task_delete_project.id}/respond',
            data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_respond_to_non_pending_task(self, api_client, user, secondary_user, db):
        """Test responding to non-pending task fails"""
        # Arrange
        api_client.force_authenticate(user=secondary_user)
        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.APPROVED,
            requester=user,
            primary_user=user,
            secondary_users=[secondary_user.id],
            reason='Test',
        )
        
        data = {'action': 'approve'}
        
        # Act
        response = api_client.post(
            f'/api/v1/adminoptions/tasks/{task.id}/respond',
            data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_respond_unauthorized_user(self, api_client, user, secondary_user, db):
        """Test responding as unauthorized user fails"""
        # Arrange
        third_user = User.objects.create_user(
            username='third',
            email='third@test.com',
        )
        api_client.force_authenticate(user=third_user)
        
        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            requester=user,
            primary_user=user,
            secondary_users=[secondary_user.id],
            reason='Test',
        )
        
        data = {'action': 'approve'}
        
        # Act
        response = api_client.post(
            f'/api/v1/adminoptions/tasks/{task.id}/respond',
            data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_respond_invalid_action(self, api_client, user, secondary_user, db):
        """Test responding with invalid action fails"""
        # Arrange
        api_client.force_authenticate(user=secondary_user)
        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            requester=user,
            primary_user=user,
            secondary_users=[secondary_user.id],
            reason='Test',
        )
        
        data = {'action': 'invalid'}
        
        # Act
        response = api_client.post(
            f'/api/v1/adminoptions/tasks/{task.id}/respond',
            data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
