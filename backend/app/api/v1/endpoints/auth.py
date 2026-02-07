from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.db import get_session
from app.core.security import verify_password, get_password_hash
from app.core.crud import CRUDBase
from app.core.rbac import require_admin, get_user_roles
from app.models.core_models import User, UserRead, UserScopeRole, Role

router = APIRouter()
crud_user = CRUDBase(User)
limiter = Limiter(key_func=get_remote_address)


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    """Admin changes another user's password."""
    user_id: int
    new_password: str


class ResetMyPasswordRequest(BaseModel):
    """User changes own password."""
    old_password: str
    new_password: str


@router.post("/login")
@limiter.limit("5/minute")
async def login(
    request: Request,
    credentials: LoginRequest,
    session: AsyncSession = Depends(get_session),
):
    """Validate credentials against database and return user data + roles/permissions."""
    user = await crud_user.get_by_field(session, "username", credentials.username)
    if not user:
        raise HTTPException(status_code=401, detail="Ongeldige gebruikersnaam of wachtwoord")

    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account is gedeactiveerd")

    if not user.password_hash:
        raise HTTPException(status_code=401, detail="Geen wachtwoord ingesteld voor dit account")

    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Ongeldige gebruikersnaam of wachtwoord")

    # Update last_login
    user.last_login = datetime.utcnow()
    session.add(user)
    await session.commit()
    await session.refresh(user)

    # Fetch user roles across all scopes
    roles = await get_user_roles(user, session)
    role_names = sorted({r.value for r in roles})

    # Build permissions map
    is_admin = user.is_superuser or Role.BEHEERDER in roles
    permissions = {
        "is_admin": is_admin,
        "can_edit": is_admin or bool(roles.intersection({
            Role.COORDINATOR, Role.EIGENAAR, Role.MEDEWERKER,
        })),
        "can_configure": is_admin or bool(roles.intersection({
            Role.COORDINATOR, Role.EIGENAAR,
        })),
        "can_manage_users": is_admin or Role.COORDINATOR in roles,
        "can_write_findings": is_admin or bool(roles.intersection({
            Role.COORDINATOR, Role.TOEZICHTHOUDER,
        })),
    }

    # Return user data + RBAC info (no response_model restriction)
    user_data = UserRead.model_validate(user).model_dump()
    user_data["global_roles"] = role_names
    user_data["permissions"] = permissions

    return user_data


@router.post("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """Admin changes another user's password. Requires Beheerder role."""
    target = await crud_user.get_or_404(session, req.user_id)

    if len(req.new_password) < 8:
        raise HTTPException(status_code=400, detail="Wachtwoord moet minimaal 8 tekens zijn")

    target.password_hash = get_password_hash(req.new_password)
    session.add(target)
    await session.commit()

    return {"message": f"Wachtwoord van {target.username} is gewijzigd"}


@router.post("/reset-my-password")
async def reset_my_password(
    req: ResetMyPasswordRequest,
    user_id: int = 0,
    session: AsyncSession = Depends(get_session),
):
    """User changes own password (verifies old password first)."""
    if not user_id:
        raise HTTPException(status_code=400, detail="Gebruiker-ID is verplicht")

    user = await crud_user.get_or_404(session, user_id)

    if not user.password_hash or not verify_password(req.old_password, user.password_hash):
        raise HTTPException(status_code=401, detail="Huidig wachtwoord is onjuist")

    if len(req.new_password) < 8:
        raise HTTPException(status_code=400, detail="Wachtwoord moet minimaal 8 tekens zijn")

    user.password_hash = get_password_hash(req.new_password)
    session.add(user)
    await session.commit()

    return {"message": "Wachtwoord is gewijzigd"}
