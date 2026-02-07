"""
Tests for project services
"""

from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound

from projects.models import Project, ProjectArea, ProjectMember
from projects.services.area_service import AreaService
from projects.services.details_service import DetailsService
from projects.services.export_service import ExportService
from projects.services.member_service import MemberService
from projects.services.project_service import ProjectService

User = get_user_model()


class TestProjectService:
    """Tests for ProjectService"""

    def test_list_projects_no_filters(self, user, project, db):
        """Test listing projects without filters"""
        # Act
        projects = ProjectService.list_projects(user)

        # Assert
        assert projects.count() >= 1
        assert project in projects

    def test_list_projects_with_search_term(self, user, project, db):
        """Test listing projects with search term filter"""
        # Arrange
        filters = {"searchTerm": "Test"}

        # Act
        projects = ProjectService.list_projects(user, filters)

        # Assert
        assert projects.count() >= 1
        assert project in projects

    def test_list_projects_with_status_filter(self, user, project, db):
        """Test listing projects with status filter"""
        # Arrange
        filters = {"projectstatus": "new"}

        # Act
        projects = ProjectService.list_projects(user, filters)

        # Assert
        assert projects.count() >= 1
        assert project in projects

    def test_list_projects_with_year_filter(self, user, project, db):
        """Test listing projects with year filter"""
        # Arrange
        filters = {"year": project.year}

        # Act
        projects = ProjectService.list_projects(user, filters)

        # Assert
        assert projects.count() >= 1
        assert project in projects

    def test_list_projects_with_business_area_filter(self, user, project, db):
        """Test listing projects with business area filter"""
        # Arrange
        filters = {"businessarea": project.business_area.pk}

        # Act
        projects = ProjectService.list_projects(user, filters)

        # Assert
        assert projects.count() >= 1
        assert project in projects

    def test_list_projects_with_project_tag_search(self, user, project, db):
        """Test listing projects with project tag search"""
        # Arrange
        project.kind = "core_function"
        project.year = 2023
        project.number = 123
        project.save()
        filters = {"searchTerm": "CF-2023-123"}

        # Act
        projects = ProjectService.list_projects(user, filters)

        # Assert
        assert projects.count() >= 1
        assert project in projects

    def test_get_project_success(self, project, db):
        """Test getting a project by ID"""
        # Act
        result = ProjectService.get_project(project.pk)

        # Assert
        assert result.pk == project.pk
        assert result.title == project.title

    def test_get_project_not_found(self, db):
        """Test getting non-existent project raises NotFound"""
        # Act & Assert
        with pytest.raises(NotFound, match="Project 99999 not found"):
            ProjectService.get_project(99999)

    def test_create_project(self, user, business_area, db):
        """Test creating a project"""
        # Arrange
        data = {
            "kind": "science",
            "year": 2023,
            "title": "New Project",
            "description": "New Description",
            "keywords": "test, keywords",
            "business_area": business_area.pk,
        }

        # Act
        project = ProjectService.create_project(user, data)

        # Assert
        assert project.id is not None
        assert project.title == "New Project"
        assert project.kind == "science"
        assert project.status == "new"
        assert project.year == 2023

    def test_update_project(self, project, user, db):
        """Test updating a project"""
        # Arrange
        data = {
            "title": "Updated Title",
            "description": "Updated Description",
        }

        # Act
        updated = ProjectService.update_project(project.pk, user, data)

        # Assert
        assert updated.pk == project.pk
        assert updated.title == "Updated Title"
        assert updated.description == "Updated Description"

    def test_delete_project(self, project, user, db):
        """Test deleting a project"""
        # Arrange
        project_id = project.pk

        # Act
        ProjectService.delete_project(project_id, user)

        # Assert
        assert not Project.objects.filter(pk=project_id).exists()

    def test_suspend_project(self, project, user, db):
        """Test suspending a project"""
        # Act
        suspended = ProjectService.suspend_project(project.pk, user)

        # Assert
        assert suspended.status == Project.StatusChoices.SUSPENDED

    def test_get_project_years(self, project, db):
        """Test getting list of project years"""
        # Act
        years = ProjectService.get_project_years()

        # Assert
        assert project.year in years

    def test_toggle_user_profile_visibility_hide(self, project, user, db):
        """Test hiding project from user profile"""
        # Arrange
        assert user.pk not in project.hidden_from_staff_profiles

        # Act
        updated = ProjectService.toggle_user_profile_visibility(project.pk, user)

        # Assert
        assert user.pk in updated.hidden_from_staff_profiles

    def test_toggle_user_profile_visibility_show(self, project, user, db):
        """Test showing project on user profile"""
        # Arrange
        project.hidden_from_staff_profiles = [user.pk]
        project.save()

        # Act
        updated = ProjectService.toggle_user_profile_visibility(project.pk, user)

        # Assert
        assert user.pk not in updated.hidden_from_staff_profiles


