"""
Tests for project serializers
"""

from projects.serializers.areas import ProjectAreaSerializer
from projects.serializers.base import (
    CreateProjectSerializer,
    PkAndKindOnlyProjectSerializer,
    ProblematicProjectSerializer,
    ProjectSerializer,
    ProjectUpdateSerializer,
    TinyProjectSerializer,
    UserProfileProjectSerializer,
)
from projects.serializers.details import (
    ExternalProjectDetailSerializer,
    ProjectDetailSerializer,
    ProjectDetailViewSerializer,
    StudentProjectDetailSerializer,
    TinyExternalProjectDetailSerializer,
    TinyProjectDetailSerializer,
    TinyStudentProjectDetailSerializer,
)
from projects.serializers.export import (
    ARExternalProjectSerializer,
    ARProjectSerializer,
    ProjectDataTableSerializer,
    TinyStudentProjectARSerializer,
)
from projects.serializers.members import (
    MiniProjectMemberSerializer,
    ProjectMemberSerializer,
    TinyProjectMemberSerializer,
)


class TestCreateProjectSerializer:
    """Tests for CreateProjectSerializer"""

    def test_serialization(self, project, db):
        """Test serializing a project"""
        # Arrange
        serializer = CreateProjectSerializer(project)

        # Act
        data = serializer.data

        # Assert
        assert data["id"] == project.id
        assert data["title"] == project.title
        assert data["kind"] == project.kind
        assert data["status"] == project.status

    def test_validation_valid_data(self, business_area, db):
        """Test validation with valid data"""
        # Arrange
        data = {
            "title": "Test Project",
            "kind": "science",
            "status": "new",
            "year": 2023,
            "number": 1,
            "business_area": business_area.id,
        }
        serializer = CreateProjectSerializer(data=data)

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is True
        assert serializer.validated_data["title"] == "Test Project"


class TestProjectSerializer:
    """Tests for ProjectSerializer"""

    def test_serialization(self, project, db):
        """Test serializing a project"""
        # Arrange
        serializer = ProjectSerializer(project)

        # Act
        data = serializer.data

        # Assert
        assert data["id"] == project.id
        assert data["title"] == project.title
        assert "business_area" in data
        assert "deletion_request_id" in data
        assert "areas" in data

    def test_get_deletion_request_id_none(self, project, db):
        """Test get_deletion_request_id returns None when no request"""
        # Arrange
        serializer = ProjectSerializer(project)

        # Act
        data = serializer.data

        # Assert
        assert data["deletion_request_id"] is None

    def test_get_deletion_request_id_with_request(self, project, db):
        """Test get_deletion_request_id returns ID when request exists"""
        # Arrange
        from adminoptions.models import AdminTask

        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.DELETEPROJECT,
            project=project,
            status=AdminTask.TaskStatus.PENDING,
        )
        serializer = ProjectSerializer(project)

        # Act
        data = serializer.data

        # Assert
        assert data["deletion_request_id"] == task.id

    def test_get_areas_empty(self, db):
        """Test get_areas returns empty list when no areas"""
        # Arrange
        from agencies.models import Agency, BusinessArea
        from projects.models import Project, ProjectArea

        agency = Agency.objects.create(name="Test Agency")
        business_area = BusinessArea.objects.create(
            name="Test BA",
            agency=agency,
            leader=None,
            finance_admin=None,
            data_custodian=None,
        )
        project = Project.objects.create(
            title="Test Project",
            kind="science",
            status="new",
            year=2023,
            number=1,
            business_area=business_area,
        )
        ProjectArea.objects.create(project=project, areas=[])
        serializer = ProjectSerializer(project)

        # Act
        data = serializer.data

        # Assert
        assert data["areas"] == []

    def test_get_areas_with_areas(self, db):
        """Test get_areas returns area data when areas exist"""
        # Arrange
        from agencies.models import Agency, BusinessArea
        from locations.models import Area
        from projects.models import Project, ProjectArea

        agency = Agency.objects.create(name="Test Agency")
        business_area = BusinessArea.objects.create(
            name="Test BA",
            agency=agency,
            leader=None,
            finance_admin=None,
            data_custodian=None,
        )
        project = Project.objects.create(
            title="Test Project",
            kind="science",
            status="new",
            year=2023,
            number=2,
            business_area=business_area,
        )

        area1 = Area.objects.create(name="Area 1", area_type="dbcaregion")
        area2 = Area.objects.create(name="Area 2", area_type="dbcaregion")

        ProjectArea.objects.create(project=project, areas=[area1.id, area2.id])
        serializer = ProjectSerializer(project)

        # Act
        data = serializer.data

        # Assert
        assert len(data["areas"]) == 2
        assert data["areas"][0]["id"] == area1.id
        assert data["areas"][1]["id"] == area2.id


