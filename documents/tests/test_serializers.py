"""
Tests for document serializers
"""

from documents.serializers.base import (
    AnnualReportCreateSerializer,
    AnnualReportSerializer,
    AnnualReportUpdateSerializer,
    MiniAnnualReportSerializer,
    ProjectDocumentCreateSerializer,
    ProjectDocumentSerializer,
    ProjectDocumentUpdateSerializer,
    TinyAnnualReportSerializer,
    TinyProjectDocumentSerializer,
    TinyProjectDocumentSerializerWithUserDocsBelongTo,
)


class TestTinyProjectDocumentSerializer:
    """Tests for TinyProjectDocumentSerializer"""

    def test_serialization(self, project_document, db):
        """Test serializing a project document"""
        # Arrange
        serializer = TinyProjectDocumentSerializer(project_document)

        # Act
        data = serializer.data

        # Assert
        assert data["id"] == project_document.id
        assert data["kind"] == project_document.kind
        assert data["status"] == project_document.status
        assert "project" in data
        assert "created_year" in data
        assert data["created_year"] == project_document.created_at.year


class TestProjectDocumentSerializer:
    """Tests for ProjectDocumentSerializer"""

    def test_serialization(self, project_document, db):
        """Test serializing a project document"""
        # Arrange
        serializer = ProjectDocumentSerializer(project_document)

        # Act
        data = serializer.data

        # Assert
        assert data["id"] == project_document.id
        assert data["kind"] == project_document.kind
        assert data["status"] == project_document.status
        assert "project" in data
        assert "pdf" in data


class TestProjectDocumentCreateSerializer:
    """Tests for ProjectDocumentCreateSerializer"""

    def test_validation_valid_data(self, project_with_lead, db):
        """Test validation with valid data"""
        # Arrange
        data = {
            "project": project_with_lead.id,
            "kind": "concept",
        }
        serializer = ProjectDocumentCreateSerializer(data=data)

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is True
        assert serializer.validated_data["kind"] == "concept"

    def test_validation_missing_required_field(self, db):
        """Test validation with missing required field"""
        # Arrange
        data = {
            "kind": "concept",
        }
        serializer = ProjectDocumentCreateSerializer(data=data)

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is False
        assert "project" in serializer.errors


class TestProjectDocumentUpdateSerializer:
    """Tests for ProjectDocumentUpdateSerializer"""

    def test_validation_valid_data(self, db):
        """Test validation with valid data"""
        # Arrange
        data = {
            "status": "approved",
        }
        serializer = ProjectDocumentUpdateSerializer(data=data)

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is True
        assert serializer.validated_data["status"] == "approved"


class TestTinyAnnualReportSerializer:
    """Tests for TinyAnnualReportSerializer"""

    def test_serialization(self, annual_report, db):
        """Test serializing an annual report"""
        # Arrange
        serializer = TinyAnnualReportSerializer(annual_report)

        # Act
        data = serializer.data

        # Assert
        assert data["id"] == annual_report.id
        assert data["year"] == annual_report.year
        assert "pdf" in data
        assert "pdf_generation_in_progress" in data


class TestMiniAnnualReportSerializer:
    """Tests for MiniAnnualReportSerializer"""

    def test_serialization(self, annual_report, db):
        """Test serializing an annual report"""
        # Arrange
        serializer = MiniAnnualReportSerializer(annual_report)

        # Act
        data = serializer.data

        # Assert
        assert data["id"] == annual_report.id
        assert data["year"] == annual_report.year
        assert "pdf_generation_in_progress" in data
        assert len(data.keys()) == 3  # Only 3 fields


class TestAnnualReportSerializer:
    """Tests for AnnualReportSerializer"""

    def test_serialization(self, annual_report, db):
        """Test serializing an annual report"""
        # Arrange
        serializer = AnnualReportSerializer(annual_report)

        # Act
        data = serializer.data

        # Assert
        assert data["id"] == annual_report.id
        assert data["year"] == annual_report.year
        assert "dm" in data
        assert "dm_sign" in data


class TestAnnualReportCreateSerializer:
    """Tests for AnnualReportCreateSerializer"""

    def test_validation_valid_data(self, db):
        """Test validation with valid data"""
        # Arrange
        data = {
            "year": 2024,
            "date_open": "2024-01-01",
            "date_closed": "2024-12-31",
        }
        serializer = AnnualReportCreateSerializer(data=data)

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is True
        assert serializer.validated_data["year"] == 2024

    def test_validation_missing_required_field(self, db):
        """Test validation with missing required field"""
        # Arrange
        data = {
            "date_open": "2024-01-01",
            "date_closed": "2024-12-31",
        }
        serializer = AnnualReportCreateSerializer(data=data)

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is False
        assert "year" in serializer.errors


class TestAnnualReportUpdateSerializer:
    """Tests for AnnualReportUpdateSerializer"""

    def test_validation_valid_data(self, db):
        """Test validation with valid data"""
        # Arrange
        data = {
            "dm": "Dr. Test Director",
            "dm_sign": "Test Signature",
            "service_delivery_intro": "Test intro",
            "research_intro": "Research intro",
            "student_intro": "Student intro",
            "publications": "Publications text",
            "is_published": True,
        }
        serializer = AnnualReportUpdateSerializer(data=data, partial=True)

        # Act
        is_valid = serializer.is_valid()

        # Assert
        assert is_valid is True
        assert serializer.validated_data["dm"] == "Dr. Test Director"


class TestTinyProjectDocumentSerializerWithUserDocsBelongTo:
    """Tests for TinyProjectDocumentSerializerWithUserDocsBelongTo"""

    def test_serialization_with_user_context(self, project_document, user, db):
        """Test serializing with user in context"""
        # Arrange
        context = {"for_user": user}
        serializer = TinyProjectDocumentSerializerWithUserDocsBelongTo(
            project_document, context=context
        )

        # Act
        data = serializer.data

        # Assert
        assert data["id"] == project_document.id
        assert "for_user" in data
        assert data["for_user"] is not None
        assert data["for_user"]["id"] == user.pk
        assert data["for_user"]["email"] == user.email
        assert data["for_user"]["display_first_name"] == user.display_first_name
        assert data["for_user"]["display_last_name"] == user.display_last_name
        assert "image" in data["for_user"]

    def test_serialization_with_user_with_avatar(
        self, project_document, user_with_avatar, db
    ):
        """Test serializing with user that has avatar"""
        # Arrange
        context = {"for_user": user_with_avatar}
        serializer = TinyProjectDocumentSerializerWithUserDocsBelongTo(
            project_document, context=context
        )

        # Act
        data = serializer.data

        # Assert
        assert data["for_user"] is not None
        assert data["for_user"]["image"] is not None
        assert "avatar" in data["for_user"]["image"]

    def test_serialization_without_user_context(self, project_document, db):
        """Test serializing without user in context"""
        # Arrange
        serializer = TinyProjectDocumentSerializerWithUserDocsBelongTo(project_document)

        # Act
        data = serializer.data

        # Assert
        assert data["id"] == project_document.id
        assert "for_user" in data
        assert data["for_user"] is None

    def test_get_created_year(self, project_document, db):
        """Test get_created_year method"""
        # Arrange
        serializer = TinyProjectDocumentSerializerWithUserDocsBelongTo(project_document)

        # Act
        data = serializer.data

        # Assert
        assert "created_year" in data
        assert data["created_year"] == project_document.created_at.year
