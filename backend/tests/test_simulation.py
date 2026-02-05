import pytest
from httpx import AsyncClient
from app.models.core_models import RiskQuantificationProfile, Risk, RiskLevel

@pytest.mark.asyncio
async def test_get_default_config(client: AsyncClient):
    """Test getting default configuration."""
    response = await client.get("/api/v1/simulation/config", params={"tenant_id": 1})
    assert response.status_code == 200
    data = response.json()
    assert data["tenant_id"] == 1
    assert "LOW" in data["global_config"]
    assert data["currency"] == "EUR"

@pytest.mark.asyncio
async def test_save_config(client: AsyncClient):
    """Test saving configuration."""
    # First create
    config_data = {
        "tenant_id": 1,
        "global_config": '{"LOW": {"freq_min": 0.1, "freq_max": 0.2, "impact_min": 100, "impact_max": 200}}',
        "currency": "USD",
        "iterations": 500
    }
    response = await client.post("/api/v1/simulation/config", json=config_data)
    assert response.status_code == 200
    data = response.json()
    assert data["currency"] == "USD"
    assert data["iterations"] == 500

    # Verify persistence
    response = await client.get("/api/v1/simulation/config", params={"tenant_id": 1})
    assert response.status_code == 200
    data = response.json()
    assert data["currency"] == "USD"

@pytest.mark.asyncio
async def test_run_simulation(client: AsyncClient, db_session):
    """Test running simulation."""
    # Create a risk first
    # Using raw SQL or session to bypass API for speed/directness?
    # API is safer given existing fixtures might set up things.
    # But db_session fixture is available.

    risk = Risk(
        tenant_id=1,
        title="Sim Risk",
        description="Test",
        inherent_likelihood=RiskLevel.HIGH,
        inherent_impact=RiskLevel.CRITICAL
    )
    db_session.add(risk)
    await db_session.commit()

    # Run simulation
    response = await client.post("/api/v1/simulation/run", params={"tenant_id": 1, "iterations": 100})
    assert response.status_code == 200
    data = response.json()

    assert data["risk_count"] == 1
    assert data["total_iterations"] == 100
    assert "histogram" in data
    assert "mean_loss" in data
    assert data["mean_loss"] > 0 # Should be non-zero for High/Critical
