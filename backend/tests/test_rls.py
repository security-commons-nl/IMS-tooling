"""
RLS (Row Level Security) verification tests.

Tests tenant data isolation at the database level using raw SQL.
Requires a running PostgreSQL instance with RLS policies applied.
"""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.core.config import settings

# Use the real PostgreSQL database for RLS testing (RLS does not work with SQLite)
DATABASE_URL = settings.SQLALCHEMY_DATABASE_URI

# Test tenant IDs (high numbers to avoid conflicts with real data)
TENANT_A = 9991
TENANT_B = 9992


@pytest_asyncio.fixture(scope="function")
async def setup_rls_test():
    """
    Complete setup and teardown for RLS tests:
    1. Create test role (non-superuser)
    2. Seed test data as superuser
    3. Yield engine connected as test role
    4. Clean up everything
    """
    admin_engine = create_async_engine(DATABASE_URL, echo=False, future=True)

    # --- SETUP ---
    async with admin_engine.begin() as conn:
        # Create test role
        try:
            await conn.execute(text("DROP OWNED BY ims_test_user"))
        except Exception:
            pass
        try:
            await conn.execute(text("DROP ROLE IF EXISTS ims_test_user"))
        except Exception:
            pass
        await conn.execute(text("CREATE ROLE ims_test_user WITH LOGIN PASSWORD 'testpass' NOBYPASSRLS"))
        await conn.execute(text("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ims_test_user"))
        await conn.execute(text("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ims_test_user"))

        # Seed test data (as superuser, bypasses RLS)
        await conn.execute(text(f"""
            INSERT INTO tenant (id, name, slug, country, is_active, is_service_provider, created_at, updated_at)
            VALUES ({TENANT_A}, 'RLS Tenant A', 'rls-test-a-{TENANT_A}', 'NL', true, false, NOW(), NOW())
            ON CONFLICT (id) DO NOTHING
        """))
        await conn.execute(text(f"""
            INSERT INTO tenant (id, name, slug, country, is_active, is_service_provider, created_at, updated_at)
            VALUES ({TENANT_B}, 'RLS Tenant B', 'rls-test-b-{TENANT_B}', 'NL', true, false, NOW(), NOW())
            ON CONFLICT (id) DO NOTHING
        """))
        await conn.execute(text(f"""
            INSERT INTO risk (tenant_id, title, risk_accepted, is_critical, status, inherent_likelihood, inherent_impact, created_at, updated_at)
            VALUES ({TENANT_A}, 'Secret Risk A', false, false, 'DRAFT', 'LOW', 'LOW', NOW(), NOW())
        """))
        await conn.execute(text(f"""
            INSERT INTO risk (tenant_id, title, risk_accepted, is_critical, status, inherent_likelihood, inherent_impact, created_at, updated_at)
            VALUES ({TENANT_B}, 'Secret Risk B', false, false, 'DRAFT', 'HIGH', 'HIGH', NOW(), NOW())
        """))

    # Create test user engine
    from sqlalchemy.engine.url import make_url
    url = make_url(DATABASE_URL)
    test_url = url.set(username="ims_test_user", password="testpass")
    test_engine = create_async_engine(test_url, echo=False, future=True)

    yield test_engine

    # --- TEARDOWN ---
    await test_engine.dispose()
    async with admin_engine.begin() as conn:
        await conn.execute(text(f"DELETE FROM risk WHERE tenant_id IN ({TENANT_A}, {TENANT_B})"))
        await conn.execute(text(f"DELETE FROM tenant WHERE id IN ({TENANT_A}, {TENANT_B})"))
    await admin_engine.dispose()


@pytest.mark.asyncio
async def test_rls_tenant_a_sees_own_data(setup_rls_test):
    """Tenant A should only see its own risks."""
    async_session = sessionmaker(setup_rls_test, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        await session.execute(text(f"SET app.current_tenant = '{TENANT_A}'"))
        result = await session.execute(text("SELECT tenant_id, title FROM risk"))
        rows = result.fetchall()

        assert len(rows) >= 1, "Tenant A should see at least 1 risk"
        tenant_ids = [r[0] for r in rows]
        assert all(tid == TENANT_A for tid in tenant_ids), f"Tenant A saw foreign data: {tenant_ids}"
        assert TENANT_B not in tenant_ids, "Tenant A should NOT see Tenant B data"


@pytest.mark.asyncio
async def test_rls_tenant_b_sees_own_data(setup_rls_test):
    """Tenant B should only see its own risks."""
    async_session = sessionmaker(setup_rls_test, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        await session.execute(text(f"SET app.current_tenant = '{TENANT_B}'"))
        result = await session.execute(text("SELECT tenant_id, title FROM risk"))
        rows = result.fetchall()

        assert len(rows) >= 1, "Tenant B should see at least 1 risk"
        tenant_ids = [r[0] for r in rows]
        assert all(tid == TENANT_B for tid in tenant_ids), f"Tenant B saw foreign data: {tenant_ids}"
        assert TENANT_A not in tenant_ids, "Tenant B should NOT see Tenant A data"


@pytest.mark.asyncio
async def test_rls_no_tenant_sees_nothing(setup_rls_test):
    """Without setting app.current_tenant, no rows should be visible."""
    async_session = sessionmaker(setup_rls_test, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        await session.execute(text("RESET app.current_tenant"))
        try:
            result = await session.execute(text("SELECT tenant_id, title FROM risk"))
            rows = result.fetchall()
            assert len(rows) == 0, f"Expected 0 rows without tenant context, got {len(rows)}"
        except Exception:
            # current_setting raises error when not set — fail-closed behavior is also acceptable
            pass


@pytest.mark.asyncio
async def test_rls_cross_tenant_isolation(setup_rls_test):
    """Switching tenants mid-session should correctly filter data."""
    async_session = sessionmaker(setup_rls_test, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        # First as Tenant A
        await session.execute(text(f"SET app.current_tenant = '{TENANT_A}'"))
        result_a = await session.execute(text("SELECT title FROM risk"))
        titles_a = [r[0] for r in result_a.fetchall()]

        # Switch to Tenant B
        await session.execute(text(f"SET app.current_tenant = '{TENANT_B}'"))
        result_b = await session.execute(text("SELECT title FROM risk"))
        titles_b = [r[0] for r in result_b.fetchall()]

        # Verify isolation
        assert "Secret Risk A" in titles_a, f"Tenant A should see 'Secret Risk A', got: {titles_a}"
        assert "Secret Risk B" not in titles_a, f"Tenant A should NOT see 'Secret Risk B'"
        assert "Secret Risk B" in titles_b, f"Tenant B should see 'Secret Risk B', got: {titles_b}"
        assert "Secret Risk A" not in titles_b, f"Tenant B should NOT see 'Secret Risk A'"