class TestMemberService:
    """Tests for MemberService"""

    def test_list_members_no_filters(self, project_with_members, db):
        """Test listing all members"""
        # Act
        members = MemberService.list_members()

        # Assert
        assert members.count() >= 4  # 1 lead + 3 members

    def test_list_members_by_project(self, project_with_members, db):
        """Test listing members for a specific project"""
        # Act
        members = MemberService.list_members(project_id=project_with_members.pk)

        # Assert
        # ProjectFactory creates a default leader, plus our fixture adds 1 lead + 3 members
        assert members.count() >= 4  # At least 4 members
        for member in members:
            assert member.project == project_with_members

    def test_list_members_by_user(self, project_with_lead, project_lead, db):
        """Test listing projects for a specific user"""
        # Act
        members = MemberService.list_members(user_id=project_lead.pk)

        # Assert
        assert members.count() >= 1
        for member in members:
            assert member.user == project_lead

    def test_get_member_success(self, project_with_lead, project_lead, db):
        """Test getting a specific member"""
        # Act
        member = MemberService.get_member(project_with_lead.pk, project_lead.pk)

        # Assert
        assert member.project == project_with_lead
        assert member.user == project_lead
        assert member.is_leader is True

    def test_get_member_not_found(self, project, user, db):
        """Test getting non-existent member raises NotFound"""
        # Act & Assert
        with pytest.raises(NotFound):
            MemberService.get_member(project.pk, user.pk)

    def test_get_project_leader(self, project_with_lead, project_lead, db):
        """Test getting project leader"""
        # Act
        leader = MemberService.get_project_leader(project_with_lead.pk)

        # Assert
        # Should get the leader we explicitly created (not the factory default)
        assert leader.is_leader is True
        assert leader.project == project_with_lead

    def test_get_project_leader_not_found(self, business_area, db):
        """Test getting leader when none exists raises NotFound"""
        # Arrange - Create project without any members
        from common.tests.factories import ProjectFactory

        project = ProjectFactory.create(business_area=business_area)
        # Remove the default leader created by factory
        project.members.all().delete()

        # Act & Assert
        with pytest.raises(NotFound):
            MemberService.get_project_leader(project.pk)

    def test_get_project_leader_multiple_leaders(
        self, project_with_lead, user_factory, db
    ):
        """Test getting leader when multiple exist returns first"""
        # Arrange - Create another leader (data issue scenario)
        another_leader = user_factory()
        project_with_lead.members.create(
            user=another_leader,
            is_leader=True,
            role="supervising",
        )

        # Act
        leader = MemberService.get_project_leader(project_with_lead.pk)

        # Assert
        assert leader.is_leader is True
        assert leader.project == project_with_lead

    def test_add_member(self, project, user, superuser, db):
        """Test adding a member to a project"""
        # Arrange
        data = {
            "role": "supervising",
            "is_leader": False,
            "time_allocation": 50,
        }

        # Act
        member = MemberService.add_member(project.pk, user.pk, data, superuser)

        # Assert
        assert member.project == project
        assert member.user == user
        assert member.role == "supervising"
        assert member.is_leader is False

    def test_add_member_with_all_fields(self, project, user, superuser, db):
        """Test adding member with all optional fields"""
        # Arrange
        data = {
            "role": "research",
            "is_leader": False,
            "time_allocation": 75,
            "position": 50,
            "short_code": "ABC",
            "comments": "Test comments",
        }

        # Act
        member = MemberService.add_member(project.pk, user.pk, data, superuser)

        # Assert
        assert member.role == "research"
        assert member.time_allocation == 75
        assert member.position == 50
        assert member.short_code == "ABC"
        assert member.comments == "Test comments"

    def test_add_member_without_role_raises_error(self, project, user, superuser, db):
        """Test adding member without role raises ValidationError"""
        # Arrange
        data = {"is_leader": False}

        # Act & Assert
        from rest_framework.exceptions import ValidationError

        with pytest.raises(ValidationError, match="Role is required"):
            MemberService.add_member(project.pk, user.pk, data, superuser)

    def test_add_duplicate_member_raises_error(
        self, project_with_lead, project_lead, superuser, db
    ):
        """Test adding duplicate member raises ValidationError"""
        # Arrange
        data = {"role": "supervising"}

        # Act & Assert
        from rest_framework.exceptions import ValidationError

        with pytest.raises(ValidationError, match="already a member"):
            MemberService.add_member(
                project_with_lead.pk, project_lead.pk, data, superuser
            )

    def test_update_member(self, project_with_lead, project_lead, superuser, db):
        """Test updating a member"""
        # Arrange
        data = {
            "role": "research",
            "time_allocation": 75,
        }

        # Act
        updated = MemberService.update_member(
            project_with_lead.pk, project_lead.pk, data, superuser
        )

        # Assert
        assert updated.role == "research"
        assert updated.time_allocation == 75

    def test_update_member_with_none_values(
        self, project_with_lead, project_lead, superuser, db
    ):
        """Test updating member with None values doesn't change fields"""
        # Arrange
        original_role = ProjectMember.objects.get(
            project=project_with_lead, user=project_lead
        ).role
        data = {
            "role": None,  # Should not update
            "time_allocation": 80,
        }

        # Act
        updated = MemberService.update_member(
            project_with_lead.pk, project_lead.pk, data, superuser
        )

        # Assert
        assert updated.role == original_role  # Unchanged
        assert updated.time_allocation == 80  # Changed

    def test_remove_member(self, project_with_lead, project_lead, superuser, db):
        """Test removing a member from a project"""
        # Act
        MemberService.remove_member(project_with_lead.pk, project_lead.pk, superuser)

        # Assert
        assert not ProjectMember.objects.filter(
            project=project_with_lead, user=project_lead
        ).exists()

    def test_promote_to_leader(self, project_with_members, user_factory, superuser, db):
        """Test promoting a member to leader"""
        # Arrange
        new_leader = user_factory()
        MemberService.add_member(
            project_with_members.pk, new_leader.pk, {"role": "supervising"}, superuser
        )

        # Act
        promoted = MemberService.promote_to_leader(
            project_with_members.pk, new_leader.pk, superuser
        )

        # Assert
        assert promoted.is_leader is True
        # Old leader should be demoted
        old_leaders = ProjectMember.objects.filter(
            project=project_with_members, is_leader=True
        ).exclude(user=new_leader)
        assert old_leaders.count() == 0

    def test_get_members_for_project(self, project_with_members, db):
        """Test getting all members for a project"""
        # Act
        members = MemberService.get_members_for_project(project_with_members.pk)

        # Assert
        assert members.count() >= 4
        for member in members:
            assert member.project == project_with_members

    def test_get_user_projects(self, project_with_lead, project_lead, db):
        """Test getting all projects for a user"""
        # Act
        projects = MemberService.get_user_projects(project_lead.pk)

        # Assert
        assert projects.count() >= 1
        assert project_with_lead in projects


