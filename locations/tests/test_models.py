"""
Tests for locations models
"""
import pytest
from django.db import IntegrityError
from django.core.exceptions import ValidationError

from locations.models import Area


class TestAreaModel:
    """Tests for Area model"""

    def test_create_area_valid_data(self, db):
        """Test creating area with valid data"""
        area = Area.objects.create(
            name='Perth District',
            area_type=Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
            old_id=100,
        )
        
        assert area.id is not None
        assert area.name == 'Perth District'
        assert area.area_type == 'dbcadistrict'
        assert area.old_id == 100
        assert area.created_at is not None
        assert area.updated_at is not None

    def test_area_str_method(self, db):
        """Test Area __str__ method returns name"""
        area = Area.objects.create(
            name='Perth District',
            area_type=Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
            old_id=100,
        )
        
        assert str(area) == 'Perth District'

    def test_area_type_dbca_region(self, db):
        """Test creating area with DBCA region type"""
        area = Area.objects.create(
            name='Swan Region',
            area_type=Area.AreaTypeChoices.AREA_TYPE_DBCA_REGION,
            old_id=101,
        )
        
        assert area.area_type == 'dbcaregion'

    def test_area_type_dbca_district(self, db):
        """Test creating area with DBCA district type"""
        area = Area.objects.create(
            name='Perth District',
            area_type=Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
            old_id=102,
        )
        
        assert area.area_type == 'dbcadistrict'

    def test_area_type_ibra_region(self, db):
        """Test creating area with IBRA region type"""
        area = Area.objects.create(
            name='Jarrah Forest',
            area_type=Area.AreaTypeChoices.AREA_TYPE_IBRA_REGION,
            old_id=103,
        )
        
        assert area.area_type == 'ibra'

    def test_area_type_imcra_region(self, db):
        """Test creating area with IMCRA region type"""
        area = Area.objects.create(
            name='Southwest Shelf',
            area_type=Area.AreaTypeChoices.AREA_TYPE_IMCRA_REGION,
            old_id=104,
        )
        
        assert area.area_type == 'imcra'

    def test_area_type_nrm_region(self, db):
        """Test creating area with NRM region type"""
        area = Area.objects.create(
            name='South West NRM',
            area_type=Area.AreaTypeChoices.AREA_TYPE_NRM_REGION,
            old_id=105,
        )
        
        assert area.area_type == 'nrm'

    def test_area_unique_together_constraint(self, db):
        """Test unique_together constraint on name and area_type"""
        # Create first area
        Area.objects.create(
            name='Perth District',
            area_type=Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
            old_id=100,
        )
        
        # Try to create duplicate with same name and area_type
        with pytest.raises(IntegrityError):
            Area.objects.create(
                name='Perth District',
                area_type=Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
                old_id=101,
            )

    def test_area_same_name_different_type_allowed(self, db):
        """Test same name with different area_type is allowed"""
        # Create area with DBCA district type
        area1 = Area.objects.create(
            name='Perth',
            area_type=Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
            old_id=100,
        )
        
        # Create area with same name but DBCA region type - should succeed
        area2 = Area.objects.create(
            name='Perth',
            area_type=Area.AreaTypeChoices.AREA_TYPE_DBCA_REGION,
            old_id=101,
        )
        
        assert area1.name == area2.name
        assert area1.area_type != area2.area_type
        assert Area.objects.filter(name='Perth').count() == 2

    def test_area_name_max_length(self, db):
        """Test area name respects max_length of 150"""
        long_name = 'A' * 150
        area = Area.objects.create(
            name=long_name,
            area_type=Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
            old_id=100,
        )
        
        assert len(area.name) == 150
        assert area.name == long_name

    def test_area_name_exceeds_max_length(self, db):
        """Test area name exceeding max_length raises error"""
        too_long_name = 'A' * 151
        
        with pytest.raises(Exception):  # Django will raise DataError or ValidationError
            Area.objects.create(
                name=too_long_name,
                area_type=Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
                old_id=100,
            )

    def test_area_verbose_name(self, db):
        """Test model verbose_name is set correctly"""
        assert Area._meta.verbose_name == 'Area'

    def test_area_verbose_name_plural(self, db):
        """Test model verbose_name_plural is set correctly"""
        assert Area._meta.verbose_name_plural == 'Areas'

    def test_area_created_at_auto_set(self, db):
        """Test created_at is automatically set on creation"""
        area = Area.objects.create(
            name='Test Area',
            area_type=Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
            old_id=100,
        )
        
        assert area.created_at is not None

    def test_area_updated_at_auto_set(self, db):
        """Test updated_at is automatically set on creation"""
        area = Area.objects.create(
            name='Test Area',
            area_type=Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
            old_id=100,
        )
        
        assert area.updated_at is not None

    def test_area_updated_at_changes_on_save(self, db):
        """Test updated_at changes when model is saved"""
        area = Area.objects.create(
            name='Test Area',
            area_type=Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
            old_id=100,
        )
        
        original_updated_at = area.updated_at
        
        # Update the area
        area.name = 'Updated Area'
        area.save()
        
        # Refresh from database
        area.refresh_from_db()
        
        assert area.updated_at > original_updated_at

    def test_area_old_id_field(self, db):
        """Test old_id field stores integer value"""
        area = Area.objects.create(
            name='Test Area',
            area_type=Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
            old_id=12345,
        )
        
        assert area.old_id == 12345
        assert isinstance(area.old_id, int)

    def test_area_queryset_filter_by_type(self, db):
        """Test filtering areas by area_type"""
        # Create areas of different types
        Area.objects.create(
            name='District 1',
            area_type=Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
            old_id=1,
        )
        Area.objects.create(
            name='District 2',
            area_type=Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
            old_id=2,
        )
        Area.objects.create(
            name='Region 1',
            area_type=Area.AreaTypeChoices.AREA_TYPE_DBCA_REGION,
            old_id=3,
        )
        
        # Filter by district type
        districts = Area.objects.filter(
            area_type=Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT
        )
        
        assert districts.count() == 2
        assert all(a.area_type == 'dbcadistrict' for a in districts)

    def test_area_queryset_filter_by_name(self, db):
        """Test filtering areas by name"""
        Area.objects.create(
            name='Perth District',
            area_type=Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
            old_id=1,
        )
        Area.objects.create(
            name='Albany District',
            area_type=Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
            old_id=2,
        )
        
        # Filter by name
        perth_areas = Area.objects.filter(name='Perth District')
        
        assert perth_areas.count() == 1
        assert perth_areas.first().name == 'Perth District'

    def test_area_update_name(self, db):
        """Test updating area name"""
        area = Area.objects.create(
            name='Original Name',
            area_type=Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
            old_id=100,
        )
        
        area.name = 'Updated Name'
        area.save()
        
        area.refresh_from_db()
        assert area.name == 'Updated Name'

    def test_area_update_area_type(self, db):
        """Test updating area type"""
        area = Area.objects.create(
            name='Test Area',
            area_type=Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
            old_id=100,
        )
        
        area.area_type = Area.AreaTypeChoices.AREA_TYPE_DBCA_REGION
        area.save()
        
        area.refresh_from_db()
        assert area.area_type == 'dbcaregion'

    def test_area_delete(self, db):
        """Test deleting an area"""
        area = Area.objects.create(
            name='Test Area',
            area_type=Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
            old_id=100,
        )
        
        area_id = area.id
        area.delete()
        
        assert not Area.objects.filter(id=area_id).exists()

    def test_area_count(self, db):
        """Test counting areas"""
        # Create multiple areas
        for i in range(5):
            Area.objects.create(
                name=f'Area {i}',
                area_type=Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
                old_id=i,
            )
        
        assert Area.objects.count() == 5

    def test_area_ordering(self, db):
        """Test areas can be ordered by name"""
        Area.objects.create(
            name='Zebra District',
            area_type=Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
            old_id=1,
        )
        Area.objects.create(
            name='Alpha District',
            area_type=Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
            old_id=2,
        )
        
        areas = Area.objects.order_by('name')
        
        assert areas.first().name == 'Alpha District'
        assert areas.last().name == 'Zebra District'
