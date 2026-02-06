"""
Tests for locations serializers
"""

import pytest
from django.core.exceptions import ValidationError

from locations.models import Area
from locations.serializers import AreaSerializer, TinyAreaSerializer


class TestTinyAreaSerializer:
    """Tests for TinyAreaSerializer"""

    def test_serialize_area(self, dbca_district, db):
        """Test serializing area to JSON"""
        serializer = TinyAreaSerializer(dbca_district)
        data = serializer.data

        assert "id" in data
        assert "name" in data
        assert "area_type" in data
        assert data["id"] == dbca_district.id
        assert data["name"] == dbca_district.name
        assert data["area_type"] == dbca_district.area_type

    def test_serialize_area_fields_only(self, dbca_district, db):
        """Test TinyAreaSerializer only includes specified fields"""
        serializer = TinyAreaSerializer(dbca_district)
        data = serializer.data

        # Should only have id, name, area_type
        assert set(data.keys()) == {"id", "name", "area_type"}
        # Should not have created_at, updated_at
        assert "created_at" not in data
        assert "updated_at" not in data

    def test_serialize_multiple_areas(self, dbca_district, dbca_region, db):
        """Test serializing multiple areas"""
        areas = [dbca_district, dbca_region]
        serializer = TinyAreaSerializer(areas, many=True)
        data = serializer.data

        assert len(data) == 2
        assert data[0]["name"] == dbca_district.name
        assert data[1]["name"] == dbca_region.name

    def test_serialize_dbca_region(self, dbca_region, db):
        """Test serializing DBCA region area"""
        serializer = TinyAreaSerializer(dbca_region)
        data = serializer.data

        assert data["area_type"] == "dbcaregion"

    def test_serialize_ibra_region(self, ibra_region, db):
        """Test serializing IBRA region area"""
        serializer = TinyAreaSerializer(ibra_region)
        data = serializer.data

        assert data["area_type"] == "ibra"