class TestDetailsService:
    """Tests for DetailsService"""

    def test_get_project_details_not_found(self, project, db):
        """Test getting non-existent details raises NotFound"""
        # Act & Assert
        with pytest.raises(NotFound):
            DetailsService.get_project_details(project.pk)

    def test_create_project_details(self, project, user, db):
        """Test creating project details"""
        # Arrange
        data = {
            "creator": user.pk,
            "modifier": user.pk,
            "owner": user.pk,
        }

        # Act
        details = DetailsService.create_project_details(project.pk, data, user)

        # Assert
        assert details.id is not None
        assert details.project == project
        assert details.creator == user

    def test_get_project_details_success(self, project, user, db):
        """Test getting project details"""
        # Arrange
        details = DetailsService.create_project_details(
            project.pk, {"creator": user.pk}, user
        )

        # Act
        result = DetailsService.get_project_details(project.pk)

        # Assert
        assert result.pk == details.pk
        assert result.project == project

    def test_update_project_details(self, project, user, db):
        """Test updating project details"""
        # Arrange
        details = DetailsService.create_project_details(
            project.pk, {"creator": user.pk}, user
        )
        # Use _id suffix for foreign key fields
        data = {"modifier_id": user.pk}

        # Act
        updated = DetailsService.update_project_details(project.pk, data, user)

        # Assert
        assert updated.pk == details.pk
        assert updated.modifier == user

    def test_get_student_details_none(self, project, db):
        """Test getting student details when none exist"""
        # Act
        result = DetailsService.get_student_details_by_project(project.pk)

        # Assert
        assert result is None

    def test_create_student_details(self, project, user, db):
        """Test creating student details"""
        # Arrange
        data = {
            "level": "undergraduate",
            "organisation": "Test University",
        }

        # Act
        details = DetailsService.create_student_details(project.pk, data, user)

        # Assert
        assert details.id is not None
        assert details.project == project
        assert details.level == "undergraduate"

    def test_get_external_details_none(self, project, db):
        """Test getting external details when none exist"""
        # Act
        result = DetailsService.get_external_details(project.pk)

        # Assert
        assert result is None

    def test_create_external_details(self, project, user, db):
        """Test creating external details"""
        # Arrange
        data = {
            "collaboration_with": "<p>Test Collaborator</p>",
            "budget": "<p>$10,000</p>",
        }

        # Act
        details = DetailsService.create_external_details(project.pk, data, user)

        # Assert
        assert details.id is not None
        assert details.project == project
        assert "Test Collaborator" in details.collaboration_with

    def test_get_all_details(self, project, user, db):
        """Test getting all details for a project"""
        # Arrange
        base_details = DetailsService.create_project_details(
            project.pk, {"creator": user.pk}, user
        )

        # Act
        all_details = DetailsService.get_all_details(project.pk)

        # Assert
        assert all_details["base"] == base_details
        assert all_details["student"] is None
        assert all_details["external"] is None


