"""
Tests for project models
"""
import pytest
from datetime import datetime, date
from django.forms import ValidationError

from projects.models import (
    Project,
    ProjectDetail,
    ProjectArea,
    ProjectMember,
    StudentProjectDetails,
    ExternalProjectDetails,
    get_next_available_number_for_year,
)


class TestGetNextAvailableNumberForYear:
    """Tests for get_next_available_number_for_year function"""

    def test_returns_1_when_no_projects_exist(self, db):
        """Test returns 1 when no projects exist for current year"""
        # Arrange - no projects exist
        current_year = datetime.today().year
        Project.objects.filter(year=current_year).delete()
        
        # Act
        result = get_next_available_number_for_year()
        
        # Assert
        assert result == 1

    def test_returns_next_number_when_projects_exist(self, db, project):
        """Test returns next available number when projects exist"""
        # Arrange
        current_year = datetime.today().year
        project.year = current_year
        project.number = 5
        project.save()
        
        # Act
        result = get_next_available_number_for_year()
        
        # Assert
        assert result == 6


class TestProject:
    """Tests for Project model"""

    def test_get_deletion_request_id_returns_none_when_no_request(self, project, db):
        """Test get_deletion_request_id returns None when no deletion request exists"""
        # Act
        result = project.get_deletion_request_id()
        
        # Assert
        assert result is None

    def test_get_deletion_request_id_returns_id_when_request_exists(self, project, db):
        """Test get_deletion_request_id returns task ID when deletion request exists"""
        # Arrange
        from adminoptions.models import AdminTask
        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.DELETEPROJECT,
            project=project,
            status=AdminTask.TaskStatus.PENDING,
        )
        
        # Act
        result = project.get_deletion_request_id()
        
        # Assert
        assert result == task.id

    def test_extract_inner_text(self, project, db):
        """Test extract_inner_text method"""
        # Arrange
        html = '<p>Test <strong>content</strong> here</p>'
        
        # Act
        result = project.extract_inner_text(html)
        
        # Assert
        assert result == 'Test content here'

    def test_extract_inner_text_with_complex_html(self, project, db):
        """Test extract_inner_text with complex HTML"""
        # Arrange
        html = '<div><p>First</p><span>Second</span></div>'
        
        # Act
        result = project.extract_inner_text(html)
        
        # Assert
        assert 'First' in result
        assert 'Second' in result

    def test_project_kind_to_tag_science(self, project, db):
        """Test project_kind_to_tag for science project"""
        # Arrange
        project.kind = 'science'
        
        # Act
        result = project.project_kind_to_tag()
        
        # Assert
        assert result == 'SP'

    def test_project_kind_to_tag_student(self, project, db):
        """Test project_kind_to_tag for student project"""
        # Arrange
        project.kind = 'student'
        
        # Act
        result = project.project_kind_to_tag()
        
        # Assert
        assert result == 'STP'

    def test_project_kind_to_tag_external(self, project, db):
        """Test project_kind_to_tag for external project"""
        # Arrange
        project.kind = 'external'
        
        # Act
        result = project.project_kind_to_tag()
        
        # Assert
        assert result == 'EXT'

    def test_project_kind_to_tag_core_function(self, project, db):
        """Test project_kind_to_tag for core function project"""
        # Arrange
        project.kind = 'core_function'
        
        # Act
        result = project.project_kind_to_tag()
        
        # Assert
        assert result == 'CF'

    def test_project_kind_to_tag_unknown(self, project, db):
        """Test project_kind_to_tag for unknown project kind"""
        # Arrange
        project.kind = 'unknown_kind'
        
        # Act
        result = project.project_kind_to_tag()
        
        # Assert
        assert result == 'UNKNOWN'

    def test_get_project_tag(self, project, db):
        """Test get_project_tag method"""
        # Arrange
        project.kind = 'science'
        project.year = 2023
        project.number = 42
        
        # Act
        result = project.get_project_tag()
        
        # Assert
        assert result == 'SP-2023-42'

    def test_get_description_non_external(self, project, db):
        """Test get_description for non-external project"""
        # Arrange
        project.kind = 'science'
        project.description = 'Test description'
        
        # Act
        result = project.get_description()
        
        # Assert
        assert result == 'Test description'

    def test_get_description_external_with_details(self, project, db):
        """Test get_description for external project with details"""
        # Arrange
        project.kind = 'external'
        project.description = 'Base description'
        project.save()
        
        ExternalProjectDetails.objects.create(
            project=project,
            description='<p>External description</p>',
        )
        
        # Act
        result = project.get_description()
        
        # Assert
        assert result == '<p>External description</p>'

    def test_get_description_external_without_details(self, project, db):
        """Test get_description for external project without details"""
        # Arrange
        project.kind = 'external'
        project.description = 'Base description'
        
        # Act
        result = project.get_description()
        
        # Assert
        assert result == ''

    def test_str_representation(self, project, db):
        """Test string representation of Project"""
        # Arrange
        project.kind = 'science'
        project.title = '<p>Test Project Title</p>'
        
        # Act
        result = str(project)
        
        # Assert
        assert '(SCIENCE)' in result
        assert 'Test Project Title' in result


class TestProjectDetail:
    """Tests for ProjectDetail model"""

    def test_str_representation(self, project_with_lead, db):
        """Test string representation of ProjectDetail"""
        # Arrange
        detail = project_with_lead.project_detail
        
        # Act
        result = str(detail)
        
        # Assert
        assert '(DETAILS)' in result
        assert str(project_with_lead) in result


