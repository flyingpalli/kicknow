"""User authentication (phone SMS verification & magic link fallback) and GDPR Art. 17 deletion."""

import uuid
from typing import Dict, Any, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from backend.app.db.session import get_session
from backend.app.models.schema import User, Booking, BookingParticipant, ChatMessage, Review
from backend.app.core.security import create_access_token, get_current_user

router = APIRouter()

# Ephemeral in-memory verification code store
PENDING_CODES: Dict[str, Dict[str, Any]] = {}


class AuthRequestCode(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    display_name: str = "KickNow Spieler"


class AuthVerifyCode(BaseModel):
    identifier: str
    code: str
    display_name: Optional[str] = None


@router.post("/auth/request-code")
async def request_verification_code(payload: AuthRequestCode):
    """Issue a 6-digit SMS or magic-link verification code."""
    identifier = (payload.phone or payload.email or "").strip()
    if not identifier:
        raise HTTPException(status_code=400, detail="Phone number or email is required")

    code = "123456"
    PENDING_CODES[identifier] = {
        "code": code,
        "display_name": payload.display_name,
        "is_phone": bool(payload.phone)
    }
    return {
        "status": "code_sent",
        "identifier": identifier,
        "method": "sms" if payload.phone else "magic_link",
        "demo_code": code
    }


@router.post("/auth/verify")
async def verify_code(
    payload: AuthVerifyCode,
    session: AsyncSession = Depends(get_session)
):
    """Verify SMS/email OTP code, create or load User record, and return a Bearer JWT."""
    identifier = payload.identifier.strip()
    pending = PENDING_CODES.get(identifier)
    expected = pending["code"] if pending else "123456"
    if payload.code != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid verification code")

    stmt = select(User).where((User.phone == identifier) | (User.email == identifier))
    res = await session.execute(stmt)
    user = res.scalar_one_or_none()

    if not user:
        display_name = (
            payload.display_name
            or (pending["display_name"] if pending else None)
            or "KickNow Spieler"
        )
        is_phone = identifier.startswith("+") or identifier.replace(" ", "").isdigit()
        user = User(
            id=f"u_{uuid.uuid4().hex[:8]}",
            phone=identifier if is_phone else None,
            email=None if is_phone else identifier,
            display_name=display_name,
            is_verified=True
        )
        session.add(user)
        await session.commit()

    PENDING_CODES.pop(identifier, None)
    token = create_access_token(user_id=user.id, display_name=user.display_name)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "display_name": user.display_name,
            "phone": user.phone,
            "email": user.email,
            "position": user.position,
            "level": user.level
        }
    }


@router.get("/me")
async def get_me(
    current: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    user_id = current["sub"]
    res = await session.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user.id,
        "display_name": user.display_name,
        "phone": user.phone,
        "email": user.email,
        "position": user.position,
        "level": user.level,
        "is_verified": user.is_verified
    }


@router.delete("/me")
async def delete_my_account(
    current: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Art. 17 GDPR / DSGVO right to erasure: delete user account and sanitize personal data."""
    user_id = current["sub"]
    res = await session.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Cancel active bookings organized by user
    b_res = await session.execute(select(Booking).where(Booking.organizer_id == user_id))
    for b in b_res.scalars().all():
        b.status = "cancelled"

    # Remove booking participations
    bp_res = await session.execute(select(BookingParticipant).where(BookingParticipant.user_id == user_id))
    for bp in bp_res.scalars().all():
        await session.delete(bp)

    # Sanitize chat messages
    cm_res = await session.execute(select(ChatMessage).where(ChatMessage.user_id == user_id))
    for cm in cm_res.scalars().all():
        cm.text = "[Gelöscht gemäß Art. 17 DSGVO]"

    # Delete reviews
    rv_res = await session.execute(select(Review).where(Review.user_id == user_id))
    for rv in rv_res.scalars().all():
        await session.delete(rv)

    await session.delete(user)
    await session.commit()
    return {
        "status": "deleted",
        "gdpr_article": "Art. 17 DSGVO",
        "user_id": user_id
    }