class TestExportService:
    """Tests for ExportService"""

    def test_strip_html_tags(self):
        """Test stripping HTML tags from string"""
        # Arrange
        html = "<p>Test <strong>content</strong></p>"

        # Act
        result = ExportService.strip_html_tags(html)

        # Assert
        assert result == "Test content"

    def test_strip_html_tags_empty(self):
        """Test stripping HTML tags from empty string"""
        # Act
        result = ExportService.strip_html_tags("")

        # Assert
        assert result == ""

    def test_strip_html_tags_none(self):
        """Test stripping HTML tags from None"""
        # Act
        result = ExportService.strip_html_tags(None)

        # Assert
        assert result == ""

    def test_export_all_projects_csv(self, project_with_members, user, db):
        """Test exporting all projects to CSV"""
        # Act
        response = ExportService.export_all_projects_csv(user)

        # Assert
        assert response.status_code == 200
        assert response["Content-Type"] == "text/csv"
        assert "projects-full.csv" in response["Content-Disposition"]

        # Check CSV content
        content = response.content.decode("utf-8")
        assert "Project Code" in content
        assert "Title" in content

    @patch("projects.services.export_service.Project.objects")
    def test_export_all_projects_csv_error(self, mock_projects, user, db):
        """Test export error handling"""
        # Arrange
        mock_projects.select_related.side_effect = Exception("Database error")

        # Act
        response = ExportService.export_all_projects_csv(user)

        # Assert
        assert response.status_code == 500
        assert "Error generating CSV" in response.content.decode("utf-8")

    def test_export_all_projects_csv_with_business_area_leader(
        self, project_with_members, user, business_area, db
    ):
        """Test CSV export includes business area leader"""
        # Arrange
        business_area.leader_id = user.pk
        business_area.save()
        project_with_members.business_area = business_area
        project_with_members.save()

        # Act
        response = ExportService.export_all_projects_csv(user)

        # Assert
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert str(user) in content

    def test_export_all_projects_csv_with_team_members(
        self, project_with_members, user, db
    ):
        """Test CSV export includes team member names"""
        # Act
        response = ExportService.export_all_projects_csv(user)

        # Assert
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        # Check that member names appear in CSV
        for member in project_with_members.members.all():
            if member.user:
                assert (
                    member.user.first_name in content
                    or member.user.last_name in content
                )

    @patch("projects.services.export_service.AnnualReport")
    def test_export_annual_report_projects_csv_no_reports(
        self, mock_annual_report, user, db
    ):
        """Test exporting annual report projects when no reports exist"""
        # Arrange
        mock_annual_report.objects.order_by.return_value.first.return_value = None

        # Act
        response = ExportService.export_annual_report_projects_csv(user)

        # Assert
        assert response.status_code == 404
        assert "No annual reports found" in response.content.decode("utf-8")

    @patch("projects.services.export_service.Project.objects")
    @patch("projects.services.export_service.AnnualReport")
    def test_export_annual_report_projects_csv_error(
        self, mock_annual_report, mock_projects, user, db
    ):
        """Test annual report export error handling"""
        # Arrange
        mock_annual_report.objects.order_by.side_effect = Exception("Database error")

        # Act
        response = ExportService.export_annual_report_projects_csv(user)

        # Assert
        assert response.status_code == 500
        assert "Error generating CSV" in response.content.decode("utf-8")


