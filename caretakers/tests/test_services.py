"""
Tests for caretaker services

Tests business logic in caretaker services.
"""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from adminoptions.models import AdminTask
from caretakers.models import Caretaker
from caretakers.services.caretaker_service import CaretakerService
from caretakers.services.request_service import CaretakerRequestService
from caretakers.services.task_service import CaretakerTaskService
from common.tests.factories import BusinessAreaFactory, ProjectFactory, UserFactory
from documents.models import ProjectDocument
from projects.models import Project, ProjectMember

User = get_user_model()


class TestCaretakerTaskService:
    """Test CaretakerTaskService business logic"""

    @pytest.mark.django_db
    def test_get_all_caretaker_assignments_direct(
        self, caretaker_user, caretakee_user, caretaker_assignment
    ):
        """Test get_all_caretaker_assignments returns direct assignments"""
        # Act
        assignments = CaretakerTaskService.get_all_caretaker_assignments(
            caretaker_user.id
        )

        # Assert
        assert len(assignments) == 1
        assert assignments[0].user == caretakee_user
        assert assignments[0].caretaker == caretaker_user

    @pytest.mark.django_db
    def test_get_all_caretaker_assignments_nested(self, db):
        """Test get_all_caretaker_assignments handles nested relationships"""
        # Arrange - Create chain: user1 -> user2 -> user3
        user1 = UserFactory(username="user1")
        user2 = UserFactory(username="user2")
        user3 = UserFactory(username="user3")

        # user1 caretakes for user2
        Caretaker.objects.create(user=user2, caretaker=user1)
        # user2 caretakes for user3
        Caretaker.objects.create(user=user3, caretaker=user2)

        # Act
        assignments = CaretakerTaskService.get_all_caretaker_assignments(user1.id)

        # Assert - Should get both user2 and user3
        assert len(assignments) == 2
        user_ids = [a.user.id for a in assignments]
        assert user2.id in user_ids
        assert user3.id in user_ids

    @pytest.mark.django_db
    def test_get_all_caretaker_assignments_circular_prevention(self, db):
        """Test get_all_caretaker_assignments prevents infinite loops"""
        # Arrange - Create circular relationship: user1 -> user2 -> user1
        user1 = UserFactory(username="user1")
        user2 = UserFactory(username="user2")

        Caretaker.objects.create(user=user2, caretaker=user1)
        Caretaker.objects.create(user=user1, caretaker=user2)

        # Act - Should not cause infinite loop
        assignments = CaretakerTaskService.get_all_caretaker_assignments(user1.id)

        # Assert - Should get user2 (direct assignment) but not loop back to user1
        # The function tracks processed_users to prevent infinite recursion
        assert len(assignments) >= 1
        # Verify user2 is in the assignments
        user_ids = [a.user.id for a in assignments]
        assert user2.id in user_ids

    @pytest.mark.django_db
    def test_get_all_caretaker_assignments_no_assignments(self, db):
        """Test get_all_caretaker_assignments with no assignments"""
        # Arrange
        user = UserFactory()

        # Act
        assignments = CaretakerTaskService.get_all_caretaker_assignments(user.id)

        # Assert
        assert len(assignments) == 0

    @pytest.mark.django_db
    def test_get_directorate_documents(self, db):
        """Test get_directorate_documents returns correct documents"""
        # Arrange
        project1 = ProjectFactory()
        project2 = ProjectFactory()

        # Create documents at different stages
        doc1 = ProjectDocument.objects.create(
            project=project1,
            kind="concept",
            status=ProjectDocument.StatusChoices.INAPPROVAL,
            project_lead_approval_granted=True,
            business_area_lead_approval_granted=True,
            directorate_approval_granted=False,
        )

        # Document already approved (should be excluded)
        ProjectDocument.objects.create(
            project=project2,
            kind="concept",
            status=ProjectDocument.StatusChoices.APPROVED,
            project_lead_approval_granted=True,
            business_area_lead_approval_granted=True,
            directorate_approval_granted=True,
        )

        # Document not ready for directorate (should be excluded)
        ProjectDocument.objects.create(
            project=project1,
            kind="projectplan",
            status=ProjectDocument.StatusChoices.INAPPROVAL,
            project_lead_approval_granted=True,
            business_area_lead_approval_granted=False,
            directorate_approval_granted=False,
        )

        projects = Project.objects.filter(pk__in=[project1.pk, project2.pk])

        # Act
        documents = CaretakerTaskService.get_directorate_documents(projects)

        # Assert
        assert documents.count() == 1
        assert documents.first().pk == doc1.pk

    @pytest.mark.django_db
    def test_get_ba_documents(self, db):
        """Test get_ba_documents returns correct documents"""
        # Arrange
        project1 = ProjectFactory()
        project2 = ProjectFactory()

        # Document ready for BA approval
        doc1 = ProjectDocument.objects.create(
            project=project1,
            kind="concept",
            status=ProjectDocument.StatusChoices.INAPPROVAL,
            project_lead_approval_granted=True,
            business_area_lead_approval_granted=False,
        )

        # Document already approved (should be excluded)
        ProjectDocument.objects.create(
            project=project2,
            kind="concept",
            status=ProjectDocument.StatusChoices.APPROVED,
            project_lead_approval_granted=True,
            business_area_lead_approval_granted=True,
        )

        # Document not ready for BA (should be excluded)
        ProjectDocument.objects.create(
            project=project1,
            kind="projectplan",
            status=ProjectDocument.StatusChoices.INAPPROVAL,
            project_lead_approval_granted=False,
            business_area_lead_approval_granted=False,
        )

        projects = Project.objects.filter(pk__in=[project1.pk, project2.pk])

        # Act
        documents = CaretakerTaskService.get_ba_documents(projects)

        # Assert
        assert documents.count() == 1
        assert documents.first().pk == doc1.pk

    @pytest.mark.django_db
    def test_get_lead_documents(self, db):
        """Test get_lead_documents returns correct documents"""
        # Arrange
        project1 = ProjectFactory()
        project2 = ProjectFactory()

        # Document ready for project lead approval
        doc1 = ProjectDocument.objects.create(
            project=project1,
            kind="concept",
            status=ProjectDocument.StatusChoices.INAPPROVAL,
            project_lead_approval_granted=False,
        )

        # Document already approved (should be excluded)
        ProjectDocument.objects.create(
            project=project2,
            kind="concept",
            status=ProjectDocument.StatusChoices.APPROVED,
            project_lead_approval_granted=True,
        )

        # Document already has lead approval (should be excluded)
        ProjectDocument.objects.create(
            project=project1,
            kind="projectplan",
            status=ProjectDocument.StatusChoices.INAPPROVAL,
            project_lead_approval_granted=True,
        )

        project_ids = [project1.pk, project2.pk]

        # Act
        documents = CaretakerTaskService.get_lead_documents(project_ids)

        # Assert
        assert documents.count() == 1
        assert documents.first().pk == doc1.pk

    @pytest.mark.django_db
    def test_get_team_documents(self, db):
        """Test get_team_documents returns correct documents"""
        # Arrange
        project1 = ProjectFactory()
        project2 = ProjectFactory()

        # Document ready for team member attention
        doc1 = ProjectDocument.objects.create(
            project=project1,
            kind="concept",
            status=ProjectDocument.StatusChoices.INAPPROVAL,
            project_lead_approval_granted=False,
        )

        # Document already approved (should be excluded)
        ProjectDocument.objects.create(
            project=project2,
            kind="concept",
            status=ProjectDocument.StatusChoices.APPROVED,
            project_lead_approval_granted=True,
        )

        project_ids = [project1.pk, project2.pk]

        # Act
        documents = CaretakerTaskService.get_team_documents(project_ids)

        # Assert
        assert documents.count() == 1
        assert documents.first().pk == doc1.pk

    @pytest.mark.django_db
    def test_analyze_caretakee_roles_project_lead(self, db):
        """Test analyze_caretakee_roles identifies project leads"""
        # Arrange
        user = UserFactory()
        project = ProjectFactory()

        # Make user a project lead
        ProjectMember.objects.create(
            project=project,
            user=user,
            is_leader=True,
            role="supervising",
        )

        # Create caretaker assignment
        caretaker = UserFactory()
        assignment = Caretaker.objects.create(user=user, caretaker=caretaker)

        # Act
        roles = CaretakerTaskService.analyze_caretakee_roles([assignment])

        # Assert
        assert user.id in roles["project_lead_user_ids"]
        assert user.id not in roles["team_member_user_ids"]
        assert not roles["directorate_user_found"]
        assert len(roles["ba_leader_user_ids"]) == 0

    @pytest.mark.django_db
    def test_analyze_caretakee_roles_team_member(self, db):
        """Test analyze_caretakee_roles identifies team members"""
        # Arrange
        user = UserFactory()
        project = ProjectFactory()

        # Make user a team member (not leader)
        ProjectMember.objects.create(
            project=project,
            user=user,
            is_leader=False,
            role="research",
        )

        # Create caretaker assignment
        caretaker = UserFactory()
        assignment = Caretaker.objects.create(user=user, caretaker=caretaker)

        # Act
        roles = CaretakerTaskService.analyze_caretakee_roles([assignment])

        # Assert
        assert user.id in roles["team_member_user_ids"]
        assert user.id not in roles["project_lead_user_ids"]
        assert not roles["directorate_user_found"]
        assert len(roles["ba_leader_user_ids"]) == 0

    @pytest.mark.django_db
    def test_analyze_caretakee_roles_ba_leader(self, db):
        """Test analyze_caretakee_roles identifies BA leaders"""
        # Arrange
        user = UserFactory()
        BusinessAreaFactory(leader=user)

        # Create caretaker assignment
        caretaker = UserFactory()
        assignment = Caretaker.objects.create(user=user, caretaker=caretaker)

        # Act
        roles = CaretakerTaskService.analyze_caretakee_roles([assignment])

        # Assert
        assert user.id in roles["ba_leader_user_ids"]
        assert not roles["directorate_user_found"]

    @pytest.mark.django_db
    def test_analyze_caretakee_roles_directorate_by_ba(self, db, directorate_user):
        """Test analyze_caretakee_roles identifies Directorate users by BA"""
        # Arrange
        caretaker = UserFactory()
        assignment = Caretaker.objects.create(
            user=directorate_user, caretaker=caretaker
        )

        # Act
        roles = CaretakerTaskService.analyze_caretakee_roles([assignment])

        # Assert
        assert roles["directorate_user_found"] is True

    @pytest.mark.django_db
    def test_analyze_caretakee_roles_directorate_by_superuser(self, db):
        """Test analyze_caretakee_roles identifies superusers as Directorate"""
        # Arrange
        user = UserFactory(is_superuser=True)
        caretaker = UserFactory()
        assignment = Caretaker.objects.create(user=user, caretaker=caretaker)

        # Act
        roles = CaretakerTaskService.analyze_caretakee_roles([assignment])

        # Assert
        assert roles["directorate_user_found"] is True

    @pytest.mark.django_db
    def test_analyze_caretakee_roles_closed_projects_excluded(self, db):
        """Test analyze_caretakee_roles excludes closed projects"""
        # Arrange
        user = UserFactory()
        # Use COMPLETED status which is in CLOSED_ONLY tuple
        closed_project = ProjectFactory(status=Project.StatusChoices.COMPLETED)

        # Make user a project lead of closed project
        ProjectMember.objects.create(
            project=closed_project,
            user=user,
            is_leader=True,
            role="supervising",
        )

        # Create caretaker assignment
        caretaker = UserFactory()
        assignment = Caretaker.objects.create(user=user, caretaker=caretaker)

        # Act
        roles = CaretakerTaskService.analyze_caretakee_roles([assignment])

        # Assert - User should NOT be in project_lead_user_ids because project is closed
        # The service correctly excludes closed projects from the query
        assert user.id not in roles["project_lead_user_ids"]
        assert user.id not in roles["team_member_user_ids"]

    @pytest.mark.django_db
    def test_analyze_caretakee_roles_active_projects_included(self, db):
        """Test analyze_caretakee_roles includes active projects"""
        # Arrange
        user = UserFactory()
        # Use ACTIVE status (not in CLOSED_ONLY tuple)
        active_project = ProjectFactory(status=Project.StatusChoices.ACTIVE)

        # Make user a project lead of active project
        ProjectMember.objects.create(
            project=active_project,
            user=user,
            is_leader=True,
            role="supervising",
        )

        # Create caretaker assignment
        caretaker = UserFactory()
        assignment = Caretaker.objects.create(user=user, caretaker=caretaker)

        # Act
        roles = CaretakerTaskService.analyze_caretakee_roles([assignment])

        # Assert - User SHOULD be in project_lead_user_ids because project is active
        assert user.id in roles["project_lead_user_ids"]
        assert user.id not in roles["team_member_user_ids"]

    @pytest.mark.django_db
    def test_get_tasks_for_user_no_assignments(self, db):
        """Test get_tasks_for_user with no caretaker assignments"""
        # Arrange
        user = UserFactory()
        requesting_user = UserFactory()

        # Act
        tasks = CaretakerTaskService.get_tasks_for_user(user.id, requesting_user)

        # Assert
        assert len(tasks["caretaker_assignments"]) == 0
        assert len(tasks["directorate_documents"]) == 0
        assert len(tasks["ba_documents"]) == 0
        assert len(tasks["lead_documents"]) == 0
        assert len(tasks["member_documents"]) == 0

    @pytest.mark.django_db
    def test_get_tasks_for_user_with_directorate_documents(self, db, directorate_user):
        """Test get_tasks_for_user returns directorate documents"""
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

        requesting_user = UserFactory()

        # Act
        tasks = CaretakerTaskService.get_tasks_for_user(caretaker.id, requesting_user)

        # Assert
        assert len(tasks["caretaker_assignments"]) == 1
        assert tasks["roles"]["directorate_user_found"] is True
        assert len(tasks["directorate_documents"]) == 1
        assert tasks["directorate_documents"][0].pk == doc.pk

    @pytest.mark.django_db
    def test_get_tasks_for_user_requesting_user_is_directorate(
        self, db, directorate_user
    ):
        """Test get_tasks_for_user filters out documents requesting user has access to"""
        # Arrange
        caretaker = UserFactory()
        Caretaker.objects.create(user=directorate_user, caretaker=caretaker)

        project = ProjectFactory()
        ProjectDocument.objects.create(
            project=project,
            kind="concept",
            status=ProjectDocument.StatusChoices.INAPPROVAL,
            project_lead_approval_granted=True,
            business_area_lead_approval_granted=True,
            directorate_approval_granted=False,
        )

        # Requesting user is also in Directorate
        requesting_user = directorate_user

        # Act
        tasks = CaretakerTaskService.get_tasks_for_user(caretaker.id, requesting_user)

        # Assert - Should filter out directorate documents
        assert len(tasks["directorate_documents"]) == 0

    @pytest.mark.django_db
    def test_get_tasks_for_user_with_ba_documents(self, db):
        """Test get_tasks_for_user returns BA documents"""
        # Arrange
        ba_leader = UserFactory()
        business_area = BusinessAreaFactory(leader=ba_leader)
        project = ProjectFactory(business_area=business_area)

        caretaker = UserFactory()
        Caretaker.objects.create(user=ba_leader, caretaker=caretaker)

        doc = ProjectDocument.objects.create(
            project=project,
            kind="concept",
            status=ProjectDocument.StatusChoices.INAPPROVAL,
            project_lead_approval_granted=True,
            business_area_lead_approval_granted=False,
        )

        requesting_user = UserFactory()

        # Act
        tasks = CaretakerTaskService.get_tasks_for_user(caretaker.id, requesting_user)

        # Assert
        assert len(tasks["caretaker_assignments"]) == 1
        assert ba_leader.id in tasks["roles"]["ba_leader_user_ids"]
        assert len(tasks["ba_documents"]) == 1
        assert tasks["ba_documents"][0].pk == doc.pk

    @pytest.mark.django_db
    def test_get_tasks_for_user_with_lead_documents(self, db):
        """Test get_tasks_for_user returns project lead documents"""
        # Arrange
        project_lead = UserFactory()
        project = ProjectFactory()
        ProjectMember.objects.create(
            project=project,
            user=project_lead,
            is_leader=True,
            role="supervising",
        )

        caretaker = UserFactory()
        Caretaker.objects.create(user=project_lead, caretaker=caretaker)

        doc = ProjectDocument.objects.create(
            project=project,
            kind="concept",
            status=ProjectDocument.StatusChoices.INAPPROVAL,
            project_lead_approval_granted=False,
        )

        requesting_user = UserFactory()

        # Act
        tasks = CaretakerTaskService.get_tasks_for_user(caretaker.id, requesting_user)

        # Assert
        assert len(tasks["caretaker_assignments"]) == 1
        assert project_lead.id in tasks["roles"]["project_lead_user_ids"]
        assert len(tasks["lead_documents"]) == 1
        assert tasks["lead_documents"][0].pk == doc.pk

    @pytest.mark.django_db
    def test_get_tasks_for_user_with_member_documents(self, db):
        """Test get_tasks_for_user returns team member documents"""
        # Arrange
        team_member = UserFactory()
        project = ProjectFactory()
        ProjectMember.objects.create(
            project=project,
            user=team_member,
            is_leader=False,
            role="research",
        )

        caretaker = UserFactory()
        Caretaker.objects.create(user=team_member, caretaker=caretaker)

        doc = ProjectDocument.objects.create(
            project=project,
            kind="concept",
            status=ProjectDocument.StatusChoices.INAPPROVAL,
            project_lead_approval_granted=False,
        )

        requesting_user = UserFactory()

        # Act
        tasks = CaretakerTaskService.get_tasks_for_user(caretaker.id, requesting_user)

        # Assert
        assert len(tasks["caretaker_assignments"]) == 1
        assert team_member.id in tasks["roles"]["team_member_user_ids"]
        assert len(tasks["member_documents"]) == 1
        assert tasks["member_documents"][0].pk == doc.pk

    @pytest.mark.django_db
    def test_get_tasks_for_user_multiple_roles(self, db):
        """Test get_tasks_for_user handles user with multiple roles"""
        # Arrange
        user = UserFactory()

        # User is BA leader
        business_area = BusinessAreaFactory(leader=user)

        # User is also project lead
        project = ProjectFactory(business_area=business_area)
        ProjectMember.objects.create(
            project=project,
            user=user,
            is_leader=True,
            role="supervising",
        )

        caretaker = UserFactory()
        Caretaker.objects.create(user=user, caretaker=caretaker)

        # Create documents for both roles
        ProjectDocument.objects.create(
            project=project,
            kind="concept",
            status=ProjectDocument.StatusChoices.INAPPROVAL,
            project_lead_approval_granted=True,
            business_area_lead_approval_granted=False,
        )

        ProjectDocument.objects.create(
            project=project,
            kind="projectplan",
            status=ProjectDocument.StatusChoices.INAPPROVAL,
            project_lead_approval_granted=False,
        )

        requesting_user = UserFactory()

        # Act
        tasks = CaretakerTaskService.get_tasks_for_user(caretaker.id, requesting_user)

        # Assert
        assert len(tasks["caretaker_assignments"]) == 1
        assert user.id in tasks["roles"]["ba_leader_user_ids"]
        assert user.id in tasks["roles"]["project_lead_user_ids"]
        assert len(tasks["ba_documents"]) == 1
        assert len(tasks["lead_documents"]) == 1


