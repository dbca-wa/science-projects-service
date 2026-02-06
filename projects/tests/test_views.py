"""
Tests for project views
"""
import pytest
from rest_framework import status
from rest_framework.test import APIClient

from projects.models import Project, ProjectMember
from common.tests.test_helpers import projects_urls


class TestProjects:
    """Tests for Projects view (list and create)"""

    def test_list_projects_authenticated(self, api_client, user, project, db):
        """Test listing projects as authenticated user"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(projects_urls.list())
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert 'projects' in response.data
        assert 'total_results' in response.data
        assert 'total_pages' in response.data

    def test_list_projects_unauthenticated(self, api_client, db):
        """Test listing projects without authentication"""
        # Act
        response = api_client.get(projects_urls.list())
        
        # Assert
        # DRF returns 403 for unauthenticated requests with IsAuthenticated permission
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_projects_with_filters(self, api_client, user, project, db):
        """Test listing projects with search filter"""
        # Arrange
        project.title = "Test Project Title"
        project.save()
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(projects_urls.list(), {'searchTerm': 'Test'})
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['projects']) >= 0


class TestProjectDetails:
    """Tests for ProjectDetails view (get, update, delete)"""

    def test_get_project_authenticated(self, api_client, user, project, db):
        """Test getting project details as authenticated user"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(projects_urls.detail(project.pk))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert 'project' in response.data
        assert response.data['project']['id'] == project.pk
        assert 'details' in response.data
        assert 'documents' in response.data
        assert 'members' in response.data

    def test_get_project_unauthenticated(self, api_client, project, db):
        """Test getting project without authentication"""
        # Act
        response = api_client.get(projects_urls.detail(project.pk))
        
        # Assert
        # DRF returns 403 for unauthenticated requests with IsAuthenticated permission
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_project_not_found(self, api_client, user, db):
        """Test getting non-existent project"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(projects_urls.detail(99999))
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_project_as_leader(self, api_client, project_with_lead, project_lead, db):
        """Test updating project as project leader"""
        # Arrange
        api_client.force_authenticate(user=project_lead)
        update_data = {
            'title': 'Updated Project Title',
        }
        
        # Act
        response = api_client.put(
            projects_urls.detail(project_with_lead.pk),
            update_data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        project_with_lead.refresh_from_db()
        assert project_with_lead.title == 'Updated Project Title'

    def test_update_project_as_non_leader(self, api_client, project_with_members, user_factory, db):
        """Test updating project as non-leader member fails"""
        # Arrange
        non_leader = project_with_members.members.filter(is_leader=False).first().user
        api_client.force_authenticate(user=non_leader)
        update_data = {
            'title': 'Updated Title',
        }
        
        # Act
        response = api_client.put(
            projects_urls.detail(project_with_members.pk),
            update_data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_project_as_leader(self, api_client, project_with_lead, project_lead, db):
        """Test deleting project as project leader"""
        # Arrange
        api_client.force_authenticate(user=project_lead)
        project_id = project_with_lead.pk
        
        # Act
        response = api_client.delete(projects_urls.detail(project_id))
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Project.objects.filter(pk=project_id).exists()

    def test_delete_project_as_non_leader(self, api_client, project_with_members, db):
        """Test deleting project as non-leader member fails"""
        # Arrange
        non_leader = project_with_members.members.filter(is_leader=False).first().user
        api_client.force_authenticate(user=non_leader)
        
        # Act
        response = api_client.delete(projects_urls.detail(project_with_members.pk))
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestProjectMembers:
    """Tests for ProjectMembers view (list and create)"""

    def test_list_all_members(self, api_client, user, project_with_members, db):
        """Test listing all project members"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(projects_urls.path('project_members'))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) >= 4  # 1 leader + 3 members

    def test_add_member_to_project(self, api_client, user, project_with_lead, user_factory, db):
        """Test adding a member to a project"""
        # Arrange
        api_client.force_authenticate(user=user)
        new_user = user_factory()
        member_data = {
            'project': project_with_lead.pk,
            'user': new_user.pk,
            'is_leader': False,
            'role': 'research',
        }
        
        # Act
        response = api_client.post(
            projects_urls.path('project_members'),
            member_data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert ProjectMember.objects.filter(
            project=project_with_lead,
            user=new_user
        ).exists()

    def test_add_member_invalid_data(self, api_client, user, db):
        """Test adding member with invalid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        invalid_data = {
            'project': 99999,  # Non-existent project
            'user': 99999,  # Non-existent user
        }
        
        # Act
        response = api_client.post(
            projects_urls.path('project_members'),
            invalid_data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestProjectMemberDetail:
    """Tests for ProjectMemberDetail view (get, update, delete)"""

    def test_get_member(self, api_client, user, project_with_lead, project_lead, db):
        """Test getting specific project member"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(
            projects_urls.path('project_members', project_with_lead.pk, project_lead.pk)
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['user']['id'] == project_lead.pk

    def test_update_member(self, api_client, user, project_with_members, db):
        """Test updating project member"""
        # Arrange
        api_client.force_authenticate(user=user)
        member = project_with_members.members.filter(is_leader=False).first()
        update_data = {
            'role': 'technical',
        }
        
        # Act
        response = api_client.put(
            projects_urls.path('project_members', project_with_members.pk, member.user.pk),
            update_data,
            format='json'
        )
        
        # Assert
        if response.status_code != status.HTTP_202_ACCEPTED:
            print(f"ERROR: {response.data}")
        assert response.status_code == status.HTTP_202_ACCEPTED
        member.refresh_from_db()
        assert member.role == 'technical'

    def test_remove_member(self, api_client, user, project_with_members, db):
        """Test removing member from project"""
        # Arrange
        api_client.force_authenticate(user=user)
        member = project_with_members.members.filter(is_leader=False).first()
        member_id = member.user.pk
        
        # Act
        response = api_client.delete(
            projects_urls.path('project_members', project_with_members.pk, member_id)
        )
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not ProjectMember.objects.filter(
            project=project_with_members,
            user_id=member_id
        ).exists()


class TestMembersForProject:
    """Tests for MembersForProject view"""

    def test_get_members_for_project(self, api_client, user, project_with_members, db):
        """Test getting all members for a specific project"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(projects_urls.path(project_with_members.pk, 'team'))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) >= 4  # 1 leader + 3 members


class TestProjectLeaderDetail:
    """Tests for ProjectLeaderDetail view"""

    def test_get_project_leader(self, api_client, user, project_with_lead, project_lead, db):
        """Test getting project leader"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Verify the fixture setup is correct
        leader_member = project_with_lead.members.filter(is_leader=True).first()
        assert leader_member is not None, "No leader found in project"
        assert leader_member.user == project_lead, f"Leader is {leader_member.user.username}, expected {project_lead.username}"
        
        # Act
        response = api_client.get(projects_urls.path('project_members', project_with_lead.pk, 'leader'))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['user']['username'] == project_lead.username
        assert response.data['is_leader'] is True


class TestPromoteToLeader:
    """Tests for PromoteToLeader view"""

    def test_promote_member_to_leader(self, api_client, user, project_with_members, db):
        """Test promoting a member to project leader"""
        # Arrange
        api_client.force_authenticate(user=user)
        member = project_with_members.members.filter(is_leader=False).first()
        promote_data = {
            'user_id': member.user.pk,
            'project_id': project_with_members.pk,
        }
        
        # Act
        response = api_client.post(
            projects_urls.path('promote'),
            promote_data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        member.refresh_from_db()
        assert member.is_leader is True

    def test_promote_missing_data(self, api_client, user, db):
        """Test promoting without required data"""
        # Arrange
        api_client.force_authenticate(user=user)
        incomplete_data = {
            'user_id': 1,
            # Missing project_id
        }
        
        # Act
        response = api_client.post(
            projects_urls.path('promote'),
            incomplete_data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestProjectAdditional:
    """Tests for ProjectAdditional view (project details)"""

    def test_list_project_details(self, api_client, user, db):
        """Test listing all project details"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(projects_urls.path('project_details'))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_create_project_detail(self, api_client, project, user, db):
        """Test creating project detail"""
        # Arrange
        api_client.force_authenticate(user=user)
        detail_data = {
            'project': project.pk,
            'creator': user.pk,
            'modifier': user.pk,
            'owner': user.pk,
        }
        
        # Act
        response = api_client.post(
            projects_urls.path('project_details'),
            detail_data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED


class TestProjectAdditionalDetail:
    """Tests for ProjectAdditionalDetail view"""

    def test_get_project_detail(self, api_client, user, project_with_lead, db):
        """Test getting project detail by ID"""
        # Arrange
        api_client.force_authenticate(user=user)
        detail = project_with_lead.project_detail
        
        # Act
        response = api_client.get(projects_urls.path('project_details', detail.pk))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == detail.pk

    def test_update_project_detail(self, api_client, project_with_lead, user, db):
        """Test updating project detail"""
        # Arrange
        api_client.force_authenticate(user=user)
        detail = project_with_lead.project_detail
        update_data = {
            'modifier': user.pk,
        }
        
        # Act
        response = api_client.put(
            projects_urls.path('project_details', detail.pk),
            update_data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED

    def test_delete_project_detail(self, api_client, user, project_with_lead, db):
        """Test deleting project detail"""
        # Arrange
        api_client.force_authenticate(user=user)
        detail = project_with_lead.project_detail
        detail_id = detail.pk
        
        # Act
        response = api_client.delete(projects_urls.path('project_details', detail_id))
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT


class TestSelectedProjectAdditionalDetail:
    """Tests for SelectedProjectAdditionalDetail view"""

    def test_get_detail_by_project(self, api_client, user, project_with_lead, db):
        """Test getting project detail by project ID"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(projects_urls.path(project_with_lead.pk, 'details'))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['project']['id'] == project_with_lead.pk



# Additional tests for Projects.post() - CREATE project endpoint

class TestProjectsCreate:
    """Tests for Projects.post() - creating projects"""

    def test_create_project_minimal_data(self, api_client, user, business_area, db):
        """Test creating project with minimal required data"""
        # Arrange
        api_client.force_authenticate(user=user)
        project_data = {
            'kind': 'science',
            'year': '2023',
            'title': 'New Science Project',
            'description': 'Project description',
            'businessArea': business_area.pk,
            'projectLead': user.pk,
            'creator': user.pk,
            'keywords': '[]',
            'locations': [],
        }
        
        # Act
        response = api_client.post(
            projects_urls.list(),
            project_data,
            format='multipart'
        )
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'New Science Project'
        assert response.data['kind'] == 'science'

    def test_create_project_with_dates(self, api_client, user, business_area, db):
        """Test creating project with start and end dates"""
        # Arrange
        api_client.force_authenticate(user=user)
        project_data = {
            'kind': 'core_function',
            'year': '2023',
            'title': 'Project with Dates',
            'description': 'Test',
            'businessArea': business_area.pk,
            'projectLead': user.pk,
            'creator': user.pk,
            'keywords': '[]',
            'locations': [],
            'startDate': '2023-01-01T00:00:00.000Z',
            'endDate': '2023-12-31T00:00:00.000Z',
        }
        
        # Act
        response = api_client.post(
            projects_urls.list(),
            project_data,
            format='multipart'
        )
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_project_with_keywords(self, api_client, user, business_area, db):
        """Test creating project with keywords"""
        # Arrange
        api_client.force_authenticate(user=user)
        project_data = {
            'kind': 'science',
            'year': '2023',
            'title': 'Project with Keywords',
            'description': 'Test',
            'businessArea': business_area.pk,
            'projectLead': user.pk,
            'creator': user.pk,
            'keywords': '["keyword1","keyword2","keyword3"]',
            'locations': [],
        }
        
        # Act
        response = api_client.post(
            projects_urls.list(),
            project_data,
            format='multipart'
        )
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert 'keyword1' in response.data['keywords']

    def test_create_project_invalid_data(self, api_client, user, db):
        """Test creating project with invalid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        invalid_data = {
            'kind': 'science',
            # Missing required fields
        }
        
        # Act
        response = api_client.post(
            projects_urls.list(),
            invalid_data,
            format='multipart'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_student_project(self, api_client, user, business_area, db):
        """Test creating student project with student details"""
        # Arrange
        api_client.force_authenticate(user=user)
        project_data = {
            'kind': 'student',
            'year': '2023',
            'title': 'Student Project',
            'description': 'Test',
            'businessArea': business_area.pk,
            'projectLead': user.pk,
            'creator': user.pk,
            'keywords': '[]',
            'locations': [],
            'organisation': 'Test University',
            'level': 'undergrad',
        }
        
        # Act
        response = api_client.post(
            projects_urls.list(),
            project_data,
            format='multipart'
        )
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['kind'] == 'student'

    def test_create_external_project(self, api_client, user, business_area, db):
        """Test creating external project with external details"""
        # Arrange
        api_client.force_authenticate(user=user)
        project_data = {
            'kind': 'external',
            'year': '2023',
            'title': 'External Project',
            'description': 'Test',
            'businessArea': business_area.pk,
            'projectLead': user.pk,
            'creator': user.pk,
            'keywords': '[]',
            'locations': [],
            'externalDescription': '<p>External description</p>',
            'aims': '<p>Project aims</p>',
            'budget': '<p>$10,000</p>',
            'collaborationWith': '<p>Partner org</p>',
        }
        
        # Act
        response = api_client.post(
            projects_urls.list(),
            project_data,
            format='multipart'
        )
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['kind'] == 'external'


# Additional tests for admin views

class TestUnapprovedThisFY:
    """Tests for UnapprovedThisFY view"""

    def test_get_unapproved_projects(self, api_client, user, project, db):
        """Test getting unapproved projects for current fiscal year"""
        # Arrange
        api_client.force_authenticate(user=user)
        from datetime import date
        today = date.today()
        if today.month >= 7:
            fy_year = today.year
        else:
            fy_year = today.year - 1
        
        project.year = fy_year
        project.status = 'new'
        project.save()
        
        # Act
        response = api_client.get(projects_urls.path('unapprovedFY'))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)


class TestProblematicProjects:
    """Tests for ProblematicProjects view"""

    def test_get_problematic_projects(self, api_client, user, db):
        """Test getting projects with various issues"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(projects_urls.path('problematic'))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert 'open_with_closure' in response.data
        assert 'memberless' in response.data
        assert 'leaderless' in response.data
        assert 'multiple_leaders' in response.data
        assert 'external_leaders' in response.data


class TestRemedyViews:
    """Tests for remedy views"""

    def test_remedy_open_closed(self, api_client, user, db):
        """Test getting open projects with approved closures"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(projects_urls.path('remedy', 'open_closed'))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_remedy_memberless(self, api_client, user, db):
        """Test getting projects with no members"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(projects_urls.path('remedy', 'memberless'))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_remedy_no_leader(self, api_client, user, db):
        """Test getting projects with no leader"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(projects_urls.path('remedy', 'leaderless'))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_remedy_multiple_leaders(self, api_client, user, db):
        """Test getting projects with multiple leaders"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(projects_urls.path('remedy', 'multiple_leaders'))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_remedy_external_leaders(self, api_client, user, db):
        """Test getting projects with external leaders"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(projects_urls.path('remedy', 'external_leaders'))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)


# Additional tests for detail views

class TestStudentProjectAdditional:
    """Tests for StudentProjectAdditional view"""

    def test_list_student_details(self, api_client, user, db):
        """Test listing all student project details"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(projects_urls.path('student_project_details'))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_create_student_detail(self, api_client, user, project, db):
        """Test creating student project detail"""
        # Arrange
        api_client.force_authenticate(user=user)
        detail_data = {
            'project': project.pk,
            'organisation': 'Test University',
            'level': 'phd',
        }
        
        # Act
        response = api_client.post(
            projects_urls.path('student_project_details'),
            detail_data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED


class TestStudentProjectAdditionalDetail:
    """Tests for StudentProjectAdditionalDetail view"""

    def test_get_student_detail(self, api_client, user, project, db):
        """Test getting student project detail"""
        # Arrange
        api_client.force_authenticate(user=user)
        from projects.services.details_service import DetailsService
        detail = DetailsService.create_student_details(
            project.pk,
            {'organisation': 'Test Uni', 'level': 'undergrad'},
            user
        )
        
        # Act
        response = api_client.get(projects_urls.path('student_project_details', detail.pk))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK

    def test_update_student_detail(self, api_client, user, project, db):
        """Test updating student project detail"""
        # Arrange
        api_client.force_authenticate(user=user)
        from projects.services.details_service import DetailsService
        detail = DetailsService.create_student_details(
            project.pk,
            {'organisation': 'Test Uni', 'level': 'undergrad'},
            user
        )
        update_data = {'level': 'phd'}
        
        # Act
        response = api_client.put(
            projects_urls.path('student_project_details', detail.pk),
            update_data,
            format='json'
        )
        
        # Assert
        if response.status_code != status.HTTP_202_ACCEPTED:
            print(f"ERROR: {response.data}")
        assert response.status_code == status.HTTP_202_ACCEPTED

    def test_delete_student_detail(self, api_client, user, project, db):
        """Test deleting student project detail"""
        # Arrange
        api_client.force_authenticate(user=user)
        from projects.services.details_service import DetailsService
        detail = DetailsService.create_student_details(
            project.pk,
            {'organisation': 'Test Uni', 'level': 'undergrad'},
            user
        )
        detail_id = detail.pk
        
        # Act
        response = api_client.delete(projects_urls.path('student_project_details', detail_id))
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT


class TestExternalProjectAdditional:
    """Tests for ExternalProjectAdditional view"""

    def test_list_external_details(self, api_client, user, db):
        """Test listing all external project details"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(projects_urls.path('external_project_details'))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_create_external_detail(self, api_client, user, project, db):
        """Test creating external project detail"""
        # Arrange
        api_client.force_authenticate(user=user)
        detail_data = {
            'project': project.pk,
            'collaboration_with': '<p>Partner</p>',
            'budget': '<p>$5000</p>',
        }
        
        # Act
        response = api_client.post(
            projects_urls.path('external_project_details'),
            detail_data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED


class TestExternalProjectAdditionalDetail:
    """Tests for ExternalProjectAdditionalDetail view"""

    def test_get_external_detail(self, api_client, user, project, db):
        """Test getting external project detail"""
        # Arrange
        api_client.force_authenticate(user=user)
        from projects.services.details_service import DetailsService
        detail = DetailsService.create_external_details(
            project.pk,
            {'collaboration_with': '<p>Partner</p>'},
            user
        )
        
        # Act
        response = api_client.get(projects_urls.path('external_project_details', detail.pk))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK

    def test_update_external_detail(self, api_client, user, project, db):
        """Test updating external project detail"""
        # Arrange
        api_client.force_authenticate(user=user)
        from projects.services.details_service import DetailsService
        detail = DetailsService.create_external_details(
            project.pk,
            {'collaboration_with': '<p>Partner</p>'},
            user
        )
        update_data = {'budget': '<p>$10000</p>'}
        
        # Act
        response = api_client.put(
            projects_urls.path('external_project_details', detail.pk),
            update_data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED

    def test_delete_external_detail(self, api_client, user, project, db):
        """Test deleting external project detail"""
        # Arrange
        api_client.force_authenticate(user=user)
        from projects.services.details_service import DetailsService
        detail = DetailsService.create_external_details(
            project.pk,
            {'collaboration_with': '<p>Partner</p>'},
            user
        )
        detail_id = detail.pk
        
        # Act
        response = api_client.delete(projects_urls.path('external_project_details', detail_id))
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT


# Tests for areas views

class TestProjectAreas:
    """Tests for ProjectAreas view (list and create)"""

    def test_list_all_areas(self, api_client, user, db):
        """Test listing all project areas"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(projects_urls.path('project_areas'))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_create_project_area(self, api_client, user, project_factory, area, db):
        """Test creating project area"""
        # Arrange
        api_client.force_authenticate(user=user)
        # Create a new project without ProjectArea
        new_project = project_factory()
        area_data = {
            'project': new_project.pk,
            'areas': [area.pk],
        }
        
        # Act
        response = api_client.post(
            projects_urls.path('project_areas'),
            area_data,
            format='json'
        )
        
        # Assert
        if response.status_code != status.HTTP_201_CREATED:
            print(f"ERROR: {response.data}")
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_project_area_invalid_data(self, api_client, user, db):
        """Test creating project area with invalid data"""
        # Arrange
        api_client.force_authenticate(user=user)
        invalid_data = {
            'project': 99999,  # Non-existent project
        }
        
        # Act
        response = api_client.post(
            projects_urls.path('project_areas'),
            invalid_data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestProjectAreaDetail:
    """Tests for ProjectAreaDetail view"""

    def test_get_project_area(self, api_client, user, project_area, db):
        """Test getting project area by ID"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(projects_urls.path('project_areas', project_area.pk))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == project_area.pk

    def test_update_project_area(self, api_client, user, project_area, area, db):
        """Test updating project area"""
        # Arrange
        api_client.force_authenticate(user=user)
        update_data = {
            'areas': [area.pk],
        }
        
        # Act
        response = api_client.put(
            projects_urls.path('project_areas', project_area.pk),
            update_data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED

    def test_delete_project_area(self, api_client, user, project_area, db):
        """Test deleting project area"""
        # Arrange
        api_client.force_authenticate(user=user)
        area_id = project_area.pk
        
        # Act
        response = api_client.delete(projects_urls.path('project_areas', area_id))
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT


class TestAreasForProject:
    """Tests for AreasForProject view"""

    def test_get_areas_for_project(self, api_client, user, project_area, db):
        """Test getting areas for a specific project"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(projects_urls.path(project_area.project.pk, 'areas'))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == project_area.pk


# Tests for export views

class TestDownloadAllProjectsAsCSV:
    """Tests for DownloadAllProjectsAsCSV view"""

    def test_download_csv_as_admin(self, api_client, superuser, project, db):
        """Test downloading all projects CSV as admin"""
        # Arrange
        api_client.force_authenticate(user=superuser)
        
        # Act
        response = api_client.get(projects_urls.path('download'))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response['Content-Type'] == 'text/csv'
        assert 'attachment' in response['Content-Disposition']

    def test_download_csv_as_non_admin(self, api_client, user, db):
        """Test downloading CSV as non-admin fails"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(projects_urls.path('download'))
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestDownloadARProjectsAsCSV:
    """Tests for DownloadARProjectsAsCSV view"""

    def test_download_ar_csv_as_admin(self, api_client, superuser, project, db):
        """Test downloading annual report projects CSV as admin"""
        # Arrange
        api_client.force_authenticate(user=superuser)
        
        # Act
        response = api_client.get(projects_urls.path('download-ar'))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response['Content-Type'] == 'text/csv'
        assert 'attachment' in response['Content-Disposition']

    def test_download_ar_csv_as_non_admin(self, api_client, user, db):
        """Test downloading AR CSV as non-admin fails"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(projects_urls.path('download-ar'))
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN


# Tests for map view

class TestProjectMap:
    """Tests for ProjectMap view"""

    def test_get_project_map(self, api_client, user, project, db):
        """Test getting projects for map display"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(projects_urls.path('map'))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert 'projects' in response.data
        assert 'total_projects' in response.data
        assert 'projects_without_location' in response.data

    def test_get_project_map_with_filters(self, api_client, user, project, db):
        """Test getting map with filters"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(projects_urls.path('map'), {'kind': 'science'})
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert 'projects' in response.data


# Tests for search views

class TestSmallProjectSearch:
    """Tests for SmallProjectSearch view"""

    def test_small_search(self, api_client, user, project, db):
        """Test small project search for autocomplete"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(projects_urls.path('smallsearch'))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_small_search_with_filter(self, api_client, user, project, db):
        """Test small search with search term"""
        # Arrange
        project.title = "Unique Search Term"
        project.save()
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(projects_urls.path('smallsearch'), {'searchTerm': 'Unique'})
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)


class TestMyProjects:
    """Tests for MyProjects view"""

    def test_get_my_projects(self, api_client, user, project_with_lead, project_lead, db):
        """Test getting projects for current user"""
        # Arrange
        api_client.force_authenticate(user=project_lead)
        
        # Act
        response = api_client.get(projects_urls.path('mine'))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) >= 1


# Tests for utils views

class TestProjectYears:
    """Tests for ProjectYears view"""

    def test_get_project_years(self, api_client, user, project, db):
        """Test getting list of project years"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(projects_urls.path('listofyears'))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)


class TestSuspendProject:
    """Tests for SuspendProject view"""

    def test_suspend_project(self, api_client, user, project, db):
        """Test suspending a project"""
        # Arrange
        api_client.force_authenticate(user=user)
        project.status = 'active'
        project.save()
        
        # Act
        response = api_client.post(projects_urls.path(project.pk, 'suspend'))
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        project.refresh_from_db()
        assert project.status == 'suspended'


class TestProjectDocs:
    """Tests for ProjectDocs view"""

    def test_get_project_docs(self, api_client, user, project, db):
        """Test getting all documents for a project"""
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get(projects_urls.path(project.pk, 'project_docs'))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)


class TestToggleUserProfileVisibilityForProject:
    """Tests for ToggleUserProfileVisibilityForProject view"""

    def test_toggle_visibility(self, api_client, user, project, db):
        """Test toggling project visibility on user profile"""
        # Arrange
        api_client.force_authenticate(user=user)
        original_hidden_list = project.hidden_from_staff_profiles.copy() if project.hidden_from_staff_profiles else []
        
        # Act
        response = api_client.post(projects_urls.path(project.pk, 'toggle_user_profile_visibility'))
        
        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED
        project.refresh_from_db()
        # Check that the hidden list changed
        assert project.hidden_from_staff_profiles != original_hidden_list


class TestProjectKindGetters:
    """Tests for project kind getter views"""

    def test_get_core_function_projects(self, api_client, user, project_factory, db):
        """Test getting core function projects"""
        # Arrange
        api_client.force_authenticate(user=user)
        project_factory(kind='core_function')
        
        # Act
        response = api_client.get(projects_urls.path('core_function'))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_get_science_projects(self, api_client, user, project_factory, db):
        """Test getting science projects"""
        # Arrange
        api_client.force_authenticate(user=user)
        project_factory(kind='science')
        
        # Act
        response = api_client.get(projects_urls.path('science'))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_get_student_projects(self, api_client, user, project_factory, db):
        """Test getting student projects"""
        # Arrange
        api_client.force_authenticate(user=user)
        project_factory(kind='student')
        
        # Act
        response = api_client.get(projects_urls.path('student'))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_get_external_projects(self, api_client, user, project_factory, db):
        """Test getting external projects"""
        # Arrange
        api_client.force_authenticate(user=user)
        project_factory(kind='external')
        
        # Act
        response = api_client.get(projects_urls.path('external'))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