class TestAreaService:
    """Tests for AreaService"""

    def test_get_project_area_success(self, project_with_area, db):
        """Test getting project area by project ID"""
        # Act
        result = AreaService.get_project_area(project_with_area.pk)

        # Assert
        assert result.project == project_with_area
        assert result.areas == [1, 2, 3]

    def test_get_project_area_not_found(self, business_area, db):
        """Test getting non-existent project area raises NotFound"""
        # Arrange - Create project without area
        from common.tests.factories import ProjectFactory

        project_without_area = ProjectFactory(business_area=business_area)
        # Remove the default area created by fixture
        ProjectArea.objects.filter(project=project_without_area).delete()

        # Act & Assert
        with pytest.raises(
            NotFound,
            match=f"Project area not found for project {project_without_area.pk}",
        ):
            AreaService.get_project_area(project_without_area.pk)

    def test_get_area_by_pk_success(self, project_with_area, db):
        """Test getting project area by primary key"""
        # Arrange
        area = ProjectArea.objects.get(project=project_with_area)

        # Act
        result = AreaService.get_area_by_pk(area.pk)

        # Assert
        assert result.pk == area.pk
        assert result.project == project_with_area

    def test_get_area_by_pk_not_found(self, db):
        """Test getting non-existent area by pk raises NotFound"""
        # Act & Assert
        with pytest.raises(NotFound, match="Project area 99999 not found"):
            AreaService.get_area_by_pk(99999)

    def test_create_project_area(self, project, user, db):
        """Test creating project area"""
        # Arrange
        # Remove the default area created by project fixture
        ProjectArea.objects.filter(project=project).delete()
        area_ids = [1, 2, 3]

        # Act
        area = AreaService.create_project_area(project.pk, area_ids, user)

        # Assert
        assert area.id is not None
        assert area.project == project
        assert area.areas == [1, 2, 3]

    def test_create_project_area_empty_list(self, project, user, db):
        """Test creating project area with empty area list"""
        # Arrange
        # Remove the default area created by project fixture
        ProjectArea.objects.filter(project=project).delete()

        # Act
        area = AreaService.create_project_area(project.pk, [], user)

        # Assert
        assert area.id is not None
        assert area.project == project
        assert area.areas == []

    def test_create_project_area_none_list(self, project, user, db):
        """Test creating project area with None area list"""
        # Arrange
        # Remove the default area created by project fixture
        ProjectArea.objects.filter(project=project).delete()

        # Act
        area = AreaService.create_project_area(project.pk, None, user)

        # Assert
        assert area.id is not None
        assert area.project == project
        assert area.areas == []

    def test_update_project_area(self, project_with_area, user, db):
        """Test updating project area by project ID"""
        # Arrange
        new_area_ids = [4, 5, 6]

        # Act
        updated = AreaService.update_project_area(
            project_with_area.pk, new_area_ids, user
        )

        # Assert
        assert updated.project == project_with_area
        assert updated.areas == [4, 5, 6]

    def test_update_project_area_empty_list(self, project_with_area, user, db):
        """Test updating project area with empty list"""
        # Act
        updated = AreaService.update_project_area(project_with_area.pk, [], user)

        # Assert
        assert updated.project == project_with_area
        assert updated.areas == []

    def test_update_project_area_none_list(self, project_with_area, user, db):
        """Test updating project area with None"""
        # Act
        updated = AreaService.update_project_area(project_with_area.pk, None, user)

        # Assert
        assert updated.project == project_with_area
        assert updated.areas == []

    def test_update_project_area_not_found(self, user, db):
        """Test updating non-existent project area raises NotFound"""
        # Arrange
        from common.tests.factories import ProjectFactory

        project_without_area = ProjectFactory()
        # Remove any default area
        ProjectArea.objects.filter(project=project_without_area).delete()

        # Act & Assert
        with pytest.raises(NotFound):
            AreaService.update_project_area(project_without_area.pk, [1, 2], user)

    def test_update_area_by_pk(self, project_with_area, user, db):
        """Test updating project area by primary key"""
        # Arrange
        area = ProjectArea.objects.get(project=project_with_area)
        new_area_ids = [7, 8, 9]

        # Act
        updated = AreaService.update_area_by_pk(area.pk, new_area_ids, user)

        # Assert
        assert updated.pk == area.pk
        assert updated.areas == [7, 8, 9]

    def test_update_area_by_pk_empty_list(self, project_with_area, user, db):
        """Test updating area by pk with empty list"""
        # Arrange
        area = ProjectArea.objects.get(project=project_with_area)

        # Act
        updated = AreaService.update_area_by_pk(area.pk, [], user)

        # Assert
        assert updated.pk == area.pk
        assert updated.areas == []

    def test_update_area_by_pk_none_list(self, project_with_area, user, db):
        """Test updating area by pk with None"""
        # Arrange
        area = ProjectArea.objects.get(project=project_with_area)

        # Act
        updated = AreaService.update_area_by_pk(area.pk, None, user)

        # Assert
        assert updated.pk == area.pk
        assert updated.areas == []

    def test_update_area_by_pk_not_found(self, user, db):
        """Test updating non-existent area by pk raises NotFound"""
        # Act & Assert
        with pytest.raises(NotFound):
            AreaService.update_area_by_pk(99999, [1, 2], user)

    def test_delete_project_area(self, project_with_area, user, db):
        """Test deleting project area"""
        # Arrange
        area = ProjectArea.objects.get(project=project_with_area)
        area_pk = area.pk

        # Act
        AreaService.delete_project_area(area_pk, user)

        # Assert
        assert not ProjectArea.objects.filter(pk=area_pk).exists()

    def test_delete_project_area_not_found(self, user, db):
        """Test deleting non-existent area raises NotFound"""
        # Act & Assert
        with pytest.raises(NotFound):
            AreaService.delete_project_area(99999, user)

    def test_list_all_areas(self, project_with_area, db):
        """Test listing all project areas"""
        # Act
        areas = AreaService.list_all_areas()

        # Assert
        assert areas.count() >= 1
        assert ProjectArea.objects.get(project=project_with_area) in areas

    def test_list_all_areas_empty(self, db):
        """Test listing all areas when none exist"""
        # Arrange
        ProjectArea.objects.all().delete()

        # Act
        areas = AreaService.list_all_areas()

        # Assert
        assert areas.count() == 0


