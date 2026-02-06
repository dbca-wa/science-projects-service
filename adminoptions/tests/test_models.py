"""
Tests for adminoptions models
"""
import pytest
from django.core.exceptions import ValidationError
from django.core.cache import cache
from adminoptions.models import (
    AdminOptions,
    AdminTask,
    ContentField,
    GuideSection,
)
from caretakers.models import Caretaker


class TestContentFieldModel:
    """Tests for ContentField model"""

    def test_create_content_field(self, guide_section, db):
        """Test creating content field with valid data"""
        field = ContentField.objects.create(
            title="Test Field",
            field_key="test_key",
            description="Test description",
            section=guide_section,
            order=1,
        )
        assert field.id is not None
        assert field.title == "Test Field"
        assert field.field_key == "test_key"
        assert field.description == "Test description"
        assert field.section == guide_section
        assert field.order == 1

    def test_content_field_str_method(self, content_field, db):
        """Test ContentField __str__ method"""
        expected = f"{content_field.section.title} - {content_field.field_key}"
        assert str(content_field) == expected

    def test_content_field_ordering(self, guide_section, db):
        """Test ContentField ordering by order field"""
        field1 = ContentField.objects.create(
            field_key="field1", section=guide_section, order=2
        )
        field2 = ContentField.objects.create(
            field_key="field2", section=guide_section, order=1
        )
        field3 = ContentField.objects.create(
            field_key="field3", section=guide_section, order=3
        )

        fields = list(ContentField.objects.all())
        assert fields[0] == field2
        assert fields[1] == field1
        assert fields[2] == field3

    def test_content_field_unique_together(self, guide_section, db):
        """Test ContentField unique_together constraint"""
        ContentField.objects.create(
            field_key="unique_key", section=guide_section, order=1
        )

        with pytest.raises(Exception):  # IntegrityError
            ContentField.objects.create(
                field_key="unique_key", section=guide_section, order=2
            )


class TestGuideSectionModel:
    """Tests for GuideSection model"""

    def test_create_guide_section(self, db):
        """Test creating guide section with valid data"""
        section = GuideSection.objects.create(
            id="test-section",
            title="Test Section",
            order=1,
            show_divider_after=True,
            category="test",
            is_active=True,
        )
        assert section.id == "test-section"
        assert section.title == "Test Section"
        assert section.order == 1
        assert section.show_divider_after is True
        assert section.category == "test"
        assert section.is_active is True

    def test_guide_section_str_method(self, guide_section, db):
        """Test GuideSection __str__ method"""
        assert str(guide_section) == guide_section.title

    def test_guide_section_ordering(self, db):
        """Test GuideSection ordering by order field"""
        section1 = GuideSection.objects.create(
            id="section1", title="Section 1", order=2
        )
        section2 = GuideSection.objects.create(
            id="section2", title="Section 2", order=1
        )
        section3 = GuideSection.objects.create(
            id="section3", title="Section 3", order=3
        )

        sections = list(GuideSection.objects.all())
        assert sections[0] == section2
        assert sections[1] == section1
        assert sections[2] == section3

    def test_guide_section_defaults(self, db):
        """Test GuideSection default values"""
        section = GuideSection.objects.create(id="defaults", title="Defaults")
        assert section.order == 0
        assert section.show_divider_after is False
        assert section.is_active is True


class TestAdminOptionsModel:
    """Tests for AdminOptions model"""

    def test_create_admin_options(self, admin_user, db):
        """Test creating AdminOptions with valid data"""
        options = AdminOptions.objects.create(
            email_options=AdminOptions.EmailOptions.ENABLED,
            maintainer=admin_user,
            guide_content={"test": "content"},
        )
        assert options.id is not None
        assert options.email_options == AdminOptions.EmailOptions.ENABLED
        assert options.maintainer == admin_user
        assert options.guide_content == {"test": "content"}

    def test_admin_options_str_method(self, admin_options, db):
        """Test AdminOptions __str__ method"""
        assert str(admin_options) == "Admin Options"

    def test_admin_options_email_choices(self, admin_user, db):
        """Test AdminOptions email_options choices"""
        for choice in AdminOptions.EmailOptions:
            options = AdminOptions.objects.create(
                email_options=choice, maintainer=admin_user
            )
            assert options.email_options == choice
            options.delete()

    def test_admin_options_get_guide_content(self, admin_options, db):
        """Test get_guide_content method"""
        content = admin_options.get_guide_content("test_field")
        assert content == "Test content"

        # Test non-existent key
        content = admin_options.get_guide_content("nonexistent")
        assert content == ""

    def test_admin_options_set_guide_content(self, admin_options, db):
        """Test set_guide_content method"""
        admin_options.set_guide_content("new_field", "New content")
        assert admin_options.guide_content["new_field"] == "New content"

        # Verify it was saved
        refreshed = AdminOptions.objects.get(pk=admin_options.pk)
        assert refreshed.guide_content["new_field"] == "New content"

    def test_admin_options_singleton_validation(self, admin_options, db):
        """Test that only one AdminOptions instance can exist"""
        with pytest.raises(ValidationError):
            new_options = AdminOptions(email_options=AdminOptions.EmailOptions.DISABLED)
            new_options.clean()

    def test_admin_options_defaults(self, admin_user, db):
        """Test AdminOptions default values"""
        options = AdminOptions.objects.create(maintainer=admin_user)
        assert options.email_options == AdminOptions.EmailOptions.DISABLED
        assert options.guide_content == {}


