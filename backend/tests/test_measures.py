"""
Tests for Measure Management API endpoints.
"""
import pytest
from httpx import AsyncClient


class TestMeasureCRUD:
    """Test CRUD operations for measures."""

    @pytest.mark.asyncio
    async def test_create_measure(self, client: AsyncClient, sample_measure_data: dict):
        """Test creating a new measure."""
        response = await client.post("/api/v1/measures/", json=sample_measure_data)
        assert response.status_code == 200

        data = response.json()
        assert data["title"] == sample_measure_data["title"]
        assert data["description"] == sample_measure_data["description"]
        assert data["id"] is not None
        assert data["status"] == "Draft"  # Default status

    @pytest.mark.asyncio
    async def test_list_measures(self, client: AsyncClient, sample_measure_data: dict):
        """Test listing measures."""
        # Create a measure first
        await client.post("/api/v1/measures/", json=sample_measure_data)

        # List measures
        response = await client.get("/api/v1/measures/")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_get_measure(self, client: AsyncClient, sample_measure_data: dict):
        """Test getting a single measure."""
        # Create a measure
        create_response = await client.post("/api/v1/measures/", json=sample_measure_data)
        measure_id = create_response.json()["id"]

        # Get the measure
        response = await client.get(f"/api/v1/measures/{measure_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == measure_id
        assert data["title"] == sample_measure_data["title"]

    @pytest.mark.asyncio
    async def test_get_measure_not_found(self, client: AsyncClient):
        """Test getting a non-existent measure."""
        response = await client.get("/api/v1/measures/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_measure(self, client: AsyncClient, sample_measure_data: dict):
        """Test updating a measure."""
        # Create a measure
        create_response = await client.post("/api/v1/measures/", json=sample_measure_data)
        measure_id = create_response.json()["id"]

        # Update the measure
        update_data = {"title": "Updated Measure Title"}
        response = await client.patch(f"/api/v1/measures/{measure_id}", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["title"] == "Updated Measure Title"

    @pytest.mark.asyncio
    async def test_delete_measure(self, client: AsyncClient, sample_measure_data: dict):
        """Test deleting a measure."""
        # Create a measure
        create_response = await client.post("/api/v1/measures/", json=sample_measure_data)
        measure_id = create_response.json()["id"]

        # Delete the measure
        response = await client.delete(f"/api/v1/measures/{measure_id}")
        assert response.status_code == 200

        # Verify it's deleted
        get_response = await client.get(f"/api/v1/measures/{measure_id}")
        assert get_response.status_code == 404


class TestMeasureStatusTransitions:
    """Test measure status workflow."""

    @pytest.mark.asyncio
    async def test_activate_measure(self, client: AsyncClient, sample_measure_data: dict):
        """Test activating a draft measure."""
        # Create a measure (starts as Draft)
        create_response = await client.post("/api/v1/measures/", json=sample_measure_data)
        measure_id = create_response.json()["id"]

        # Activate it
        response = await client.post(f"/api/v1/measures/{measure_id}/activate")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "Active"

    @pytest.mark.asyncio
    async def test_deactivate_measure(self, client: AsyncClient, sample_measure_data: dict):
        """Test deactivating an active measure."""
        # Create and activate a measure
        create_response = await client.post("/api/v1/measures/", json=sample_measure_data)
        measure_id = create_response.json()["id"]
        await client.post(f"/api/v1/measures/{measure_id}/activate")

        # Deactivate it
        response = await client.post(f"/api/v1/measures/{measure_id}/deactivate")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "Inactive"


class TestMeasureEffectiveness:
    """Test measure effectiveness tracking."""

    @pytest.mark.asyncio
    async def test_update_effectiveness(self, client: AsyncClient, sample_measure_data: dict):
        """Test updating measure effectiveness score."""
        # Create a measure
        create_response = await client.post("/api/v1/measures/", json=sample_measure_data)
        measure_id = create_response.json()["id"]

        # Update effectiveness
        response = await client.patch(
            f"/api/v1/measures/{measure_id}/effectiveness",
            params={"effectiveness_score": 85}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["effectiveness_score"] == 85


class TestMeasureStatistics:
    """Test measure statistics endpoints."""

    @pytest.mark.asyncio
    async def test_get_measures_by_status(self, client: AsyncClient, sample_measure_data: dict):
        """Test getting measure counts by status."""
        # Create a measure
        await client.post("/api/v1/measures/", json=sample_measure_data)

        # Get stats
        response = await client.get("/api/v1/measures/stats/by-status")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)