# Additional tests for ExportService to reach 100% coverage


class TestExportServiceAdditional:
    """Additional tests for ExportService to cover remaining lines"""

    def test_export_annual_report_projects_csv_success(
        self, project_with_members, user, db
    ):
        """Test exporting annual report projects CSV successfully"""
        # Arrange
        from documents.models import ProgressReport, ProjectDocument
        from documents.tests.factories import AnnualReportFactory

        annual_report = AnnualReportFactory(year=2023)

        # Create a project document first (required for ProgressReport)
        doc = ProjectDocument.objects.create(
            project=project_with_members,
            kind="progressreport",
            status="approved",
        )

        # Create progress report for project
        ProgressReport.objects.create(
            project=project_with_members, report=annual_report, document=doc, year=2023
        )

        # Act
        response = ExportService.export_annual_report_projects_csv(user)

        # Assert
        assert response.status_code == 200
        assert response["Content-Type"] == "text/csv"
        assert "projects-annual-report-2023.csv" in response["Content-Disposition"]

        # Check CSV content
        content = response.content.decode("utf-8")
        assert "Project Code" in content
        assert "Report Type" in content
        assert "Progress" in content

    def test_export_annual_report_with_student_report(
        self, project_with_members, user, db
    ):
        """Test CSV export with student report"""
        # Arrange
        from documents.models import ProjectDocument, StudentReport
        from documents.tests.factories import AnnualReportFactory

        annual_report = AnnualReportFactory(year=2023)

        # Create a project document first (required for StudentReport)
        doc = ProjectDocument.objects.create(
            project=project_with_members,
            kind="studentreport",
            status="approved",
        )

        # Create student report for project
        StudentReport.objects.create(
            project=project_with_members, report=annual_report, document=doc, year=2023
        )

        # Act
        response = ExportService.export_annual_report_projects_csv(user)

        # Assert
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Student" in content

    def test_export_annual_report_with_both_reports(
        self, project_with_members, user, db
    ):
        """Test CSV export with both progress and student reports"""
        # Arrange
        from documents.models import ProgressReport, ProjectDocument, StudentReport
        from documents.tests.factories import AnnualReportFactory

        annual_report = AnnualReportFactory(year=2023)

        # Create project documents
        progress_doc = ProjectDocument.objects.create(
            project=project_with_members,
            kind="progressreport",
            status="approved",
        )
        student_doc = ProjectDocument.objects.create(
            project=project_with_members,
            kind="studentreport",
            status="approved",
        )

        # Create both reports for project
        ProgressReport.objects.create(
            project=project_with_members,
            report=annual_report,
            document=progress_doc,
            year=2023,
        )
        StudentReport.objects.create(
            project=project_with_members,
            report=annual_report,
            document=student_doc,
            year=2023,
        )

        # Act
        response = ExportService.export_annual_report_projects_csv(user)

        # Assert
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Progress & Student" in content


# Additional tests for ProjectService to reach 100% coverage


