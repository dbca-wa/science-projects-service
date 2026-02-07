"""
Tests for project permissions
"""

from unittest.mock import Mock

from projects.permissions.project_permissions import (
    CanEditProject,
    CanManageProjectMembers,
    CanViewProject,
    IsProjectLeader,
    IsProjectMember,
)


class TestCanViewProject:
    """Tests for CanViewProject permission"""

    def test_authenticated_user_has_permission(self, user, db):
        """Test authenticated user has view permission"""
        # Arrange
        request = Mock(user=user)
        permission = CanViewProject()

        # Act
        result = permission.has_permission(request, None)

        # Assert
        assert result is True

    def test_unauthenticated_user_no_permission(self, db):
        """Test unauthenticated user has no view permission"""
        # Arrange
        user = Mock(is_authenticated=False)
        request = Mock(user=user)
        permission = CanViewProject()

        # Act
        result = permission.has_permission(request, None)

        # Assert
        assert result is False

    def test_authenticated_user_can_view_any_project(self, user, project, db):
        """Test authenticated user can view any project"""
        # Arrange
        request = Mock(user=user)
        permission = CanViewProject()

        # Act
        result = permission.has_object_permission(request, None, project)

        # Assert
        assert result is True

    def test_unauthenticated_user_cannot_view_project(self, project, db):
        """Test unauthenticated user cannot view project"""
        # Arrange
        user = Mock(is_authenticated=False)
        request = Mock(user=user)
        permission = CanViewProject()

        # Act
        result = permission.has_object_permission(request, None, project)

        # Assert
        assert result is False


class TestCanEditProject:
    """Tests for CanEditProject permission"""

    def test_authenticated_user_has_permission(self, user, db):
        """Test authenticated user has base permission"""
        # Arrange
        request = Mock(user=user)
        permission = CanEditProject()

        # Act
        result = permission.has_permission(request, None)

        # Assert
        assert result is True

    def test_unauthenticated_user_no_permission(self, db):
        """Test unauthenticated user has no permission"""
        # Arrange
        user = Mock(is_authenticated=False)
        request = Mock(user=user)
        permission = CanEditProject()

        # Act
        result = permission.has_permission(request, None)

        # Assert
        assert result is False

    def test_superuser_can_edit_any_project(self, superuser, project, db):
        """Test superuser can edit any project"""
        # Arrange
        request = Mock(user=superuser)
        permission = CanEditProject()

        # Act
        result = permission.has_object_permission(request, None, project)

        # Assert
        assert result is True

    def test_project_leader_can_edit(self, project_with_lead, project_lead, db):
        """Test project leader can edit their project"""
        # Arrange
        request = Mock(user=project_lead)
        permission = CanEditProject()

        # Act
        result = permission.has_object_permission(request, None, project_with_lead)

        # Assert
        assert result is True

    def test_non_leader_member_cannot_edit(
        self, project_with_members, user_factory, db
    ):
        """Test non-leader member cannot edit project"""
        # Arrange
        # Get a non-leader member
        non_leader_member = project_with_members.members.filter(is_leader=False).first()
        request = Mock(user=non_leader_member.user)
        permission = CanEditProject()

        # Act
        result = permission.has_object_permission(request, None, project_with_members)

        # Assert
        assert result is False

    def test_non_member_cannot_edit(self, project, user_factory, db):
        """Test non-member cannot edit project"""
        # Arrange
        other_user = user_factory()
        request = Mock(user=other_user)
        permission = CanEditProject()

        # Act
        result = permission.has_object_permission(request, None, project)

        # Assert
        assert result is False


class TestCanManageProjectMembers:
    """Tests for CanManageProjectMembers permission"""

    def test_authenticated_user_has_permission(self, user, db):
        """Test authenticated user has base permission"""
        # Arrange
        request = Mock(user=user)
        permission = CanManageProjectMembers()

        # Act
        result = permission.has_permission(request, None)

        # Assert
        assert result is True

    def test_unauthenticated_user_no_permission(self, db):
        """Test unauthenticated user has no permission"""
        # Arrange
        user = Mock(is_authenticated=False)
        request = Mock(user=user)
        permission = CanManageProjectMembers()

        # Act
        result = permission.has_permission(request, None)

        # Assert
        assert result is False

    def test_superuser_can_manage_members(self, superuser, project, db):
        """Test superuser can manage members of any project"""
        # Arrange
        request = Mock(user=superuser)
        permission = CanManageProjectMembers()

        # Act
        result = permission.has_object_permission(request, None, project)

        # Assert
        assert result is True

    def test_project_leader_can_manage_members(
        self, project_with_lead, project_lead, db
    ):
        """Test project leader can manage members"""
        # Arrange
        request = Mock(user=project_lead)
        permission = CanManageProjectMembers()

        # Act
        result = permission.has_object_permission(request, None, project_with_lead)

        # Assert
        assert result is True

    def test_non_leader_member_cannot_manage_members(self, project_with_members, db):
        """Test non-leader member cannot manage members"""
        # Arrange
        non_leader_member = project_with_members.members.filter(is_leader=False).first()
        request = Mock(user=non_leader_member.user)
        permission = CanManageProjectMembers()

        # Act
        result = permission.has_object_permission(request, None, project_with_members)

        # Assert
        assert result is False

    def test_non_member_cannot_manage_members(self, project, user_factory, db):
        """Test non-member cannot manage members"""
        # Arrange
        other_user = user_factory()
        request = Mock(user=other_user)
        permission = CanManageProjectMembers()

        # Act
        result = permission.has_object_permission(request, None, project)

        # Assert
        assert result is False