class TestAdminTaskModel:
    """Tests for AdminTask model"""

    def test_create_admin_task_delete_project(self, user, project, db):
        """Test creating AdminTask for project deletion"""
        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.DELETEPROJECT,
            status=AdminTask.TaskStatus.PENDING,
            project=project,
            requester=user,
            reason="Test reason",
        )
        assert task.id is not None
        assert task.action == AdminTask.ActionTypes.DELETEPROJECT
        assert task.status == AdminTask.TaskStatus.PENDING
        assert task.project == project
        assert task.requester == user
        assert task.reason == "Test reason"

    def test_create_admin_task_merge_user(self, user, secondary_user, db):
        """Test creating AdminTask for user merge"""
        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.MERGEUSER,
            status=AdminTask.TaskStatus.PENDING,
            primary_user=user,
            secondary_users=[secondary_user.pk],
            requester=user,
            reason="Test merge",
        )
        assert task.action == AdminTask.ActionTypes.MERGEUSER
        assert task.primary_user == user
        assert task.secondary_users == [secondary_user.pk]

    def test_create_admin_task_set_caretaker(self, user, secondary_user, db):
        """Test creating AdminTask for setting caretaker"""
        task = AdminTask.objects.create(
            action=AdminTask.ActionTypes.SETCARETAKER,
            status=AdminTask.TaskStatus.PENDING,
            primary_user=user,
            secondary_users=[secondary_user.pk],
            requester=user,
            reason="Test caretaker",
        )
        assert task.action == AdminTask.ActionTypes.SETCARETAKER
        assert task.primary_user == user
        assert task.secondary_users == [secondary_user.pk]

    def test_admin_task_str_method(self, admin_task_delete_project, db):
        """Test AdminTask __str__ method"""
        task = admin_task_delete_project
        expected = f"{task.action} - {task.project} - {task.requester}"
        assert str(task) == expected

    def test_admin_task_action_choices(self, user, db):
        """Test AdminTask action choices"""
        for action in AdminTask.ActionTypes:
            task = AdminTask.objects.create(
                action=action, status=AdminTask.TaskStatus.PENDING, requester=user
            )
            assert task.action == action
            task.delete()

    def test_admin_task_status_choices(self, user, db):
        """Test AdminTask status choices"""
        for status in AdminTask.TaskStatus:
            task = AdminTask.objects.create(
                action=AdminTask.ActionTypes.DELETEPROJECT, status=status, requester=user
            )
            assert task.status == status
            task.delete()


class TestCaretakerModel:
    """Tests for Caretaker model"""

    def test_create_caretaker(self, user, secondary_user, db):
        """Test creating Caretaker with valid data"""
        caretaker = Caretaker.objects.create(
            user=user, caretaker=secondary_user, reason="Test reason"
        )
        assert caretaker.id is not None
        assert caretaker.user == user
        assert caretaker.caretaker == secondary_user
        assert caretaker.reason == "Test reason"

    def test_caretaker_str_method(self, caretaker, db):
        """Test Caretaker __str__ method
        
        NOTE: Using caretakers app model, not adminoptions model.
        The caretakers app model has a different __str__ format.
        """
        # Caretakers app format: "{caretaker} caretaking for {user}"
        expected = f"{caretaker.caretaker} caretaking for {caretaker.user}"
        assert str(caretaker) == expected

    def test_caretaker_cache_clear_on_save(self, user, secondary_user, db):
        """Test that cache is cleared when caretaker is saved"""
        # Set some cache values
        cache.set(f"caretakers_{user.pk}", "test_value")
        cache.set(f"caretaking_{user.pk}", "test_value")
        cache.set(f"caretakers_{secondary_user.pk}", "test_value")
        cache.set(f"caretaking_{secondary_user.pk}", "test_value")

        # Create caretaker (triggers save)
        Caretaker.objects.create(
            user=user, caretaker=secondary_user, reason="Test"
        )

        # Verify cache was cleared
        assert cache.get(f"caretakers_{user.pk}") is None
        assert cache.get(f"caretaking_{user.pk}") is None
        assert cache.get(f"caretakers_{secondary_user.pk}") is None
        assert cache.get(f"caretaking_{secondary_user.pk}") is None

    def test_caretaker_cache_clear_on_delete(self, caretaker, db):
        """Test that cache is cleared when caretaker is deleted"""
        user_pk = caretaker.user.pk
        caretaker_pk = caretaker.caretaker.pk

        # Set some cache values
        cache.set(f"caretakers_{user_pk}", "test_value")
        cache.set(f"caretaking_{user_pk}", "test_value")
        cache.set(f"caretakers_{caretaker_pk}", "test_value")
        cache.set(f"caretaking_{caretaker_pk}", "test_value")

        # Delete caretaker
        caretaker.delete()

        # Verify cache was cleared
        assert cache.get(f"caretakers_{user_pk}") is None
        assert cache.get(f"caretaking_{user_pk}") is None
        assert cache.get(f"caretakers_{caretaker_pk}") is None
        assert cache.get(f"caretaking_{caretaker_pk}") is None

    def test_caretaker_with_end_date(self, user, secondary_user, db):
        """Test creating Caretaker with end_date"""
        from django.utils import timezone
        from datetime import timedelta

        end_date = timezone.now() + timedelta(days=30)
        caretaker = Caretaker.objects.create(
            user=user, caretaker=secondary_user, reason="Test", end_date=end_date
        )
        assert caretaker.end_date == end_date

    def test_caretaker_with_notes(self, user, secondary_user, db):
        """Test creating Caretaker with notes"""
        caretaker = Caretaker.objects.create(
            user=user,
            caretaker=secondary_user,
            reason="Test",
            notes="Additional notes",
        )
        assert caretaker.notes == "Additional notes"