class TestAreaSerializer:
    """Tests for AreaSerializer"""

    def test_serialize_area_all_fields(self, dbca_district, db):
        """Test serializing area includes all fields"""
        serializer = AreaSerializer(dbca_district)
        data = serializer.data

        assert "id" in data
        assert "name" in data
        assert "area_type" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_serialize_area_values(self, dbca_district, db):
        """Test serialized area has correct values"""
        serializer = AreaSerializer(dbca_district)
        data = serializer.data

        assert data["id"] == dbca_district.id
        assert data["name"] == dbca_district.name
        assert data["area_type"] == dbca_district.area_type

    def test_deserialize_valid_data(self, db):
        """Test deserializing valid JSON to area"""
        data = {
            "name": "Perth District",
            "area_type": Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
        }
        serializer = AreaSerializer(data=data)

        assert serializer.is_valid()
        area = serializer.save()
        assert area.name == "Perth District"
        assert area.area_type == "dbcadistrict"

    def test_deserialize_missing_name(self, db):
        """Test deserializing with missing name fails validation"""
        data = {
            "area_type": Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
        }
        serializer = AreaSerializer(data=data)

        assert not serializer.is_valid()
        assert "name" in serializer.errors

    def test_deserialize_missing_area_type(self, db):
        """Test deserializing with missing area_type fails validation"""
        data = {
            "name": "Perth District",
        }
        serializer = AreaSerializer(data=data)

        assert not serializer.is_valid()
        assert "area_type" in serializer.errors

    def test_deserialize_invalid_area_type(self, db):
        """Test deserializing with invalid area_type fails validation"""
        data = {
            "name": "Test Area",
            "area_type": "invalid_type",
        }
        serializer = AreaSerializer(data=data)

        assert not serializer.is_valid()
        assert "area_type" in serializer.errors

    def test_deserialize_empty_name(self, db):
        """Test deserializing with empty name fails validation"""
        data = {
            "name": "",
            "area_type": Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
        }
        serializer = AreaSerializer(data=data)

        assert not serializer.is_valid()
        assert "name" in serializer.errors

    def test_deserialize_name_too_long(self, db):
        """Test deserializing with name exceeding max_length fails"""
        data = {
            "name": "A" * 151,  # Max length is 150
            "area_type": Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
        }
        serializer = AreaSerializer(data=data)

        assert not serializer.is_valid()
        assert "name" in serializer.errors

    def test_deserialize_name_max_length(self, db):
        """Test deserializing with name at max_length succeeds"""
        data = {
            "name": "A" * 150,  # Exactly max length
            "area_type": Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
        }
        serializer = AreaSerializer(data=data)

        assert serializer.is_valid()
        area = serializer.save()
        assert len(area.name) == 150

    def test_deserialize_all_area_types(self, db):
        """Test deserializing all valid area types"""
        area_types = [
            Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
            Area.AreaTypeChoices.AREA_TYPE_DBCA_REGION,
            Area.AreaTypeChoices.AREA_TYPE_IBRA_REGION,
            Area.AreaTypeChoices.AREA_TYPE_IMCRA_REGION,
            Area.AreaTypeChoices.AREA_TYPE_NRM_REGION,
        ]

        for i, area_type in enumerate(area_types):
            data = {
                "name": f"Test Area {i}",
                "area_type": area_type,
            }
            serializer = AreaSerializer(data=data)

            assert serializer.is_valid(), f"Failed for {area_type}: {serializer.errors}"
            area = serializer.save()
            assert area.area_type == area_type

    def test_update_area_name(self, dbca_district, db):
        """Test updating area name via serializer"""
        data = {
            "name": "Updated District Name",
        }
        serializer = AreaSerializer(dbca_district, data=data, partial=True)

        assert serializer.is_valid()
        area = serializer.save()
        assert area.name == "Updated District Name"
        assert area.area_type == dbca_district.area_type  # Unchanged

    def test_update_area_type(self, dbca_district, db):
        """Test updating area type via serializer"""
        data = {
            "area_type": Area.AreaTypeChoices.AREA_TYPE_DBCA_REGION,
        }
        serializer = AreaSerializer(dbca_district, data=data, partial=True)

        assert serializer.is_valid()
        area = serializer.save()
        assert area.area_type == "dbcaregion"
        assert area.name == dbca_district.name  # Unchanged

    def test_update_area_full(self, dbca_district, db):
        """Test full update of area via serializer"""
        data = {
            "name": "Completely New Name",
            "area_type": Area.AreaTypeChoices.AREA_TYPE_IBRA_REGION,
        }
        serializer = AreaSerializer(dbca_district, data=data)

        assert serializer.is_valid()
        area = serializer.save()
        assert area.name == "Completely New Name"
        assert area.area_type == "ibra"

    def test_serialize_multiple_areas(
        self, dbca_district, dbca_region, ibra_region, db
    ):
        """Test serializing multiple areas"""
        areas = [dbca_district, dbca_region, ibra_region]
        serializer = AreaSerializer(areas, many=True)
        data = serializer.data

        assert len(data) == 3
        assert data[0]["name"] == dbca_district.name
        assert data[1]["name"] == dbca_region.name
        assert data[2]["name"] == ibra_region.name

    def test_deserialize_with_extra_fields(self, db):
        """Test deserializing with extra fields ignores them"""
        data = {
            "name": "Test Area",
            "area_type": Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
            "extra_field": "should be ignored",
        }
        serializer = AreaSerializer(data=data)

        assert serializer.is_valid()
        area = serializer.save()
        assert area.name == "Test Area"
        assert not hasattr(area, "extra_field")

    def test_serialize_area_with_special_characters(self, db):
        """Test serializing area with special characters in name"""
        area = Area.objects.create(
            name="Perth & Peel District (South-West)",
            area_type=Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
        )

        serializer = AreaSerializer(area)
        data = serializer.data

        assert data["name"] == "Perth & Peel District (South-West)"

    def test_deserialize_area_with_special_characters(self, db):
        """Test deserializing area with special characters in name"""
        data = {
            "name": "Perth & Peel District (South-West)",
            "area_type": Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
        }
        serializer = AreaSerializer(data=data)

        assert serializer.is_valid()
        area = serializer.save()
        assert area.name == "Perth & Peel District (South-West)"

    def test_serialize_preserves_timestamps(self, dbca_district, db):
        """Test serialization preserves created_at and updated_at"""
        serializer = AreaSerializer(dbca_district)
        data = serializer.data

        assert "created_at" in data
        assert "updated_at" in data
        assert data["created_at"] is not None
        assert data["updated_at"] is not None

    def test_deserialize_ignores_id(self, db):
        """Test deserializing with id field ignores it for new objects"""
        data = {
            "id": 999,  # Should be ignored
            "name": "Test Area",
            "area_type": Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
        }
        serializer = AreaSerializer(data=data)

        assert serializer.is_valid()
        area = serializer.save()
        # ID should be auto-generated, not 999
        assert area.id != 999