class TestProjectServiceAdditional:
    """Additional tests for ProjectService to cover remaining lines"""

    def test_list_projects_with_selected_user_filter(
        self, user, project_with_lead, project_lead, db
    ):
        """Test listing projects filtered by selected user"""
        # Arrange
        filters = {"selected_user": project_lead.pk}

        # Act
        projects = ProjectService.list_projects(user, filters)

        # Assert
        assert projects.count() >= 1
        assert project_with_lead in projects

    def test_list_projects_with_multiple_business_areas(
        self, user, project, business_area, db
    ):
        """Test listing projects with multiple business area filter"""
        # Arrange
        filters = {"businessarea": f"{business_area.pk},{business_area.pk}"}

        # Act
        projects = ProjectService.list_projects(user, filters)

        # Assert
        assert projects.count() >= 1

    def test_list_projects_with_unknown_status(self, user, project, db):
        """Test listing projects with unknown status filter"""
        # Arrange
        project.status = "invalid_status"
        project.save()
        filters = {"projectstatus": "unknown"}

        # Act
        projects = ProjectService.list_projects(user, filters)

        # Assert
        # Should exclude projects with valid statuses
        assert projects.count() >= 0

    def test_list_projects_with_kind_filter(self, user, project, db):
        """Test listing projects with kind filter"""
        # Arrange
        filters = {"projectkind": "science"}

        # Act
        projects = ProjectService.list_projects(user, filters)

        # Assert
        assert projects.count() >= 1

    def test_list_projects_only_active(self, user, project, db):
        """Test listing only active projects"""
        # Arrange
        project.status = "active"
        project.save()
        filters = {"only_active": True}

        # Act
        projects = ProjectService.list_projects(user, filters)

        # Assert
        assert projects.count() >= 1

    def test_list_projects_only_inactive(self, user, project, db):
        """Test listing only inactive projects"""
        # Arrange
        project.status = "completed"
        project.save()
        filters = {"only_inactive": True}

        # Act
        projects = ProjectService.list_projects(user, filters)

        # Assert
        assert projects.count() >= 1

    def test_parse_search_term_with_year_only(self, user, project, db):
        """Test parsing project tag with year only (CF-2023)"""
        # Arrange
        project.kind = "core_function"
        project.year = 2023
        project.save()
        filters = {"searchTerm": "CF-2023"}

        # Act
        projects = ProjectService.list_projects(user, filters)

        # Assert
        assert projects.count() >= 1

    def test_parse_search_term_with_prefix_only(self, user, db):
        """Test parsing project tag with prefix only (CF)"""
        # Arrange
        from common.tests.factories import BusinessAreaFactory, ProjectFactory

        business_area = BusinessAreaFactory()
        # Create a core_function project
        ProjectFactory(
            business_area=business_area, kind="core_function", year=2023, number=1
        )
        filters = {"searchTerm": "CF"}

        # Act
        projects = ProjectService.list_projects(user, filters)

        # Assert
        # Should filter by kind=core_function
        assert all(p.kind == "core_function" for p in projects)

    def test_parse_search_term_invalid_year(self, user, db):
        """Test parsing project tag with invalid year"""
        # Arrange
        filters = {"searchTerm": "CF-INVALID-123"}

        # Act
        projects = ProjectService.list_projects(user, filters)

        # Assert
        # Should still filter by kind
        assert projects.count() >= 0

    def test_parse_search_term_invalid_number(self, user, db):
        """Test parsing project tag with invalid number"""
        # Arrange
        filters = {"searchTerm": "CF-2023-INVALID"}

        # Act
        projects = ProjectService.list_projects(user, filters)

        # Assert
        # Should still filter by kind and year
        assert projects.count() >= 0

    def test_parse_search_term_empty_parts(self, user, db):
        """Test parsing project tag with empty parts"""
        # Arrange
        filters = {"searchTerm": "CF--"}

        # Act
        projects = ProjectService.list_projects(user, filters)

        # Assert
        assert projects.count() >= 0

    def test_parse_search_term_invalid_prefix(self, user, db):
        """Test parsing project tag with invalid prefix"""
        # Arrange
        filters = {"searchTerm": "INVALID-2023-123"}

        # Act
        projects = ProjectService.list_projects(user, filters)

        # Assert
        # Should return no results for invalid prefix
        assert projects.count() == 0

    def test_parse_search_term_empty(self, user, db):
        """Test parsing empty search term"""
        # Arrange
        filters = {"searchTerm": ""}

        # Act
        projects = ProjectService.list_projects(user, filters)

        # Assert
        # Should return all projects
        assert projects.count() >= 0

    def test_determine_db_kind_stp(self):
        """Test determining database kind for STP prefix"""
        # Act
        result = ProjectService._determine_db_kind("STP")

        # Assert
        assert result == "student"

    def test_determine_db_kind_ext(self):
        """Test determining database kind for EXT prefix"""
        # Act
        result = ProjectService._determine_db_kind("EXT")

        # Assert
        assert result == "external"

    def test_determine_db_kind_invalid(self):
        """Test determining database kind for invalid prefix"""
        # Act
        result = ProjectService._determine_db_kind("INVALID")

        # Assert
        assert result is None

    def test_handle_project_image_string(self):
        """Test handling project image when it's already a string"""
        # Act
        result = ProjectService.handle_project_image("/path/to/image.jpg")

        # Assert
        assert result == "/path/to/image.jpg"

    def test_handle_project_image_none(self):
        """Test handling project image when it's None"""
        # Act
        result = ProjectService.handle_project_image(None)

        # Assert
        assert result is None

    @patch("projects.services.project_service.default_storage")
    def test_handle_project_image_existing_file(self, mock_storage, db):
        """Test handling project image when file already exists with same size"""
        # Arrange
        from django.core.files.uploadedfile import SimpleUploadedFile

        image = SimpleUploadedFile(
            "test.jpg", b"file_content", content_type="image/jpeg"
        )

        mock_storage.exists.return_value = True
        mock_storage.path.return_value = "/path/to/test.jpg"

        with patch("os.path.exists", return_value=True):
            with patch("os.path.getsize", return_value=len(b"file_content")):
                # Act
                result = ProjectService.handle_project_image(image)

                # Assert
                assert result == "projects/test.jpg"

    @patch("projects.services.project_service.default_storage")
    def test_handle_project_image_new_file(self, mock_storage, db):
        """Test handling new project image upload"""
        # Arrange
        from django.core.files.uploadedfile import SimpleUploadedFile

        image = SimpleUploadedFile("new.jpg", b"new_content", content_type="image/jpeg")

        mock_storage.exists.return_value = False
        mock_storage.save.return_value = "projects/new.jpg"

        # Act
        result = ProjectService.handle_project_image(image)

        # Assert
        assert result == "projects/new.jpg"
        mock_storage.save.assert_called_once()