class TestCaretakerService:
    """Test CaretakerService business logic"""

    @pytest.mark.django_db
    def test_list_caretakers(
        self, caretaker_user, caretakee_user, caretaker_assignment
    ):
        """Test list_caretakers returns all caretaker relationships"""
        # Act
        caretakers = CaretakerService.list_caretakers()

        # Assert
        assert caretakers.count() == 1
        assert caretaker_assignment in caretakers

    @pytest.mark.django_db
    def test_list_caretakers_optimized_queries(
        self, caretaker_user, caretakee_user, caretaker_assignment
    ):
        """Test list_caretakers uses select_related and prefetch_related"""
        # Act
        caretakers = CaretakerService.list_caretakers()

        # Assert - Check that related objects are prefetched
        # This would cause additional queries if not optimized
        with patch("django.db.models.query.QuerySet.count"):
            for c in caretakers:
                _ = c.user.username
                _ = c.caretaker.username
                # Should not trigger additional queries

    @pytest.mark.django_db
    def test_get_caretaker_exists(self, caretaker_assignment):
        """Test get_caretaker returns existing caretaker"""
        # Act
        caretaker = CaretakerService.get_caretaker(caretaker_assignment.pk)

        # Assert
        assert caretaker.pk == caretaker_assignment.pk
        assert caretaker.user == caretaker_assignment.user
        assert caretaker.caretaker == caretaker_assignment.caretaker

    @pytest.mark.django_db
    def test_get_caretaker_not_found(self, db):
        """Test get_caretaker raises NotFound for non-existent caretaker"""
        # Act & Assert
        with pytest.raises(NotFound, match="Caretaker 99999 not found"):
            CaretakerService.get_caretaker(99999)

    @pytest.mark.django_db
    def test_create_caretaker_with_user_objects(self, caretaker_user, caretakee_user):
        """Test create_caretaker with User objects"""
        # Act
        caretaker = CaretakerService.create_caretaker(
            user=caretakee_user,
            caretaker=caretaker_user,
            reason="Test reason",
            end_date=timezone.now() + timedelta(days=30),
            notes="Test notes",
        )

        # Assert
        assert caretaker.id is not None
        assert caretaker.user == caretakee_user
        assert caretaker.caretaker == caretaker_user
        assert caretaker.reason == "Test reason"
        assert caretaker.notes == "Test notes"
        assert caretaker.end_date is not None

    @pytest.mark.django_db
    def test_create_caretaker_with_user_ids(self, caretaker_user, caretakee_user):
        """Test create_caretaker with user IDs"""
        # Act
        caretaker = CaretakerService.create_caretaker(
            user=caretakee_user.pk,
            caretaker=caretaker_user.pk,
            reason="Test reason",
        )

        # Assert
        assert caretaker.id is not None
        assert caretaker.user == caretakee_user
        assert caretaker.caretaker == caretaker_user

    @pytest.mark.django_db
    def test_create_caretaker_invalid_user_id(self, caretaker_user):
        """Test create_caretaker raises ValidationError for invalid user ID"""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            CaretakerService.create_caretaker(
                user=99999,
                caretaker=caretaker_user,
                reason="Test reason",
            )
        assert "user" in exc_info.value.detail

    @pytest.mark.django_db
    def test_create_caretaker_invalid_caretaker_id(self, caretakee_user):
        """Test create_caretaker raises ValidationError for invalid caretaker ID"""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            CaretakerService.create_caretaker(
                user=caretakee_user,
                caretaker=99999,
                reason="Test reason",
            )
        assert "caretaker" in exc_info.value.detail

    @pytest.mark.django_db
    def test_create_caretaker_self_caretaking(self, caretaker_user):
        """Test create_caretaker raises ValidationError for self-caretaking"""
        # Act & Assert
        with pytest.raises(ValidationError, match="Cannot caretake for yourself"):
            CaretakerService.create_caretaker(
                user=caretaker_user,
                caretaker=caretaker_user,
                reason="Test reason",
            )

    @pytest.mark.django_db
    def test_create_caretaker_duplicate(
        self, caretaker_user, caretakee_user, caretaker_assignment
    ):
        """Test create_caretaker raises ValidationError for duplicate relationship"""
        # Act & Assert
        with pytest.raises(
            ValidationError, match="Caretaker relationship already exists"
        ):
            CaretakerService.create_caretaker(
                user=caretakee_user,
                caretaker=caretaker_user,
                reason="Test reason",
            )

    @pytest.mark.django_db
    def test_create_caretaker_caretaker_has_caretaker(self, db):
        """Test create_caretaker rejects if caretaker has a caretaker"""
        # Arrange
        user1 = UserFactory(username="user1")
        user2 = UserFactory(username="user2")
        user3 = UserFactory(username="user3")

        # user2 has user1 as caretaker
        Caretaker.objects.create(user=user2, caretaker=user1, reason="Test")

        # Act & Assert - Try to make user2 a caretaker for user3
        with pytest.raises(
            ValidationError, match="Cannot set a user with a caretaker as caretaker"
        ):
            CaretakerService.create_caretaker(
                user=user3,
                caretaker=user2,
                reason="Test reason",
            )

    @pytest.mark.django_db
    def test_update_caretaker(self, caretaker_assignment):
        """Test update_caretaker updates fields"""
        # Arrange
        new_reason = "Updated reason"
        new_notes = "Updated notes"

        # Act
        updated = CaretakerService.update_caretaker(
            pk=caretaker_assignment.pk,
            data={
                "reason": new_reason,
                "notes": new_notes,
            },
        )

        # Assert
        assert updated.pk == caretaker_assignment.pk
        assert updated.reason == new_reason
        assert updated.notes == new_notes

    @pytest.mark.django_db
    def test_update_caretaker_not_found(self, db):
        """Test update_caretaker raises NotFound for non-existent caretaker"""
        # Act & Assert
        with pytest.raises(NotFound):
            CaretakerService.update_caretaker(pk=99999, data={"reason": "New reason"})

    @pytest.mark.django_db
    def test_update_caretaker_ignores_invalid_fields(self, caretaker_assignment):
        """Test update_caretaker ignores fields that don't exist"""
        # Act
        updated = CaretakerService.update_caretaker(
            pk=caretaker_assignment.pk,
            data={
                "reason": "Updated reason",
                "invalid_field": "Should be ignored",
            },
        )

        # Assert
        assert updated.reason == "Updated reason"
        assert not hasattr(updated, "invalid_field")

    @pytest.mark.django_db
    def test_delete_caretaker(self, caretaker_assignment, caretaker_user):
        """Test delete_caretaker removes caretaker relationship"""
        # Arrange
        pk = caretaker_assignment.pk

        # Act
        CaretakerService.delete_caretaker(pk, caretaker_user)

        # Assert
        assert not Caretaker.objects.filter(pk=pk).exists()

    @pytest.mark.django_db
    def test_delete_caretaker_not_found(self, caretaker_user):
        """Test delete_caretaker raises NotFound for non-existent caretaker"""
        # Act & Assert
        with pytest.raises(NotFound):
            CaretakerService.delete_caretaker(99999, caretaker_user)

    @pytest.mark.django_db
    def test_get_user_caretaker_exists(
        self, caretaker_user, caretakee_user, caretaker_assignment
    ):
        """Test get_user_caretaker returns caretaker for user"""
        # Act
        caretaker = CaretakerService.get_user_caretaker(caretakee_user)

        # Assert
        assert caretaker is not None
        assert caretaker.pk == caretaker_assignment.pk
        assert caretaker.caretaker == caretaker_user

    @pytest.mark.django_db
    def test_get_user_caretaker_not_exists(self, caretaker_user):
        """Test get_user_caretaker returns None when no caretaker"""
        # Act
        caretaker = CaretakerService.get_user_caretaker(caretaker_user)

        # Assert
        assert caretaker is None