class TestProjectUpdateSerializer:
    """Tests for ProjectUpdateSerializer"""

    def test_validation_valid_data(self, db):
        """Test validation with valid data"""
        # Arrange
        data = {
            "title": "Updated Project",
            "status": "active",
        }
        serializer = ProjectUpdateSerializer(data=data, partial=True)

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is True
        assert serializer.validated_data["title"] == "Updated Project"


class TestTinyProjectSerializer:
    """Tests for TinyProjectSerializer"""

    def test_serialization(self, project, db):
        """Test serializing a project with minimal fields"""
        # Arrange
        serializer = TinyProjectSerializer(project)

        # Act
        data = serializer.data

        # Assert
        assert data["id"] == project.id
        assert data["title"] == project.title
        assert data["status"] == project.status
        assert data["kind"] == project.kind
        assert data["year"] == project.year
        assert data["number"] == project.number
        assert "business_area" in data
        assert "image" in data


class TestProblematicProjectSerializer:
    """Tests for ProblematicProjectSerializer"""

    def test_serialization(self, project, db):
        """Test serializing a problematic project"""
        # Arrange
        project.kind = "science"
        project.year = 2023
        project.number = 42
        project.save()
        serializer = ProblematicProjectSerializer(project)

        # Act
        data = serializer.data

        # Assert
        assert data["id"] == project.id
        assert data["title"] == project.title
        assert data["tag"] == "SP-2023-42"
        assert "business_area" in data


class TestUserProfileProjectSerializer:
    """Tests for UserProfileProjectSerializer"""

    def test_serialization(self, project, db):
        """Test serializing a project for user profile"""
        # Arrange
        project.kind = "science"
        project.year = 2023
        project.number = 42
        project.save()
        serializer = UserProfileProjectSerializer(project)

        # Act
        data = serializer.data

        # Assert
        assert data["id"] == project.id
        assert data["title"] == project.title
        assert data["tag"] == "SP-2023-42"
        assert "image" in data


class TestPkAndKindOnlyProjectSerializer:
    """Tests for PkAndKindOnlyProjectSerializer"""

    def test_serialization(self, project, db):
        """Test serializing project with only ID and kind"""
        # Arrange
        serializer = PkAndKindOnlyProjectSerializer(project)

        # Act
        data = serializer.data

        # Assert
        assert data["id"] == project.id
        assert data["kind"] == project.kind
        assert len(data) == 2  # Only id and kind


class TestProjectDetailSerializer:
    """Tests for ProjectDetailSerializer"""

    def test_serialization(self, project_with_lead, db):
        """Test serializing project details"""
        # Arrange
        detail = project_with_lead.project_detail
        serializer = ProjectDetailSerializer(detail)

        # Act
        data = serializer.data

        # Assert
        assert data["id"] == detail.id
        assert data["project"] == detail.project.id


