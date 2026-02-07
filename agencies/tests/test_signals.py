"""
Tests for agencies signals
"""

from unittest.mock import patch

from django.conf import settings

from agencies.models import Affiliation
from common.tests.factories import AffiliationFactory, ProjectFactory
from projects.models import ExternalProjectDetails, StudentProjectDetails


class TestUpdateProjectAffiliationsOnNameChange:
    """Tests for update_project_affiliations_on_name_change signal"""

    def test_new_affiliation_creation_no_signal(self, db):
        """Test signal does not trigger for new affiliation creation"""
        # Arrange & Act
        affiliation = AffiliationFactory(name="New Affiliation")

        # Assert - just verify it was created without errors
        assert affiliation.id is not None
        assert affiliation.name == "New Affiliation"

    @patch.object(settings, "LOGGER")
    def test_affiliation_name_unchanged_no_update(self, mock_logger, db):
        """Test signal does not update projects when name unchanged"""
        # Arrange
        affiliation = AffiliationFactory(name="Test Affiliation")
        project = ProjectFactory()
        StudentProjectDetails.objects.create(
            project=project, organisation="Test Affiliation"
        )

        # Act - save without changing name
        affiliation.save()

        # Assert - no logging should occur
        mock_logger.info.assert_not_called()

    @patch.object(settings, "LOGGER")
    def test_affiliation_name_change_updates_student_project(self, mock_logger, db):
        """Test signal updates StudentProjectDetails when affiliation name changes"""
        # Arrange
        affiliation = AffiliationFactory(name="Old Name")
        project = ProjectFactory()
        student_project = StudentProjectDetails.objects.create(
            project=project, organisation="Old Name"
        )

        # Act - change affiliation name
        affiliation.name = "New Name"
        affiliation.save()

        # Assert
        student_project.refresh_from_db()
        assert student_project.organisation == "New Name"
        mock_logger.info.assert_called_once()
        assert "Old Name" in mock_logger.info.call_args[0][0]
        assert "New Name" in mock_logger.info.call_args[0][0]
        assert "1 student project(s)" in mock_logger.info.call_args[0][0]

    @patch.object(settings, "LOGGER")
    def test_affiliation_name_change_updates_external_project(self, mock_logger, db):
        """Test signal updates ExternalProjectDetails when affiliation name changes"""
        # Arrange
        affiliation = AffiliationFactory(name="Old Name")
        project = ProjectFactory()
        external_project = ExternalProjectDetails.objects.create(
            project=project, collaboration_with="Old Name"
        )

        # Act - change affiliation name
        affiliation.name = "New Name"
        affiliation.save()

        # Assert
        external_project.refresh_from_db()
        assert external_project.collaboration_with == "New Name"
        mock_logger.info.assert_called_once()
        assert "Old Name" in mock_logger.info.call_args[0][0]
        assert "New Name" in mock_logger.info.call_args[0][0]
        assert "1 external project(s)" in mock_logger.info.call_args[0][0]

    @patch.object(settings, "LOGGER")
    def test_affiliation_name_change_updates_multiple_projects(self, mock_logger, db):
        """Test signal updates multiple projects when affiliation name changes"""
        # Arrange
        affiliation = AffiliationFactory(name="Old Name")
        project1 = ProjectFactory()
        project2 = ProjectFactory()
        project3 = ProjectFactory()

        student_project1 = StudentProjectDetails.objects.create(
            project=project1, organisation="Old Name"
        )
        student_project2 = StudentProjectDetails.objects.create(
            project=project2, organisation="Old Name"
        )
        external_project = ExternalProjectDetails.objects.create(
            project=project3, collaboration_with="Old Name"
        )

        # Act - change affiliation name
        affiliation.name = "New Name"
        affiliation.save()

        # Assert
        student_project1.refresh_from_db()
        student_project2.refresh_from_db()
        external_project.refresh_from_db()

        assert student_project1.organisation == "New Name"
        assert student_project2.organisation == "New Name"
        assert external_project.collaboration_with == "New Name"

        mock_logger.info.assert_called_once()
        assert "2 student project(s)" in mock_logger.info.call_args[0][0]
        assert "1 external project(s)" in mock_logger.info.call_args[0][0]

    @patch.object(settings, "LOGGER")
    def test_affiliation_name_change_with_semicolon_delimited_field(
        self, mock_logger, db
    ):
        """Test signal updates semicolon-delimited affiliation fields"""
        # Arrange
        affiliation = AffiliationFactory(name="Old Name")
        project = ProjectFactory()
        student_project = StudentProjectDetails.objects.create(
            project=project, organisation="Other Org; Old Name; Another Org"
        )

        # Act - change affiliation name
        affiliation.name = "New Name"
        affiliation.save()

        # Assert
        student_project.refresh_from_db()
        assert student_project.organisation == "Other Org; New Name; Another Org"
        mock_logger.info.assert_called_once()

    @patch.object(settings, "LOGGER")
    def test_affiliation_name_change_only_updates_exact_match(self, mock_logger, db):
        """Test signal only updates exact matches in semicolon-delimited fields"""
        # Arrange
        affiliation = AffiliationFactory(name="Test")
        project = ProjectFactory()
        student_project = StudentProjectDetails.objects.create(
            project=project, organisation="Test Org; Test; Testing"
        )

        # Act - change affiliation name
        affiliation.name = "New Test"
        affiliation.save()

        # Assert
        student_project.refresh_from_db()
        # Only "Test" should be updated, not "Test Org" or "Testing"
        assert student_project.organisation == "Test Org; New Test; Testing"

    @patch.object(settings, "LOGGER")
    def test_affiliation_name_change_with_empty_organisation(self, mock_logger, db):
        """Test signal handles empty organisation field gracefully"""
        # Arrange
        affiliation = AffiliationFactory(name="Old Name")
        project = ProjectFactory()
        student_project = StudentProjectDetails.objects.create(
            project=project, organisation=""
        )

        # Act - change affiliation name
        affiliation.name = "New Name"
        affiliation.save()

        # Assert
        student_project.refresh_from_db()
        assert student_project.organisation == ""
        # No logging should occur since no projects were updated
        mock_logger.info.assert_not_called()

    @patch.object(settings, "LOGGER")
    def test_affiliation_name_change_with_none_organisation(self, mock_logger, db):
        """Test signal handles None organisation field gracefully"""
        # Arrange
        affiliation = AffiliationFactory(name="Old Name")
        project = ProjectFactory()
        student_project = StudentProjectDetails.objects.create(
            project=project, organisation=None
        )

        # Act - change affiliation name
        affiliation.name = "New Name"
        affiliation.save()

        # Assert
        student_project.refresh_from_db()
        assert student_project.organisation is None
        # No logging should occur since no projects were updated
        mock_logger.info.assert_not_called()

    @patch.object(settings, "LOGGER")
    def test_affiliation_name_change_case_sensitive(self, mock_logger, db):
        """Test signal is case-sensitive when matching affiliation names"""
        # Arrange
        affiliation = AffiliationFactory(name="Test Org")
        project = ProjectFactory()
        student_project = StudentProjectDetails.objects.create(
            project=project, organisation="test org; Test Org; TEST ORG"
        )

        # Act - change affiliation name
        affiliation.name = "New Org"
        affiliation.save()

        # Assert
        student_project.refresh_from_db()
        # Only exact match "Test Org" should be updated
        assert student_project.organisation == "test org; New Org; TEST ORG"

    @patch.object(settings, "LOGGER")
    def test_affiliation_does_not_exist_exception_handled(self, mock_logger, db):
        """Test signal handles DoesNotExist exception gracefully"""
        # Arrange
        affiliation = AffiliationFactory(name="Test")

        # Act - mock DoesNotExist exception
        with patch("agencies.models.Affiliation.objects.get") as mock_get:
            mock_get.side_effect = Affiliation.DoesNotExist
            affiliation.name = "New Name"
            affiliation.save()

        # Assert - no error should be raised, no logging
        mock_logger.error.assert_not_called()

    @patch.object(settings, "LOGGER")
    def test_general_exception_logged(self, mock_logger, db):
        """Test signal logs general exceptions"""
        # Arrange
        affiliation = AffiliationFactory(name="Test")

        # Act - mock general exception
        with patch("agencies.models.Affiliation.objects.get") as mock_get:
            mock_get.side_effect = Exception("Test error")
            affiliation.name = "New Name"
            affiliation.save()

        # Assert - error should be logged
        mock_logger.error.assert_called_once()
        assert (
            "Error updating project affiliations" in mock_logger.error.call_args[0][0]
        )
        assert "Test error" in mock_logger.error.call_args[0][0]

    @patch.object(settings, "LOGGER")
    def test_affiliation_name_change_with_whitespace_handling(self, mock_logger, db):
        """Test signal handles whitespace in semicolon-delimited fields"""
        # Arrange
        affiliation = AffiliationFactory(name="Test Org")
        project = ProjectFactory()
        student_project = StudentProjectDetails.objects.create(
            project=project,
            organisation="Other Org; Test Org; Another Org",  # With spaces after semicolons
        )

        # Act - change affiliation name
        affiliation.name = "New Org"
        affiliation.save()

        # Assert
        student_project.refresh_from_db()
        # Should handle whitespace correctly
        assert "New Org" in student_project.organisation
        assert student_project.organisation == "Other Org; New Org; Another Org"
