"""
RBAC (Role-Based Access Control) dependencies for FastAPI endpoints.

Usage:
    from app.core.rbac import require_editor, require_admin

    @router.post("/")
    async def create_item(
        ...,
        current_user: User = Depends(require_editor),
    ):
"""
from typing import Set

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.db import get_session
from app.models.core_models import User, UserScopeRole, Role


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