class TestProjectDetailViewSerializer:
    """Tests for ProjectDetailViewSerializer"""

    def test_serialization(self, project_with_lead, db):
        """Test serializing project details for view"""
        # Arrange
        detail = project_with_lead.project_detail
        serializer = ProjectDetailViewSerializer(detail)

        # Act
        data = serializer.data

        # Assert
        assert data["id"] == detail.id
        assert "project" in data
        assert data["project"]["id"] == detail.project.id
        assert data["project"]["title"] == detail.project.title

    def test_get_creator_with_user(self, project_with_lead, user, db):
        """Test get_creator returns user data"""
        # Arrange
        detail = project_with_lead.project_detail
        detail.creator = user
        detail.save()
        serializer = ProjectDetailViewSerializer(detail)

        # Act
        data = serializer.data

        # Assert
        assert data["creator"]["id"] == user.id
        assert data["creator"]["username"] == user.username

    def test_get_creator_none(self, project_with_lead, db):
        """Test get_creator returns None when no creator"""
        # Arrange
        detail = project_with_lead.project_detail
        detail.creator = None
        detail.save()
        serializer = ProjectDetailViewSerializer(detail)

        # Act
        data = serializer.data

        # Assert
        assert data["creator"] is None


class TestTinyProjectDetailSerializer:
    """Tests for TinyProjectDetailSerializer"""

    def test_serialization(self, project_with_lead, db):
        """Test serializing minimal project details"""
        # Arrange
        detail = project_with_lead.project_detail
        serializer = TinyProjectDetailSerializer(detail)

        # Act
        data = serializer.data

        # Assert
        assert data["id"] == detail.id
        assert "project" in data
        assert data["project"]["id"] == detail.project.id


class TestStudentProjectDetailSerializer:
    """Tests for StudentProjectDetailSerializer"""

    def test_serialization(self, project, db):
        """Test serializing student project details"""
        # Arrange
        from projects.models import StudentProjectDetails

        detail = StudentProjectDetails.objects.create(
            project=project,
            level="phd",
            organisation="Test University",
        )
        serializer = StudentProjectDetailSerializer(detail)

        # Act
        data = serializer.data

        # Assert
        assert data["id"] == detail.id
        assert data["level"] == "phd"
        assert data["organisation"] == "Test University"


class TestTinyStudentProjectDetailSerializer:
    """Tests for TinyStudentProjectDetailSerializer"""

    def test_serialization(self, project, db):
        """Test serializing minimal student project details"""
        # Arrange
        from projects.models import StudentProjectDetails

        detail = StudentProjectDetails.objects.create(
            project=project,
            level="phd",
            organisation="Test University",
        )
        serializer = TinyStudentProjectDetailSerializer(detail)

        # Act
        data = serializer.data

        # Assert
        assert data["id"] == detail.id
        assert data["level"] == "phd"
        assert data["organisation"] == "Test University"
        assert "project" in data
        assert data["project"]["id"] == project.id


class TestExternalProjectDetailSerializer:
    """Tests for ExternalProjectDetailSerializer"""

    def test_serialization(self, project, db):
        """Test serializing external project details"""
        # Arrange
        from projects.models import ExternalProjectDetails

        detail = ExternalProjectDetails.objects.create(
            project=project,
            collaboration_with="Partner Org",
            budget="$100,000",
            description="Test description",
            aims="Test aims",
        )
        serializer = ExternalProjectDetailSerializer(detail)

        # Act
        data = serializer.data

        # Assert
        assert data["id"] == detail.id
        assert data["collaboration_with"] == "Partner Org"
        assert data["budget"] == "$100,000"


class TestTinyExternalProjectDetailSerializer:
    """Tests for TinyExternalProjectDetailSerializer"""

    def test_serialization(self, project, db):
        """Test serializing minimal external project details"""
        # Arrange
        from projects.models import ExternalProjectDetails

        detail = ExternalProjectDetails.objects.create(
            project=project,
            collaboration_with="Partner Org",
            budget="$100,000",
            description="Test description",
            aims="Test aims",
        )
        serializer = TinyExternalProjectDetailSerializer(detail)

        # Act
        data = serializer.data

        # Assert
        assert data["id"] == detail.id
        assert data["collaboration_with"] == "Partner Org"
        assert "project" in data
        assert data["project"]["id"] == project.id


