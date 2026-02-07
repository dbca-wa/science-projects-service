"""
Tests for location services
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound

from locations.models import Area
from locations.services.area_service import AreaService

User = get_user_model()


class TestAreaService:
    """Tests for Area service operations"""

    def test_list_areas(self, dbca_region, dbca_district, ibra_region, db):
        """Test listing all areas"""
        # Act
        areas = AreaService.list_areas()

        # Assert
        assert areas.count() == 3
        assert dbca_region in areas
        assert dbca_district in areas
        assert ibra_region in areas

    def test_list_areas_filtered_by_type(
        self, dbca_region, dbca_district, ibra_region, db
    ):
        """Test listing areas filtered by type"""
        # Act
        dbca_regions = AreaService.list_areas(
            area_type=Area.AreaTypeChoices.AREA_TYPE_DBCA_REGION
        )

        # Assert
        assert dbca_regions.count() == 1
        assert dbca_region in dbca_regions
        assert dbca_district not in dbca_regions
        assert ibra_region not in dbca_regions

    def test_list_areas_empty(self, db):
        """Test listing areas when none exist"""
        # Act
        areas = AreaService.list_areas()

        # Assert
        assert areas.count() == 0

    def test_get_area(self, dbca_region, db):
        """Test getting area by ID"""
        # Act
        area = AreaService.get_area(dbca_region.id)

        # Assert
        assert area.id == dbca_region.id
        assert area.name == "Test DBCA Region"
        assert area.area_type == Area.AreaTypeChoices.AREA_TYPE_DBCA_REGION

    def test_get_area_not_found(self, db):
        """Test getting non-existent area raises NotFound"""
        # Act & Assert
        with pytest.raises(NotFound, match="Area 999 not found"):
            AreaService.get_area(999)

    def test_create_area(self, user, db):
        """Test creating an area"""
        # Arrange
        data = {
            "name": "New DBCA Region",
            "area_type": Area.AreaTypeChoices.AREA_TYPE_DBCA_REGION,
        }

        # Act
        area = AreaService.create_area(user, data)

        # Assert
        assert area.id is not None
        assert area.name == "New DBCA Region"
        assert area.area_type == Area.AreaTypeChoices.AREA_TYPE_DBCA_REGION

    def test_create_area_all_types(self, user, db):
        """Test creating areas of all types"""
        # Arrange
        area_types = [
            Area.AreaTypeChoices.AREA_TYPE_DBCA_REGION,
            Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
            Area.AreaTypeChoices.AREA_TYPE_IBRA_REGION,
            Area.AreaTypeChoices.AREA_TYPE_IMCRA_REGION,
            Area.AreaTypeChoices.AREA_TYPE_NRM_REGION,
        ]

        # Act & Assert
        for i, area_type in enumerate(area_types):
            data = {
                "name": f"Test Area {i}",
                "area_type": area_type,
            }
            area = AreaService.create_area(user, data)
            assert area.id is not None
            assert area.area_type == area_type

    def test_update_area(self, dbca_region, user, db):
        """Test updating an area"""
        # Arrange
        data = {"name": "Updated DBCA Region"}

        # Act
        updated = AreaService.update_area(dbca_region.id, user, data)

        # Assert
        assert updated.id == dbca_region.id
        assert updated.name == "Updated DBCA Region"
        assert updated.area_type == Area.AreaTypeChoices.AREA_TYPE_DBCA_REGION

    def test_update_area_type(self, dbca_region, user, db):
        """Test updating area type"""
        # Arrange
        data = {"area_type": Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT}

        # Act
        updated = AreaService.update_area(dbca_region.id, user, data)

        # Assert
        assert updated.id == dbca_region.id
        assert updated.area_type == Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT

    def test_update_area_not_found(self, user, db):
        """Test updating non-existent area raises NotFound"""
        # Arrange
        data = {"name": "Updated Name"}

        # Act & Assert
        with pytest.raises(NotFound, match="Area 999 not found"):
            AreaService.update_area(999, user, data)

    def test_delete_area(self, dbca_region, user, db):
        """Test deleting an area"""
        # Arrange
        area_id = dbca_region.id

        # Act
        AreaService.delete_area(area_id, user)

        # Assert
        assert not Area.objects.filter(id=area_id).exists()

    def test_delete_area_not_found(self, user, db):
        """Test deleting non-existent area raises NotFound"""
        # Act & Assert
        with pytest.raises(NotFound, match="Area 999 not found"):
            AreaService.delete_area(999, user)


class TestAreaModelValidation:
    """Tests for Area model validation"""

    def test_area_unique_together(self, db):
        """Test area name and type must be unique together"""
        # Arrange
        Area.objects.create(
            name="Test Area",
            area_type=Area.AreaTypeChoices.AREA_TYPE_DBCA_REGION,
        )

        # Act & Assert - Same name and type should fail
        with pytest.raises(Exception):  # IntegrityError
            Area.objects.create(
                name="Test Area",
                area_type=Area.AreaTypeChoices.AREA_TYPE_DBCA_REGION,
            )

    def test_area_same_name_different_type(self, db):
        """Test same name with different type is allowed"""
        # Arrange
        Area.objects.create(
            name="Test Area",
            area_type=Area.AreaTypeChoices.AREA_TYPE_DBCA_REGION,
        )

        # Act - Same name, different type should succeed
        area2 = Area.objects.create(
            name="Test Area",
            area_type=Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
        )

        # Assert
        assert area2.id is not None
        assert area2.name == "Test Area"
        assert area2.area_type == Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT

    def test_area_str_representation(self, dbca_region, db):
        """Test area string representation"""
        # Act
        str_repr = str(dbca_region)

        # Assert
        assert str_repr == "Test DBCA Region"