class TestProjectArea:
    """Tests for ProjectArea model"""

    def test_str_representation(self, db):
        """Test string representation of ProjectArea"""
        # Arrange
        from common.tests.factories import ProjectFactory
        project = ProjectFactory()
        area = ProjectArea.objects.create(
            project=project,
            areas=[1, 2, 3],
        )
        
        # Act
        result = str(area)
        
        # Assert
        assert str(project) in result
        assert '1' in result
        assert '2' in result
        assert '3' in result

    def test_save_raises_error_on_duplicate_areas(self, db):
        """Test save raises ValidationError when duplicate area IDs exist"""
        # Arrange
        from common.tests.factories import ProjectFactory
        project = ProjectFactory()
        area = ProjectArea(
            project=project,
            areas=[1, 2, 2, 3],  # Duplicate 2
        )
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            area.save()
        
        assert 'Duplicate primary keys found in areas' in str(exc_info.value)

    def test_save_succeeds_with_unique_areas(self, db):
        """Test save succeeds when all area IDs are unique"""
        # Arrange
        from common.tests.factories import ProjectFactory
        project = ProjectFactory()
        area = ProjectArea(
            project=project,
            areas=[1, 2, 3, 4],
        )
        
        # Act
        area.save()
        
        # Assert
        assert area.pk is not None
        assert area.areas == [1, 2, 3, 4]


class TestProjectMember:
    """Tests for ProjectMember model"""

    def test_str_representation(self, project_with_lead, project_lead, db):
        """Test string representation of ProjectMember"""
        # Arrange
        member = project_with_lead.members.filter(user=project_lead).first()
        
        # Act
        result = str(member)
        
        # Assert
        assert str(project_lead) in result
        assert str(project_with_lead) in result

    def test_unique_together_constraint(self, project_with_lead, project_lead, db):
        """Test unique_together constraint prevents duplicate user on same project"""
        # Arrange - member already exists from fixture
        
        # Act & Assert - try to create duplicate
        with pytest.raises(Exception):  # IntegrityError
            ProjectMember.objects.create(
                project=project_with_lead,
                user=project_lead,
                is_leader=False,
                role='research',
            )

    def test_default_values(self, project, user, db):
        """Test default values for ProjectMember fields"""
        # Arrange & Act
        member = ProjectMember.objects.create(
            project=project,
            user=user,
            role='research',
        )
        
        # Assert
        assert member.is_leader is False
        assert member.time_allocation == 0
        assert member.position == 100


class TestStudentProjectDetails:
    """Tests for StudentProjectDetails model"""

    def test_str_representation(self, project, db):
        """Test string representation of StudentProjectDetails"""
        # Arrange
        details = StudentProjectDetails.objects.create(
            project=project,
            level='phd',
            organisation='Test University',
        )
        
        # Act
        result = str(details)
        
        # Assert
        assert 'phd' in result
        assert 'Test University' in result

    def test_clean_removes_stale_affiliations(self, project, db):
        """Test clean method removes stale affiliation references"""
        # Arrange
        from common.tests.factories import AffiliationFactory
        
        valid_affiliation = AffiliationFactory(name='Valid Affiliation')
        
        details = StudentProjectDetails.objects.create(
            project=project,
            level='phd',
            organisation='Valid Affiliation; Stale Affiliation; Another Stale',
        )
        
        # Act
        details.clean()
        
        # Assert
        assert details.organisation == 'Valid Affiliation'

    def test_clean_handles_empty_organisation(self, project, db):
        """Test clean method handles empty organisation field"""
        # Arrange
        details = StudentProjectDetails.objects.create(
            project=project,
            level='phd',
            organisation='',
        )
        
        # Act
        details.clean()
        
        # Assert
        assert details.organisation == ''

    def test_clean_handles_none_organisation(self, project, db):
        """Test clean method handles None organisation field"""
        # Arrange
        details = StudentProjectDetails.objects.create(
            project=project,
            level='phd',
            organisation=None,
        )
        
        # Act
        details.clean()
        
        # Assert
        assert details.organisation is None


class TestExternalProjectDetails:
    """Tests for ExternalProjectDetails model"""

    def test_str_representation(self, project, db):
        """Test string representation of ExternalProjectDetails"""
        # Arrange
        details = ExternalProjectDetails.objects.create(
            project=project,
            collaboration_with='Partner Organization',
        )
        
        # Act
        result = str(details)
        
        # Assert
        assert str(project) in result
        assert 'Partner Organization' in result

    def test_clean_removes_stale_affiliations(self, project, db):
        """Test clean method removes stale affiliation references"""
        # Arrange
        from common.tests.factories import AffiliationFactory
        
        valid_affiliation = AffiliationFactory(name='Valid Partner')
        
        details = ExternalProjectDetails.objects.create(
            project=project,
            collaboration_with='Valid Partner; Stale Partner; Another Stale',
        )
        
        # Act
        details.clean()
        
        # Assert
        assert details.collaboration_with == 'Valid Partner'

    def test_clean_handles_empty_collaboration_with(self, project, db):
        """Test clean method handles empty collaboration_with field"""
        # Arrange
        details = ExternalProjectDetails.objects.create(
            project=project,
            collaboration_with='',
        )
        
        # Act
        details.clean()
        
        # Assert
        assert details.collaboration_with == ''

    def test_clean_handles_none_collaboration_with(self, project, db):
        """Test clean method handles None collaboration_with field"""
        # Arrange
        details = ExternalProjectDetails.objects.create(
            project=project,
            collaboration_with=None,
        )
        
        # Act
        details.clean()
        
        # Assert
        assert details.collaboration_with is None