class TestProjectMemberSerializer:
    """Tests for ProjectMemberSerializer"""

    def test_validation_valid_data(self, project, user, db):
        """Test validation with valid data"""
        # Arrange
        data = {
            "project": project.id,
            "user": user.id,
            "role": "supervising",
            "is_leader": True,
        }
        serializer = ProjectMemberSerializer(data=data)

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is True
        assert serializer.validated_data["role"] == "supervising"

    def test_validation_missing_role(self, project, user, db):
        """Test validation fails when role is missing"""
        # Arrange
        data = {
            "project": project.id,
            "user": user.id,
            "role": "",
        }
        serializer = ProjectMemberSerializer(data=data)

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is False
        assert "role" in serializer.errors


class TestTinyProjectMemberSerializer:
    """Tests for TinyProjectMemberSerializer"""

    def test_serialization(self, project_with_lead, project_lead, db):
        """Test serializing minimal project member"""
        # Arrange
        member = project_with_lead.members.filter(user=project_lead).first()
        serializer = TinyProjectMemberSerializer(member)

        # Act
        data = serializer.data

        # Assert
        assert data["id"] == member.id
        assert "user" in data
        assert "project" in data
        assert data["is_leader"] is True
        assert data["role"] == member.role


class TestMiniProjectMemberSerializer:
    """Tests for MiniProjectMemberSerializer"""

    def test_serialization(self, project_with_lead, project_lead, db):
        """Test serializing mini project member"""
        # Arrange
        from agencies.models import Affiliation
        from users.models import UserProfile, UserWork

        # Ensure user has a profile
        if not hasattr(project_lead, "profile"):
            UserProfile.objects.create(user=project_lead, title="mr")

        # Ensure user has work details with affiliation
        if not hasattr(project_lead, "work"):
            affiliation = Affiliation.objects.create(name="Test Affiliation")
            UserWork.objects.create(user=project_lead, affiliation=affiliation)

        member = project_with_lead.members.filter(user=project_lead).first()
        serializer = MiniProjectMemberSerializer(member)

        # Act
        data = serializer.data

        # Assert
        assert "user" in data
        assert "project" in data
        assert data["role"] == member.role
        assert data["is_leader"] is True


class TestProjectAreaSerializer:
    """Tests for ProjectAreaSerializer"""

    def test_serialization_with_areas(self, db):
        """Test serializing project area with location data"""
        # Arrange
        from agencies.models import Agency, BusinessArea
        from locations.models import Area
        from projects.models import Project, ProjectArea

        agency = Agency.objects.create(name="Test Agency")
        business_area = BusinessArea.objects.create(
            name="Test BA",
            agency=agency,
            leader=None,
            finance_admin=None,
            data_custodian=None,
        )
        project = Project.objects.create(
            title="Test Project",
            kind="science",
            status="new",
            year=2023,
            number=3,
            business_area=business_area,
        )

        area1 = Area.objects.create(name="Area 1", area_type="dbcaregion")
        area2 = Area.objects.create(name="Area 2", area_type="dbcaregion")

        project_area = ProjectArea.objects.create(
            project=project, areas=[area1.id, area2.id]
        )
        serializer = ProjectAreaSerializer(project_area)

        # Act
        data = serializer.data

        # Assert
        assert data["id"] == project_area.id
        assert len(data["areas"]) == 2
        assert data["areas"][0]["id"] == area1.id
        assert data["areas"][1]["id"] == area2.id

    def test_serialization_empty_areas(self, db):
        """Test serializing project area with no areas"""
        # Arrange
        from agencies.models import Agency, BusinessArea
        from projects.models import Project, ProjectArea

        agency = Agency.objects.create(name="Test Agency")
        business_area = BusinessArea.objects.create(
            name="Test BA",
            agency=agency,
            leader=None,
            finance_admin=None,
            data_custodian=None,
        )
        project = Project.objects.create(
            title="Test Project",
            kind="science",
            status="new",
            year=2023,
            number=4,
            business_area=business_area,
        )

        project_area = ProjectArea.objects.create(project=project, areas=[])
        serializer = ProjectAreaSerializer(project_area)

        # Act
        data = serializer.data

        # Assert
        assert data["id"] == project_area.id
        assert data["areas"] == []


