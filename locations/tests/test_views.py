"""
Tests for locations views
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from common.tests.test_helpers import locations_urls
from locations.models import Area


@pytest.fixture
def api_client():
    """Provide API client"""
    return APIClient()


class TestAreasView:
    """Tests for Areas list/create view"""

    def test_list_areas(self, api_client, user, dbca_district, dbca_region, db):
        """Test listing all areas"""
        api_client.force_authenticate(user=user)

        response = api_client.get(locations_urls.list())

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 2

        # Check response structure
        area_names = [area["name"] for area in response.data]
        assert dbca_district.name in area_names
        assert dbca_region.name in area_names

    def test_list_areas_empty(self, api_client, user, db):
        """Test listing areas when none exist"""
        api_client.force_authenticate(user=user)

        response = api_client.get(locations_urls.list())

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_create_area_valid_data(self, api_client, user, db):
        """Test creating area with valid data"""
        api_client.force_authenticate(user=user)

        data = {
            "name": "New District",
            "area_type": Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
        }

        response = api_client.post(locations_urls.list(), data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New District"
        assert response.data["area_type"] == "dbcadistrict"

        # Verify area was created in database
        assert Area.objects.filter(name="New District").exists()

    def test_create_area_invalid_data(self, api_client, user, db):
        """Test creating area with invalid data"""
        api_client.force_authenticate(user=user)

        data = {
            "name": "",  # Invalid - empty name
            "area_type": Area.AreaTypeChoices.AREA_TYPE_DBCA_DISTRICT,
        }

        response = api_client.post(locations_urls.list(), data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data

    def test_create_area_missing_fields(self, api_client, user, db):
        """Test creating area with missing required fields"""
        api_client.force_authenticate(user=user)

        data = {
            "name": "Test Area",
            # Missing area_type
        }

        response = api_client.post(locations_urls.list(), data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestAreaDetailView:
    """Tests for AreaDetail get/update/delete view"""

    def test_get_area_detail(self, api_client, user, dbca_district, db):
        """Test getting area detail"""
        api_client.force_authenticate(user=user)

        response = api_client.get(locations_urls.detail(dbca_district.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == dbca_district.id
        assert response.data["name"] == dbca_district.name
        assert response.data["area_type"] == dbca_district.area_type

    def test_get_area_detail_unauthenticated(self, api_client, dbca_district, db):
        """Test getting area detail without authentication"""
        response = api_client.get(locations_urls.detail(dbca_district.id))

        # Returns 403 because of IsAuthenticated permission class
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_get_area_detail_not_found(self, api_client, user, db):
        """Test getting non-existent area"""
        api_client.force_authenticate(user=user)

        response = api_client.get(locations_urls.detail(99999))

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_area(self, api_client, user, dbca_district, db):
        """Test updating area"""
        api_client.force_authenticate(user=user)

        data = {
            "name": "Updated District Name",
        }

        response = api_client.put(
            locations_urls.detail(dbca_district.id), data, format="json"
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data["name"] == "Updated District Name"

        # Verify area was updated in database
        dbca_district.refresh_from_db()
        assert dbca_district.name == "Updated District Name"

    def test_update_area_invalid_data(self, api_client, user, dbca_district, db):
        """Test updating area with invalid data"""
        api_client.force_authenticate(user=user)

        data = {
            "area_type": "invalid_type",
        }

        response = api_client.put(
            locations_urls.detail(dbca_district.id), data, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_area_unauthenticated(self, api_client, dbca_district, db):
        """Test updating area without authentication"""
        data = {"name": "New Name"}

        response = api_client.put(
            locations_urls.detail(dbca_district.id), data, format="json"
        )

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_delete_area(self, api_client, user, dbca_district, db):
        """Test deleting area"""
        api_client.force_authenticate(user=user)

        area_id = dbca_district.id
        response = api_client.delete(locations_urls.detail(area_id))

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify area was deleted from database
        assert not Area.objects.filter(id=area_id).exists()

    def test_delete_area_unauthenticated(self, api_client, dbca_district, db):
        """Test deleting area without authentication"""
        response = api_client.delete(locations_urls.detail(dbca_district.id))

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]


class TestDBCADistrictsView:
    """Tests for DBCADistricts view"""

    def test_list_dbca_districts(
        self, api_client, user, dbca_district, dbca_region, db
    ):
        """Test listing only DBCA districts"""
        api_client.force_authenticate(user=user)

        response = api_client.get(locations_urls.path("dbcadistricts"))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["name"] == dbca_district.name
        assert response.data[0]["area_type"] == "dbcadistrict"

    def test_list_dbca_districts_unauthenticated(self, api_client, db):
        """Test listing DBCA districts without authentication"""
        response = api_client.get(locations_urls.path("dbcadistricts"))

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]


class TestDBCARegionsView:
    """Tests for DBCARegions view"""

    def test_list_dbca_regions(self, api_client, user, dbca_district, dbca_region, db):
        """Test listing only DBCA regions"""
        api_client.force_authenticate(user=user)

        response = api_client.get(locations_urls.path("dbcaregions"))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["name"] == dbca_region.name
        assert response.data[0]["area_type"] == "dbcaregion"

    def test_list_dbca_regions_unauthenticated(self, api_client, db):
        """Test listing DBCA regions without authentication"""
        response = api_client.get(locations_urls.path("dbcaregions"))

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]


class TestImcrasView:
    """Tests for Imcras view"""

    def test_list_imcras(self, api_client, user, db):
        """Test listing IMCRA areas"""
        api_client.force_authenticate(user=user)

        # Create IMCRA area
        imcra = Area.objects.create(
            name="Test IMCRA",
            area_type=Area.AreaTypeChoices.AREA_TYPE_IMCRA_REGION,
        )

        response = api_client.get(locations_urls.path("imcra"))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["name"] == imcra.name
        assert response.data[0]["area_type"] == "imcra"

    def test_list_imcras_unauthenticated(self, api_client, db):
        """Test listing IMCRA areas without authentication"""
        response = api_client.get(locations_urls.path("imcra"))

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]


class TestIbrasView:
    """Tests for Ibras view"""

    def test_list_ibras(self, api_client, user, ibra_region, db):
        """Test listing IBRA areas"""
        api_client.force_authenticate(user=user)

        response = api_client.get(locations_urls.path("ibra"))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["name"] == ibra_region.name
        assert response.data[0]["area_type"] == "ibra"

    def test_list_ibras_unauthenticated(self, api_client, db):
        """Test listing IBRA areas without authentication"""
        response = api_client.get(locations_urls.path("ibra"))

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]


class TestNrmsView:
    """Tests for Nrms view"""

    def test_list_nrms(self, api_client, user, db):
        """Test listing NRM areas"""
        api_client.force_authenticate(user=user)

        # Create NRM area
        nrm = Area.objects.create(
            name="Test NRM",
            area_type=Area.AreaTypeChoices.AREA_TYPE_NRM_REGION,
        )

        response = api_client.get(locations_urls.path("nrm"))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["name"] == nrm.name
        assert response.data[0]["area_type"] == "nrm"

    def test_list_nrms_unauthenticated(self, api_client, db):
        """Test listing NRM areas without authentication"""
        response = api_client.get(locations_urls.path("nrm"))

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]