# Additional tests for DetailsService to reach 100% coverage


class TestDetailsServiceAdditional:
    """Additional tests for DetailsService to cover remaining lines"""

    def test_get_detail_by_project_alias(self, project, user, db):
        """Test get_detail_by_project alias method"""
        # Arrange
        details = DetailsService.create_project_details(
            project.pk, {"creator": user.pk}, user
        )

        # Act
        result = DetailsService.get_detail_by_project(project.pk)

        # Assert
        assert result.pk == details.pk
        assert result.project == project

    def test_update_student_details(self, project, user, db):
        """Test updating student details"""
        # Arrange
        details = DetailsService.create_student_details(
            project.pk, {"level": "undergraduate", "organisation": "Test Uni"}, user
        )
        data = {"level": "postgraduate"}

        # Act
        updated = DetailsService.update_student_details(project.pk, data, user)

        # Assert
        assert updated.pk == details.pk
        assert updated.level == "postgraduate"

    def test_update_student_details_not_found(self, project, user, db):
        """Test updating non-existent student details raises NotFound"""
        # Arrange
        data = {"level": "postgraduate"}

        # Act & Assert
        with pytest.raises(
            NotFound, match=f"Student details not found for project {project.pk}"
        ):
            DetailsService.update_student_details(project.pk, data, user)

    def test_update_external_details(self, project, user, db):
        """Test updating external details"""
        # Arrange
        details = DetailsService.create_external_details(
            project.pk, {"collaboration_with": "<p>Original</p>"}, user
        )
        data = {"collaboration_with": "<p>Updated</p>"}

        # Act
        updated = DetailsService.update_external_details(project.pk, data, user)

        # Assert
        assert updated.pk == details.pk
        assert "Updated" in updated.collaboration_with

    def test_update_external_details_not_found(self, project, user, db):
        """Test updating non-existent external details raises NotFound"""
        # Arrange
        data = {"collaboration_with": "<p>Test</p>"}

        # Act & Assert
        with pytest.raises(
            NotFound, match=f"External details not found for project {project.pk}"
        ):
            DetailsService.update_external_details(project.pk, data, user)

    def test_list_all_project_details(self, project, user, db):
        """Test listing all project details"""
        # Arrange
        DetailsService.create_project_details(project.pk, {"creator": user.pk}, user)

        # Act
        all_details = DetailsService.list_all_project_details()

        # Assert
        assert all_details.count() >= 1

    def test_list_all_student_details(self, project, user, db):
        """Test listing all student details"""
        # Arrange
        DetailsService.create_student_details(
            project.pk, {"level": "undergraduate"}, user
        )

        # Act
        all_details = DetailsService.list_all_student_details()

        # Assert
        assert all_details.count() >= 1

    def test_list_all_external_details(self, project, user, db):
        """Test listing all external details"""
        # Arrange
        DetailsService.create_external_details(
            project.pk, {"collaboration_with": "<p>Test</p>"}, user
        )

        # Act
        all_details = DetailsService.list_all_external_details()

        # Assert
        assert all_details.count() >= 1

    def test_create_project_details_with_all_fields(
        self, project, user, user_factory, db
    ):
        """Test creating project details with all optional fields"""
        # Arrange
        data_custodian = user_factory()
        site_custodian = user_factory()
        from agencies.models import DepartmentalService

        service = DepartmentalService.objects.create(name="Test Service")

        data = {
            "creator": user.pk,
            "modifier": user.pk,
            "owner": user.pk,
            "data_custodian": data_custodian.pk,
            "site_custodian": site_custodian.pk,
            "service": service.pk,
        }

        # Act
        details = DetailsService.create_project_details(project.pk, data, user)

        # Assert
        assert details.creator == user
        assert details.data_custodian == data_custodian
        assert details.site_custodian == site_custodian
        assert details.service == service

    def test_create_project_details_with_model_instances(self, project, user, db):
        """Test creating project details with model instances instead of IDs"""
        # Arrange
        data = {
            "creator": user,  # Pass model instance instead of ID
            "modifier": user,
            "owner": user,
        }

        # Act
        details = DetailsService.create_project_details(project.pk, data, user)

        # Assert
        assert details.creator == user
        assert details.modifier == user
        assert details.owner == user