class TestARProjectSerializer:
    """Tests for ARProjectSerializer"""

    def test_serialization(self, project, db):
        """Test serializing project for annual report"""
        # Arrange
        serializer = ARProjectSerializer(project)

        # Act
        data = serializer.data

        # Assert
        assert data["id"] == project.id
        assert data["title"] == project.title
        assert "image" in data
        assert "business_area" in data
        # Note: team_members is defined as SerializerMethodField without ()
        # so it's not actually a field in the serialized data

    def test_serialization_with_image(self, project, mock_image, db):
        """Test serializing project with image"""
        # Arrange
        from medias.models import ProjectPhoto

        photo = ProjectPhoto.objects.create(
            project=project,
            file=mock_image,
        )
        project.image = photo
        project.save()
        serializer = ARProjectSerializer(project)

        # Act
        data = serializer.data

        # Assert
        assert data["image"] is not None
        assert data["image"]["id"] == photo.id
        # File path will be something like 'projects/test_image_xxx.jpg'
        assert "test_image" in data["image"]["file"]


class TestARExternalProjectSerializer:
    """Tests for ARExternalProjectSerializer"""

    def test_serialization(self, project_with_lead, project_lead, db):
        """Test serializing external project for annual report"""
        # Arrange
        from agencies.models import Affiliation
        from projects.models import ExternalProjectDetails
        from users.models import UserProfile, UserWork

        # Ensure user has profile and work
        if not hasattr(project_lead, "profile"):
            UserProfile.objects.create(user=project_lead, title="mr")
        if not hasattr(project_lead, "work"):
            affiliation = Affiliation.objects.create(name="Test Affiliation")
            UserWork.objects.create(user=project_lead, affiliation=affiliation)

        ExternalProjectDetails.objects.create(
            project=project_with_lead,
            collaboration_with="Partner Organization",
            budget="$100,000",
            description="Test description",
            aims="Test aims",
        )
        serializer = ARExternalProjectSerializer(project_with_lead)

        # Act
        data = serializer.data

        # Assert
        assert data["id"] == project_with_lead.id
        assert "partners" in data
        assert "funding" in data
        assert "team_members" in data

    def test_get_partners_with_external_info(self, project_with_lead, project_lead, db):
        """Test get_partners returns collaboration_with"""
        # Arrange
        from agencies.models import Affiliation
        from projects.models import ExternalProjectDetails
        from users.models import UserProfile, UserWork

        # Ensure user has profile and work
        if not hasattr(project_lead, "profile"):
            UserProfile.objects.create(user=project_lead, title="mr")
        if not hasattr(project_lead, "work"):
            affiliation = Affiliation.objects.create(name="Test Affiliation")
            UserWork.objects.create(user=project_lead, affiliation=affiliation)

        ExternalProjectDetails.objects.create(
            project=project_with_lead,
            collaboration_with="Partner Organization",
            budget="$100,000",
            description="Test description",
            aims="Test aims",
        )
        serializer = ARExternalProjectSerializer(project_with_lead)

        # Act
        data = serializer.data

        # Assert
        assert data["partners"] == "Partner Organization"

    def test_get_partners_without_external_info(
        self, project_with_lead, project_lead, db, capsys
    ):
        """Test get_partners returns empty string when no external info"""
        # Arrange
        from agencies.models import Affiliation
        from users.models import UserProfile, UserWork

        # Ensure user has profile and work
        if not hasattr(project_lead, "profile"):
            UserProfile.objects.create(user=project_lead, title="mr")
        if not hasattr(project_lead, "work"):
            affiliation = Affiliation.objects.create(name="Test Affiliation")
            UserWork.objects.create(user=project_lead, affiliation=affiliation)

        serializer = ARExternalProjectSerializer(project_with_lead)

        # Act
        data = serializer.data

        # Assert
        assert data["partners"] == ""
        # Verify exception was caught and printed
        captured = capsys.readouterr()
        assert "EXCEPTION (NO PARTNERS):" in captured.out

    def test_get_funding_with_external_info(self, project_with_lead, project_lead, db):
        """Test get_funding returns budget"""
        # Arrange
        from agencies.models import Affiliation
        from projects.models import ExternalProjectDetails
        from users.models import UserProfile, UserWork

        # Ensure user has profile and work
        if not hasattr(project_lead, "profile"):
            UserProfile.objects.create(user=project_lead, title="mr")
        if not hasattr(project_lead, "work"):
            affiliation = Affiliation.objects.create(name="Test Affiliation")
            UserWork.objects.create(user=project_lead, affiliation=affiliation)

        ExternalProjectDetails.objects.create(
            project=project_with_lead,
            collaboration_with="Partner Organization",
            budget="$100,000",
            description="Test description",
            aims="Test aims",
        )
        serializer = ARExternalProjectSerializer(project_with_lead)

        # Act
        data = serializer.data

        # Assert
        assert data["funding"] == "$100,000"

    def test_get_funding_without_external_info(
        self, project_with_lead, project_lead, db, capsys
    ):
        """Test get_funding returns empty string when no external info"""
        # Arrange
        from agencies.models import Affiliation
        from users.models import UserProfile, UserWork

        # Ensure user has profile and work
        if not hasattr(project_lead, "profile"):
            UserProfile.objects.create(user=project_lead, title="mr")
        if not hasattr(project_lead, "work"):
            affiliation = Affiliation.objects.create(name="Test Affiliation")
            UserWork.objects.create(user=project_lead, affiliation=affiliation)

        serializer = ARExternalProjectSerializer(project_with_lead)

        # Act
        data = serializer.data

        # Assert
        assert data["funding"] == ""
        # Verify exception was caught and printed
        captured = capsys.readouterr()
        assert "EXCEPTION (NO FUNDING):" in captured.out

    def test_get_partners_method_directly(self, project_with_lead, db):
        """Test get_partners method directly without full serialization"""
        # Arrange
        from projects.models import ExternalProjectDetails

        ExternalProjectDetails.objects.create(
            project=project_with_lead,
            collaboration_with="Direct Test Partner",
            budget="$50,000",
            description="Test",
            aims="Test",
        )
        serializer = ARExternalProjectSerializer()

        # Act
        result = serializer.get_partners(project_with_lead)

        # Assert
        assert result == "Direct Test Partner"

    def test_get_funding_method_directly(self, project_with_lead, db):
        """Test get_funding method directly without full serialization"""
        # Arrange
        from projects.models import ExternalProjectDetails

        ExternalProjectDetails.objects.create(
            project=project_with_lead,
            collaboration_with="Direct Test Partner",
            budget="$75,000",
            description="Test",
            aims="Test",
        )
        serializer = ARExternalProjectSerializer()

        # Act
        result = serializer.get_funding(project_with_lead)

        # Assert
        assert result == "$75,000"

    def test_get_partners_method_no_info(self, project_with_lead, db, capsys):
        """Test get_partners method returns empty string when no external info"""
        # Arrange
        serializer = ARExternalProjectSerializer()

        # Act
        result = serializer.get_partners(project_with_lead)

        # Assert
        assert result == ""
        captured = capsys.readouterr()
        assert "EXCEPTION (NO PARTNERS):" in captured.out

    def test_get_funding_method_no_info(self, project_with_lead, db, capsys):
        """Test get_funding method returns empty string when no external info"""
        # Arrange
        serializer = ARExternalProjectSerializer()

        # Act
        result = serializer.get_funding(project_with_lead)

        # Assert
        assert result == ""
        captured = capsys.readouterr()
        assert "EXCEPTION (NO FUNDING):" in captured.out


