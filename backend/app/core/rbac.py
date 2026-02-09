"""
RBAC (Role-Based Access Control) dependencies for FastAPI endpoints.

Usage:
    from app.core.rbac import require_editor, require_admin, get_tenant_id, get_scope_access

    @router.get("/")
    async def list_items(
        tenant_id: int = Depends(get_tenant_id),
        accessible_scopes: set[int] | None = Depends(get_scope_access),
        session: AsyncSession = Depends(get_session),
    ):
"""
import logging
from collections import defaultdict
from typing import Optional, Set

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.db import get_session
from app.models.core_models import User, UserScopeRole, Role, TenantUser, Scope

logger = logging.getLogger(__name__)


async def get_current_user(
    x_user_id: int = Header(..., alias="X-User-ID"),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Extract user from X-User-ID header."""
    result = await session.execute(select(User).where(User.id == x_user_id))
    user = result.scalars().first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Gebruiker niet gevonden of inactief")
    return user


async def get_user_roles(
    user: User,
    session: AsyncSession,
    tenant_id: int | None = None,
) -> Set[Role]:
    """Get all distinct roles for a user across their scope assignments."""
    query = select(UserScopeRole.role).where(UserScopeRole.user_id == user.id)
    if tenant_id:
        query = query.where(UserScopeRole.tenant_id == tenant_id)
    result = await session.execute(query)
    return set(result.scalars().all())


# ---------------------------------------------------------------------------
# Tenant isolation dependency
# ---------------------------------------------------------------------------

async def get_tenant_id(
    x_tenant_id: Optional[int] = Header(None, alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> int:
    """Resolve and validate tenant_id from X-Tenant-ID header.

    - If header is present: validates user is a member of that tenant.
    - If header is absent: falls back to user's default tenant (deprecation warning).
    - Superusers bypass the membership check.
    """
    if x_tenant_id is not None:
        # Validate membership (superusers bypass)
        if not current_user.is_superuser:
            result = await session.execute(
                select(TenantUser.id).where(
                    TenantUser.user_id == current_user.id,
                    TenantUser.tenant_id == x_tenant_id,
                    TenantUser.is_active == True,
                )
            )
            if not result.scalars().first():
                raise HTTPException(
                    status_code=403,
                    detail="Geen toegang tot deze tenant",
                )
        return x_tenant_id

    # Fallback: resolve default tenant from memberships
    logger.warning(
        "X-Tenant-ID header missing for user %s — using default tenant (deprecated)",
        current_user.id,
    )
    result = await session.execute(
        select(TenantUser.tenant_id).where(
            TenantUser.user_id == current_user.id,
            TenantUser.is_active == True,
        ).order_by(TenantUser.is_default.desc(), TenantUser.id.asc()).limit(1)
    )
    default_tid = result.scalars().first()
    if not default_tid:
        raise HTTPException(
            status_code=403,
            detail="Gebruiker heeft geen tenant-lidmaatschap",
        )
    return default_tid


# ---------------------------------------------------------------------------
# Scope access dependency (hierarchical cascade)
# ---------------------------------------------------------------------------

async def _get_user_accessible_scope_ids(
    user_id: int,
    tenant_id: int,
    session: AsyncSession,
) -> set[int]:
    """Get all scope_ids a user can access via their UserScopeRole assignments.

    Cascades downward: a role on a parent scope grants access to all children.
    O(n) in-memory walk — no recursive CTE needed for typical scope trees (<100 nodes).
    """
    # Step 1: Get directly assigned scope_ids
    result = await session.execute(
        select(UserScopeRole.scope_id).where(
            UserScopeRole.user_id == user_id,
            UserScopeRole.tenant_id == tenant_id,
            UserScopeRole.scope_id.isnot(None),
        )
    )
    direct_scope_ids = set(result.scalars().all())

    if not direct_scope_ids:
        return set()

    # Step 2: Load all scopes in the tenant (typically <100)
    result = await session.execute(
        select(Scope.id, Scope.parent_id).where(
            Scope.tenant_id == tenant_id,
            Scope.is_active == True,
        )
    )
    all_scopes = result.all()

    # Step 3: Build parent → children map
    children_map: dict[int, list[int]] = defaultdict(list)
    for scope_id, parent_id in all_scopes:
        if parent_id is not None:
            children_map[parent_id].append(scope_id)

    # Step 4: Walk down from each assigned scope to collect all children
    accessible = set(direct_scope_ids)
    stack = list(direct_scope_ids)
    while stack:
        current = stack.pop()
        for child_id in children_map.get(current, []):
            if child_id not in accessible:
                accessible.add(child_id)
                stack.append(child_id)

    return accessible


async def get_scope_access(
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
) -> set[int] | None:
    """Get set of accessible scope_ids for the current user, or None for unrestricted.

    Returns None (= no restriction) for:
    - Superusers
    - Users with BEHEERDER or COORDINATOR role in the tenant

    Returns set[int] for regular users (may be empty if no scope assignments).
    """
    # Superusers see everything
    if current_user.is_superuser:
        return None

    # Check for admin/coordinator roles
    roles = await get_user_roles(current_user, session, tenant_id=tenant_id)
    if roles.intersection({Role.BEHEERDER, Role.COORDINATOR}):
        return None

    # Regular user: compute accessible scopes via hierarchy walk
    return await _get_user_accessible_scope_ids(
        current_user.id, tenant_id, session,
    )


# ---------------------------------------------------------------------------
# Role guards
# ---------------------------------------------------------------------------

def require_role(*allowed_roles: Role):
    """Factory that returns a FastAPI dependency enforcing role membership.

    Superusers bypass the check.
    """
    async def _guard(
        x_user_id: int = Header(..., alias="X-User-ID"),
        x_tenant_id: int | None = Header(None, alias="X-Tenant-ID"),
        session: AsyncSession = Depends(get_session),
    ) -> User:
        result = await session.execute(select(User).where(User.id == x_user_id))
        user = result.scalars().first()
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Gebruiker niet gevonden of inactief")

        # Superuser bypass
        if user.is_superuser:
            return user

        roles = await get_user_roles(user, session, tenant_id=x_tenant_id)
        if not roles.intersection(set(allowed_roles)):
            raise HTTPException(
                status_code=403,
                detail="Onvoldoende rechten voor deze actie",
            )
        return user

    return _guard


# ---------------------------------------------------------------------------
# Convenience shortcuts
# ---------------------------------------------------------------------------

require_admin = require_role(Role.BEHEERDER)
require_coordinator_or_admin = require_role(Role.BEHEERDER, Role.COORDINATOR)
require_editor = require_role(Role.BEHEERDER, Role.COORDINATOR, Role.EIGENAAR, Role.MEDEWERKER)
require_configurer = require_role(Role.BEHEERDER, Role.COORDINATOR, Role.EIGENAAR)
require_oversight = require_role(Role.BEHEERDER, Role.COORDINATOR, Role.TOEZICHTHOUDER)