class TestIsProjectLeader:
    """Tests for IsProjectLeader permission"""

    def test_authenticated_user_has_permission(self, user, db):
        """Test authenticated user has base permission"""
        # Arrange
        request = Mock(user=user)
        permission = IsProjectLeader()

        # Act
        result = permission.has_permission(request, None)

        # Assert
        assert result is True

    def test_unauthenticated_user_no_permission(self, db):
        """Test unauthenticated user has no permission"""
        # Arrange
        user = Mock(is_authenticated=False)
        request = Mock(user=user)
        permission = IsProjectLeader()

        # Act
        result = permission.has_permission(request, None)

        # Assert
        assert result is False

    def test_superuser_is_project_leader(self, superuser, project, db):
        """Test superuser is considered project leader"""
        # Arrange
        request = Mock(user=superuser)
        permission = IsProjectLeader()

        # Act
        result = permission.has_object_permission(request, None, project)

        # Assert
        assert result is True

    def test_project_leader_passes_check(self, project_with_lead, project_lead, db):
        """Test project leader passes leader check"""
        # Arrange
        request = Mock(user=project_lead)
        permission = IsProjectLeader()

        # Act
        result = permission.has_object_permission(request, None, project_with_lead)

        # Assert
        assert result is True

    def test_non_leader_member_fails_check(self, project_with_members, db):
        """Test non-leader member fails leader check"""
        # Arrange
        non_leader_member = project_with_members.members.filter(is_leader=False).first()
        request = Mock(user=non_leader_member.user)
        permission = IsProjectLeader()

        # Act
        result = permission.has_object_permission(request, None, project_with_members)

        # Assert
        assert result is False

    def test_non_member_fails_check(self, project, user_factory, db):
        """Test non-member fails leader check"""
        # Arrange
        other_user = user_factory()
        request = Mock(user=other_user)
        permission = IsProjectLeader()

        # Act
        result = permission.has_object_permission(request, None, project)

        # Assert
        assert result is False


class TestIsProjectMember:
    """Tests for IsProjectMember permission"""

    def test_authenticated_user_has_permission(self, user, db):
        """Test authenticated user has base permission"""
        # Arrange
        request = Mock(user=user)
        permission = IsProjectMember()

        # Act
        result = permission.has_permission(request, None)

        # Assert
        assert result is True

    def test_unauthenticated_user_no_permission(self, db):
        """Test unauthenticated user has no permission"""
        # Arrange
        user = Mock(is_authenticated=False)
        request = Mock(user=user)
        permission = IsProjectMember()

        # Act
        result = permission.has_permission(request, None)

        # Assert
        assert result is False

    def test_superuser_is_project_member(self, superuser, project, db):
        """Test superuser is considered project member"""
        # Arrange
        request = Mock(user=superuser)
        permission = IsProjectMember()

        # Act
        result = permission.has_object_permission(request, None, project)

        # Assert
        assert result is True

    def test_project_leader_is_member(self, project_with_lead, project_lead, db):
        """Test project leader is considered a member"""
        # Arrange
        request = Mock(user=project_lead)
        permission = IsProjectMember()

        # Act
        result = permission.has_object_permission(request, None, project_with_lead)

        # Assert
        assert result is True

    def test_non_leader_member_is_member(self, project_with_members, db):
        """Test non-leader member passes member check"""
        # Arrange
        non_leader_member = project_with_members.members.filter(is_leader=False).first()
        request = Mock(user=non_leader_member.user)
        permission = IsProjectMember()

        # Act
        result = permission.has_object_permission(request, None, project_with_members)

        # Assert
        assert result is True

    def test_non_member_fails_check(self, project, user_factory, db):
        """Test non-member fails member check"""
        # Arrange
        other_user = user_factory()
        request = Mock(user=other_user)
        permission = IsProjectMember()

        # Act
        result = permission.has_object_permission(request, None, project)

        # Assert
        assert result is False