class TestTinyStudentProjectARSerializer:
    """Tests for TinyStudentProjectARSerializer"""

    def test_serialization(self, project, db):
        """Test serializing student project for annual report"""
        # Arrange
        from projects.models import StudentProjectDetails

        StudentProjectDetails.objects.create(
            project=project,
            level="phd",
            organisation="Test University",
        )
        serializer = TinyStudentProjectARSerializer(project)

        # Act
        data = serializer.data

        # Assert
        assert data["id"] == project.id
        assert data["title"] == project.title
        assert data["status"] == project.status
        assert data["kind"] == project.kind
        assert data["year"] == project.year
        assert data["number"] == project.number
        assert "business_area" in data
        assert "image" in data
        assert "student_level" in data
        assert "start_date" in data
        assert "end_date" in data

    def test_get_student_level(self, project, db):
        """Test get_student_level returns level from student_project_info"""
        # Arrange
        from projects.models import StudentProjectDetails

        StudentProjectDetails.objects.create(
            project=project,
            level="phd",
            organisation="Test University",
        )
        serializer = TinyStudentProjectARSerializer(project)

        # Act
        data = serializer.data

        # Assert
        assert data["student_level"] == "phd"

    def test_serialization_with_image(self, project, mock_image, db):
        """Test serializing student project with image"""
        # Arrange
        from medias.models import ProjectPhoto
        from projects.models import StudentProjectDetails

        StudentProjectDetails.objects.create(
            project=project,
            level="msc",
            organisation="Test University",
        )
        photo = ProjectPhoto.objects.create(
            project=project,
            file=mock_image,
        )
        project.image = photo
        project.save()
        serializer = TinyStudentProjectARSerializer(project)

        # Act
        data = serializer.data

        # Assert
        assert data["image"] is not None
        assert data["student_level"] == "msc"


