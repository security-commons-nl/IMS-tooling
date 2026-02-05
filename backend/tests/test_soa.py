
import pytest
from httpx import AsyncClient
from sqlmodel import select
from app.models.core_models import (
    Tenant, Scope, Requirement, Measure, Standard, FrameworkType, ScopeType, ApplicabilityStatement
)

@pytest.mark.asyncio
async def test_link_measure_functional(client: AsyncClient, db_session):
    # 1. Setup Data
    tenant = Tenant(name="Test Tenant SOA", slug="test-tenant-soa")
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)

    scope = Scope(
        tenant_id=tenant.id,
        name="Test Scope SOA",
        type=ScopeType.PROCESS,
        owner="Owner"
    )
    db_session.add(scope)

    measure = Measure(
        tenant_id=tenant.id,
        name="Test Measure SOA",
        description="Desc"
    )
    db_session.add(measure)

    standard = Standard(
        name="Test Standard SOA",
        version="1.0",
        type=FrameworkType.BIO
    )
    db_session.add(standard)
    await db_session.commit()
    await db_session.refresh(scope)
    await db_session.refresh(measure)
    await db_session.refresh(standard)

    # Create 50 requirements
    req_ids = []
    for i in range(50):
        req = Requirement(
            code=f"R-SOA-{i}",
            title=f"Req SOA {i}",
            description="Desc",
            standard_id=standard.id
        )
        db_session.add(req)

    await db_session.commit()

    reqs = await db_session.execute(select(Requirement).where(Requirement.standard_id == standard.id))
    req_ids = [r.id for r in reqs.scalars().all()]
    assert len(req_ids) == 50

    # 2. Test Link (Create)
    response = await client.post(
        f"/api/v1/soa/scope/{scope.id}/link-measure/{measure.id}?tenant_id={tenant.id}",
        json=req_ids
    )
    assert response.status_code == 200

    data = response.json()
    assert data["created"] == 50
    assert data["updated"] == 0

    # Verify data exists
    result = await db_session.execute(
        select(ApplicabilityStatement)
        .where(ApplicabilityStatement.scope_id == scope.id)
        .where(ApplicabilityStatement.requirement_id.in_(req_ids))
    )
    soas = result.scalars().all()
    assert len(soas) == 50

    # 3. Test Link (Update)
    response = await client.post(
        f"/api/v1/soa/scope/{scope.id}/link-measure/{measure.id}?tenant_id={tenant.id}",
        json=req_ids
    )
    assert response.status_code == 200

    data = response.json()
    assert data["created"] == 0
    assert data["updated"] == 50