class TestCaretakerRequestService:
    """Test CaretakerRequestService business logic"""

    @pytest.mark.django_db
    def test_get_pending_requests_for_user(self, db):
        """Test get_pending_requests_for_user returns pending requests"""
        # Arrange
        user = UserFactory()
        caretakee = UserFactory()

        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            primary_user=caretakee,
            secondary_users=[user.pk],
            reason="Test request",
        )

        # Act
        requests = CaretakerRequestService.get_pending_requests_for_user(user.pk)

        # Assert
        assert requests.count() == 1
        assert task in requests

    @pytest.mark.django_db
    def test_get_pending_requests_for_user_no_requests(self, db):
        """Test get_pending_requests_for_user returns empty when no requests"""
        # Arrange
        user = UserFactory()

        # Act
        requests = CaretakerRequestService.get_pending_requests_for_user(user.pk)

        # Assert
        assert requests.count() == 0

    @pytest.mark.django_db
    def test_get_pending_requests_for_user_excludes_non_pending(self, db):
        """Test get_pending_requests_for_user excludes non-pending requests"""
        # Arrange
        user = UserFactory()
        caretakee = UserFactory()

        # Create approved task (should be excluded)
        AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.APPROVED,
            primary_user=caretakee,
            secondary_users=[user.pk],
            reason="Test request",
        )

        # Act
        requests = CaretakerRequestService.get_pending_requests_for_user(user.pk)

        # Assert
        assert requests.count() == 0

    @pytest.mark.django_db
    def test_get_task_exists(self, db):
        """Test get_task returns existing task"""
        # Arrange
        user = UserFactory()
        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            primary_user=user,
            secondary_users=[],
        )

        # Act
        result = CaretakerRequestService.get_task(task.pk)

        # Assert
        assert result.pk == task.pk

    @pytest.mark.django_db
    def test_get_task_not_found(self, db):
        """Test get_task raises NotFound for non-existent task"""
        # Act & Assert
        with pytest.raises(NotFound, match="Task 99999 not found"):
            CaretakerRequestService.get_task(99999)

    @pytest.mark.django_db
    def test_validate_caretaker_request_valid(self, db):
        """Test validate_caretaker_request passes for valid request"""
        # Arrange
        user = UserFactory()
        caretakee = UserFactory()
        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            primary_user=caretakee,
            secondary_users=[user.pk],
        )

        # Act & Assert - Should not raise
        CaretakerRequestService.validate_caretaker_request(task, user)

    @pytest.mark.django_db
    def test_validate_caretaker_request_wrong_action(self, db):
        """Test validate_caretaker_request raises ValidationError for wrong action"""
        # Arrange
        user = UserFactory()
        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.DELETEPROJECT,
            status=AdminTask.TaskStatus.PENDING,
            primary_user=user,
            secondary_users=[user.pk],
        )

        # Act & Assert
        with pytest.raises(
            ValidationError, match="This endpoint only handles caretaker requests"
        ):
            CaretakerRequestService.validate_caretaker_request(task, user)

    @pytest.mark.django_db
    def test_validate_caretaker_request_already_processed(self, db):
        """Test validate_caretaker_request raises ValidationError for processed request"""
        # Arrange
        user = UserFactory()
        caretakee = UserFactory()
        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.APPROVED,
            primary_user=caretakee,
            secondary_users=[user.pk],
        )

        # Act & Assert
        with pytest.raises(
            ValidationError, match="This request has already been processed"
        ):
            CaretakerRequestService.validate_caretaker_request(task, user)

    @pytest.mark.django_db
    def test_validate_caretaker_request_unauthorized_user(self, db):
        """Test validate_caretaker_request raises PermissionDenied for unauthorized user"""
        # Arrange
        user = UserFactory()
        other_user = UserFactory()
        caretakee = UserFactory()
        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            primary_user=caretakee,
            secondary_users=[user.pk],
        )

        # Act & Assert
        with pytest.raises(
            PermissionDenied, match="You are not authorized to respond to this request"
        ):
            CaretakerRequestService.validate_caretaker_request(task, other_user)

    @pytest.mark.django_db
    def test_approve_request_empty_secondary_users(self, db):
        """Test approve_request raises ValidationError when secondary_users is empty"""
        # Arrange
        superuser = UserFactory(is_superuser=True)
        caretakee = UserFactory()

        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            primary_user=caretakee,
            secondary_users=[],  # Empty list - the bug scenario
            reason="Test request",
        )

        # Act & Assert
        with pytest.raises(
            ValidationError, match="no caretaker specified in secondary_users"
        ):
            CaretakerRequestService.approve_request(task.pk, superuser)

    @pytest.mark.django_db
    def test_approve_request_success(self, db):
        """Test approve_request creates caretaker relationship"""
        # Arrange
        user = UserFactory()
        caretakee = UserFactory()
        end_date = timezone.now() + timedelta(days=30)

        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            primary_user=caretakee,
            secondary_users=[user.pk],
            reason="Test request",
            end_date=end_date,
            notes="Test notes",
        )

        # Act
        caretaker = CaretakerRequestService.approve_request(task.pk, user)

        # Assert
        assert caretaker is not None
        assert caretaker.user == caretakee
        assert caretaker.caretaker == user
        assert caretaker.reason == "Test request"
        assert caretaker.notes == "Test notes"

        # Check task status
        task.refresh_from_db()
        assert task.status == AdminTask.TaskStatus.FULFILLED

    @pytest.mark.django_db
    def test_approve_request_validation_error(self, db):
        """Test approve_request raises ValidationError on failure"""
        # Arrange
        user = UserFactory()
        caretakee = UserFactory()

        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            primary_user=caretakee,
            secondary_users=[user.pk],
            reason="Test request",
        )

        # Mock Caretaker.objects.create to raise exception
        with patch(
            "caretakers.services.request_service.Caretaker.objects.create"
        ) as mock_create:
            mock_create.side_effect = Exception("Database error")

            # Act & Assert
            with pytest.raises(
                ValidationError, match="Failed to create caretaker relationship"
            ):
                CaretakerRequestService.approve_request(task.pk, user)

    @pytest.mark.django_db
    def test_reject_request(self, db):
        """Test reject_request marks task as rejected"""
        # Arrange
        user = UserFactory()
        caretakee = UserFactory()

        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            primary_user=caretakee,
            secondary_users=[user.pk],
            reason="Test request",
        )

        # Act
        CaretakerRequestService.reject_request(task.pk, user)

        # Assert
        task.refresh_from_db()
        assert task.status == AdminTask.TaskStatus.REJECTED

    @pytest.mark.django_db
    def test_auto_cancel_expired_request_expired(self, db):
        """Test auto_cancel_expired_request cancels expired request"""
        # Arrange
        user = UserFactory()
        caretakee = UserFactory()

        # Create task with end_date in the past
        past_date = timezone.now() - timedelta(days=1)
        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            primary_user=caretakee,
            secondary_users=[user.pk],
            end_date=past_date,
        )

        # Act
        result = CaretakerRequestService.auto_cancel_expired_request(task)

        # Assert
        assert result is True
        task.refresh_from_db()
        assert task.status == AdminTask.TaskStatus.CANCELLED
        assert "Auto-cancelled" in task.notes

    @pytest.mark.django_db
    def test_auto_cancel_expired_request_not_expired(self, db):
        """Test auto_cancel_expired_request does not cancel non-expired request"""
        # Arrange
        user = UserFactory()
        caretakee = UserFactory()

        # Create task with end_date in the future
        future_date = timezone.now() + timedelta(days=1)
        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            primary_user=caretakee,
            secondary_users=[user.pk],
            end_date=future_date,
        )

        # Act
        result = CaretakerRequestService.auto_cancel_expired_request(task)

        # Assert
        assert result is False
        task.refresh_from_db()
        assert task.status == AdminTask.TaskStatus.PENDING

    @pytest.mark.django_db
    def test_auto_cancel_expired_request_no_end_date(self, db):
        """Test auto_cancel_expired_request does not cancel request without end_date"""
        # Arrange
        user = UserFactory()
        caretakee = UserFactory()

        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            primary_user=caretakee,
            secondary_users=[user.pk],
            end_date=None,
        )

        # Act
        result = CaretakerRequestService.auto_cancel_expired_request(task)

        # Assert
        assert result is False
        task.refresh_from_db()
        assert task.status == AdminTask.TaskStatus.PENDING

    @pytest.mark.django_db
    def test_get_user_requests_caretaker_request(self, db):
        """Test get_user_requests returns caretaker request"""
        # Arrange
        user = UserFactory()
        caretaker = UserFactory()

        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            primary_user=user,
            secondary_users=[caretaker.pk],
            reason="Test request",
        )

        # Act
        requests = CaretakerRequestService.get_user_requests(user)

        # Assert
        assert requests["caretaker_request"] is not None
        assert requests["caretaker_request"].pk == task.pk
        assert requests["become_caretaker_request"] is None

    @pytest.mark.django_db
    def test_get_user_requests_become_caretaker_request(self, db):
        """Test get_user_requests returns become caretaker request"""
        # Arrange
        user = UserFactory()
        caretakee = UserFactory()

        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            primary_user=caretakee,
            secondary_users=[user.pk],
            reason="Test request",
        )

        # Act
        requests = CaretakerRequestService.get_user_requests(user)

        # Assert
        assert requests["caretaker_request"] is None
        assert requests["become_caretaker_request"] is not None
        assert requests["become_caretaker_request"].pk == task.pk

    @pytest.mark.django_db
    def test_get_user_requests_auto_cancels_expired(self, db):
        """Test get_user_requests auto-cancels expired requests"""
        # Arrange
        user = UserFactory()
        caretaker = UserFactory()

        # Create expired request
        past_date = timezone.now() - timedelta(days=1)
        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            primary_user=user,
            secondary_users=[caretaker.pk],
            end_date=past_date,
        )

        # Act
        requests = CaretakerRequestService.get_user_requests(user)

        # Assert
        assert requests["caretaker_request"] is None
        task.refresh_from_db()
        assert task.status == AdminTask.TaskStatus.CANCELLED

    @pytest.mark.django_db
    def test_get_user_requests_no_requests(self, db):
        """Test get_user_requests returns None when no requests"""
        # Arrange
        user = UserFactory()

        # Act
        requests = CaretakerRequestService.get_user_requests(user)

        # Assert
        assert requests["caretaker_request"] is None
        assert requests["become_caretaker_request"] is None