class TestProjectDataTableSerializer:
    """Tests for ProjectDataTableSerializer"""

    def test_serialization(self, project, db):
        """Test serializing project for data table"""
        # Arrange
        serializer = ProjectDataTableSerializer(project)

        # Act
        data = serializer.data

        # Assert
        assert data["id"] == project.id
        assert data["title"] == project.title
        assert "role" in data
        assert "tag" in data
        assert "image" in data
        assert "kind" in data
        assert "created_at" in data
        assert "status" in data
        assert "business_area" in data
        assert "description" in data
        assert "start_date" in data
        assert "end_date" in data

    def test_get_start_date_with_date(self, project, db):
        """Test get_start_date returns year when start_date exists"""
        # Arrange
        from datetime import date

        project.start_date = date(2023, 1, 15)
        project.save()
        serializer = ProjectDataTableSerializer(project)

        # Act
        data = serializer.data

        # Assert
        assert data["start_date"] == 2023

    def test_get_start_date_without_date(self, project, db):
        """Test get_start_date returns None when no start_date"""
        # Arrange
        project.start_date = None
        project.save()
        serializer = ProjectDataTableSerializer(project)

        # Act
        data = serializer.data

        # Assert
        assert data["start_date"] is None

    def test_get_end_date_with_date(self, project, db):
        """Test get_end_date returns year when end_date exists"""
        # Arrange
        from datetime import date

        project.start_date = date(2023, 1, 15)  # Required for get_end_date to work
        project.end_date = date(2024, 12, 31)
        project.save()
        serializer = ProjectDataTableSerializer(project)

        # Act
        data = serializer.data

        # Assert
        assert data["end_date"] == 2024

    def test_get_end_date_without_date(self, project, db):
        """Test get_end_date returns None when no start_date"""
        # Arrange
        project.start_date = None
        project.end_date = None
        project.save()
        serializer = ProjectDataTableSerializer(project)

        # Act
        data = serializer.data

        # Assert
        assert data["end_date"] is None

    def test_get_role_from_context(self, project, db):
        """Test get_role returns role from context"""
        # Arrange
        projects_with_roles = [(project, "supervising")]
        context = {"projects_with_roles": projects_with_roles}
        serializer = ProjectDataTableSerializer(project, context=context)

        # Act
        data = serializer.data

        # Assert
        assert data["role"] == "supervising"

    def test_get_role_without_context(self, project, db):
        """Test get_role returns None when no context"""
        # Arrange
        serializer = ProjectDataTableSerializer(project)

        # Act
        data = serializer.data

        # Assert
        assert data["role"] is None

    def test_get_role_not_in_context(self, db):
        """Test get_role returns None when project not in context"""
        # Arrange
        from agencies.models import Agency, BusinessArea
        from projects.models import Project

        agency = Agency.objects.create(name="Test Agency")
        business_area = BusinessArea.objects.create(
            name="Test BA",
            agency=agency,
            leader=None,
            finance_admin=None,
            data_custodian=None,
        )
        project1 = Project.objects.create(
            title="Project 1",
            kind="science",
            status="new",
            year=2023,
            number=5,
            business_area=business_area,
        )
        project2 = Project.objects.create(
            title="Project 2",
            kind="science",
            status="new",
            year=2023,
            number=6,
            business_area=business_area,
        )

        projects_with_roles = [(project1, "supervising")]
        context = {"projects_with_roles": projects_with_roles}
        serializer = ProjectDataTableSerializer(project2, context=context)

        # Act
        data = serializer.data

        # Assert
        assert data["role"] is None

    def test_get_tag(self, project, db):
        """Test get_tag returns project tag"""
        # Arrange
        project.kind = "science"
        project.year = 2023
        project.number = 42
        project.save()
        serializer = ProjectDataTableSerializer(project)

        # Act
        data = serializer.data

        # Assert
        assert data["tag"] == "SP-2023-42"

    def test_get_description_science_project(self, project, db):
        """Test get_description returns project description for science project"""
        # Arrange
        project.kind = "science"
        project.description = "Science project description"
        project.save()
        serializer = ProjectDataTableSerializer(project)

        # Act
        data = serializer.data

        # Assert
        assert data["description"] == "Science project description"

    def test_get_description_external_project(self, db):
        """Test get_description returns external description for external project"""
        # Arrange
        from agencies.models import Agency, BusinessArea
        from projects.models import ExternalProjectDetails, Project

        agency = Agency.objects.create(name="Test Agency")
        business_area = BusinessArea.objects.create(
            name="Test BA",
            agency=agency,
            leader=None,
            finance_admin=None,
            data_custodian=None,
        )
        project = Project.objects.create(
            title="External Project",
            kind="external",
            status="new",
            year=2023,
            number=7,
            business_area=business_area,
            description="Project description",
        )
        ExternalProjectDetails.objects.create(
            project=project,
            collaboration_with="Partner",
            budget="$100,000",
            description="External project description",
            aims="Test aims",
        )
        serializer = ProjectDataTableSerializer(project)

        # Act
        data = serializer.data

        # Assert
        assert data["description"] == "External project description"

    def test_get_description_external_project_no_info(self, db):
        """Test get_description returns empty string for external project without info"""
        # Arrange
        from agencies.models import Agency, BusinessArea
        from projects.models import Project

        agency = Agency.objects.create(name="Test Agency")
        business_area = BusinessArea.objects.create(
            name="Test BA",
            agency=agency,
            leader=None,
            finance_admin=None,
            data_custodian=None,
        )
        project = Project.objects.create(
            title="External Project",
            kind="external",
            status="new",
            year=2023,
            number=8,
            business_area=business_area,
            description="Project description",
        )
        serializer = ProjectDataTableSerializer(project)

        # Act
        data = serializer.data

        # Assert
        assert data["description"] == ""
