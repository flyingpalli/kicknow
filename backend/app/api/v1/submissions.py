"""Community pitch submission moderation queue.

Newly submitted public mini-pitches or cages require confirmation by two distinct users
or admin approval before becoming verified and visible on the map.
"""

import uuid
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from backend.app.db.session import get_session, slugify
from backend.app.models.schema import PitchSubmission, Pitch
from backend.app.core.security import get_current_user

router = APIRouter()


class SubmissionCreateRequest(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    city: str = Field(default="München")
    district: str = Field(default="Stadtgebiet")
    address: str = Field(min_length=4, max_length=200)
    lat: float = Field(ge=47.0, le=55.5)
    lng: float = Field(ge=5.5, le=15.5)
    surface: str = Field(default="Kunstrasen")
    cage: bool = Field(default=False)


async def _promote_submission_to_pitch(sub: PitchSubmission, session: AsyncSession) -> Pitch:
    pitch_id = f"comm_{sub.id}"
    existing = await session.execute(select(Pitch).where(Pitch.id == pitch_id))
    p = existing.scalar_one_or_none()
    if p:
        return p

    new_pitch = Pitch(
        id=pitch_id,
        slug=slugify(sub.name, pitch_id),
        name=sub.name,
        city=sub.city,
        district=sub.district,
        address=sub.address,
        lat=sub.lat,
        lng=sub.lng,
        geom=f"POINT({sub.lng} {sub.lat})",
        surface=sub.surface,
        cage=sub.cage,
        size_w=32 if sub.cage else 50,
        size_h=18 if sub.cage else 32,
        max_players=10 if sub.cage else 14,
        access_type="Öffentlich",
        club=None,
        desc=f"Von der KickNow-Community gemeldeter und bestätigter Bolzplatz in {sub.city}.",
        amenities={"flutlicht": False, "umkleide": False, "toiletten": False},
        is_verified=True
    )
    session.add(new_pitch)
    return new_pitch


@router.get("/")
async def list_submissions(
    status_filter: Optional[str] = None,
    session: AsyncSession = Depends(get_session)
):
    stmt = select(PitchSubmission)
    if status_filter:
        stmt = stmt.where(PitchSubmission.status == status_filter)
    res = await session.execute(stmt.order_by(PitchSubmission.created_at.desc()))
    subs = res.scalars().all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "city": s.city,
            "district": s.district,
            "address": s.address,
            "lat": s.lat,
            "lng": s.lng,
            "surface": s.surface,
            "cage": s.cage,
            "submitted_by": s.submitted_by,
            "confirmations": s.confirmations,
            "confirmation_count": len(s.confirmations or []),
            "status": s.status
        }
        for s in subs
    ]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_submission(
    payload: SubmissionCreateRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    sub = PitchSubmission(
        id=f"sub_{uuid.uuid4().hex[:8]}",
        name=payload.name.strip(),
        city=payload.city.strip(),
        district=payload.district.strip(),
        address=payload.address.strip(),
        lat=payload.lat,
        lng=payload.lng,
        surface=payload.surface,
        cage=payload.cage,
        submitted_by=user["sub"],
        confirmations=[],
        status="pending"
    )
    session.add(sub)
    await session.commit()
    return {
        "id": sub.id,
        "name": sub.name,
        "city": sub.city,
        "status": sub.status,
        "confirmation_count": 0
    }


@router.post("/{submission_id}/confirm")
async def confirm_submission(
    submission_id: str,
    admin_override: bool = False,
    user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Confirm a pending pitch submission. Auto-approves once 2 distinct users confirm or on admin override."""
    user_id = user["sub"]
    res = await session.execute(select(PitchSubmission).where(PitchSubmission.id == submission_id))
    sub = res.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    if sub.submitted_by == user_id and not admin_override:
        raise HTTPException(status_code=400, detail="Submitter cannot self-confirm without admin override")

    confs = list(sub.confirmations or [])
    if user_id not in confs:
        confs.append(user_id)
    sub.confirmations = confs

    promoted_pitch_id = None
    if len(confs) >= 2 or admin_override:
        sub.status = "approved"
        pitch = await _promote_submission_to_pitch(sub, session)
        promoted_pitch_id = pitch.id

    await session.commit()
    return {
        "id": sub.id,
        "status": sub.status,
        "confirmation_count": len(confs),
        "promoted_pitch_id": promoted_pitch_id
    }
