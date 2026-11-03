"""Booking and open match participation endpoints.

Strictly informational and matchmaking for open sessions (no payment processing).
Includes concurrency lock prevention, token-bucket rate limiting, and WebSocket broadcasts.
"""

import uuid
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from backend.app.db.session import get_session
from backend.app.models.schema import Booking, BookingParticipant, MatchSchedule, Pitch, ChatMessage
from backend.app.core.security import get_current_user, booking_rate_limiter, ws_hub

router = APIRouter()


class BookingCreateRequest(BaseModel):
    pitch_id: str
    date: str
    slot_index: int = Field(ge=0, le=8)
    group_size: int = Field(default=4, ge=1, le=22)
    max_players: int = Field(default=10, ge=2, le=22)
    level: str = Field(default="Locker")
    is_open: bool = Field(default=True)
    note: Optional[str] = Field(default=None)


class JoinBookingRequest(BaseModel):
    count: int = Field(default=1, ge=1, le=6)
    message: Optional[str] = Field(default=None)


@router.get("/")
async def list_bookings(
    pitch_id: Optional[str] = None,
    date: Optional[str] = None,
    session: AsyncSession = Depends(get_session)
):
    stmt = select(Booking).where(Booking.status == "active")
    if pitch_id:
        stmt = stmt.where(Booking.pitch_id == pitch_id)
    if date:
        stmt = stmt.where(Booking.date == date)
    res = await session.execute(stmt)
    bookings = res.scalars().all()
    out = []
    for b in bookings:
        p_res = await session.execute(
            select(BookingParticipant).where(BookingParticipant.booking_id == b.id)
        )
        parts = p_res.scalars().all()
        extra_joined = sum(pt.count for pt in parts if pt.user_id != b.organizer_id)
        total = b.group_size + extra_joined
        out.append({
            "id": b.id,
            "pitch_id": b.pitch_id,
            "date": b.date,
            "slot_index": b.slot_index,
            "organizer_id": b.organizer_id,
            "group_size": b.group_size,
            "max_players": b.max_players,
            "current_players": total,
            "free_spots": max(0, b.max_players - total),
            "level": b.level,
            "is_open": b.is_open,
            "status": b.status,
            "participants": [{"user_id": pt.user_id, "count": pt.count} for pt in parts]
        })
    return out


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_booking(
    payload: BookingCreateRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    user_id = user["sub"]
    booking_rate_limiter.check_or_raise(f"booking:{user_id}")

    # Verify pitch exists
    pitch_res = await session.execute(select(Pitch).where(Pitch.id == payload.pitch_id))
    if not pitch_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Pitch not found")

    # Concurrency & conflict check: check official BFV schedule
    sched_res = await session.execute(
        select(MatchSchedule).where(
            MatchSchedule.pitch_id == payload.pitch_id,
            MatchSchedule.date == payload.date,
            MatchSchedule.slot_idx == payload.slot_index
        )
    )
    if sched_res.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Slot is occupied by an official league match")

    # Concurrency & conflict check: check existing active booking for this pitch/date/slot
    existing_res = await session.execute(
        select(Booking).where(
            Booking.pitch_id == payload.pitch_id,
            Booking.date == payload.date,
            Booking.slot_index == payload.slot_index,
            Booking.status == "active"
        )
    )
    if existing_res.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Slot is already booked")

    booking_id = f"{payload.pitch_id}_{payload.date}_{payload.slot_index}"
    # Handle case where cancelled booking with same id exists
    old_res = await session.execute(select(Booking).where(Booking.id == booking_id))
    old_booking = old_res.scalar_one_or_none()
    if old_booking:
        booking_id = f"{booking_id}_{uuid.uuid4().hex[:6]}"

    max_pl = max(payload.group_size, payload.max_players) if payload.is_open else payload.group_size
    new_booking = Booking(
        id=booking_id,
        pitch_id=payload.pitch_id,
        date=payload.date,
        slot_index=payload.slot_index,
        organizer_id=user_id,
        group_size=payload.group_size,
        max_players=max_pl,
        level=payload.level,
        is_open=payload.is_open,
        status="active"
    )
    session.add(new_booking)

    org_part = BookingParticipant(
        id=f"bp_{uuid.uuid4().hex[:10]}",
        booking_id=booking_id,
        user_id=user_id,
        count=payload.group_size
    )
    session.add(org_part)

    if payload.note and payload.note.strip():
        msg = ChatMessage(
            id=f"msg_{uuid.uuid4().hex[:10]}",
            booking_id=booking_id,
            user_id=user_id,
            text=payload.note.strip()
        )
        session.add(msg)

    await session.commit()

    event = {
        "event": "slot_booked",
        "booking_id": booking_id,
        "pitch_id": payload.pitch_id,
        "date": payload.date,
        "slot_index": payload.slot_index,
        "organizer_id": user_id
    }
    await ws_hub.broadcast("global", event)
    await ws_hub.broadcast(booking_id, event)

    return {
        "id": new_booking.id,
        "pitch_id": new_booking.pitch_id,
        "date": new_booking.date,
        "slot_index": new_booking.slot_index,
        "organizer_id": new_booking.organizer_id,
        "group_size": new_booking.group_size,
        "max_players": new_booking.max_players,
        "level": new_booking.level,
        "is_open": new_booking.is_open,
        "status": new_booking.status
    }


@router.post("/{booking_id}/join")
async def join_booking(
    booking_id: str,
    payload: JoinBookingRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    user_id = user["sub"]
    res = await session.execute(select(Booking).where(Booking.id == booking_id, Booking.status == "active"))
    booking = res.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if not booking.is_open:
        raise HTTPException(status_code=400, detail="Booking is private")

    p_res = await session.execute(
        select(BookingParticipant).where(BookingParticipant.booking_id == booking_id)
    )
    parts = p_res.scalars().all()
    if any(pt.user_id == user_id for pt in parts):
        raise HTTPException(status_code=409, detail="Already joined this match")

    current_count = booking.group_size + sum(pt.count for pt in parts if pt.user_id != booking.organizer_id)
    if current_count + payload.count > booking.max_players:
        raise HTTPException(status_code=409, detail="Not enough free spots in this match")

    new_part = BookingParticipant(
        id=f"bp_{uuid.uuid4().hex[:10]}",
        booking_id=booking_id,
        user_id=user_id,
        count=payload.count
    )
    session.add(new_part)

    if payload.message and payload.message.strip():
        session.add(ChatMessage(
            id=f"msg_{uuid.uuid4().hex[:10]}",
            booking_id=booking_id,
            user_id=user_id,
            text=payload.message.strip()
        ))

    await session.commit()

    await ws_hub.broadcast(booking_id, {
        "event": "player_joined",
        "booking_id": booking_id,
        "user_id": user_id,
        "count": payload.count
    })

    return {
        "status": "joined",
        "booking_id": booking_id,
        "user_id": user_id,
        "count": payload.count,
        "current_players": current_count + payload.count
    }


@router.delete("/{booking_id}")
async def cancel_or_leave_booking(
    booking_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    user_id = user["sub"]
    res = await session.execute(select(Booking).where(Booking.id == booking_id, Booking.status == "active"))
    booking = res.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.organizer_id == user_id:
        booking.status = "cancelled"
        await session.commit()
        await ws_hub.broadcast("global", {"event": "booking_cancelled", "booking_id": booking_id})
        return {"status": "cancelled", "booking_id": booking_id}

    p_res = await session.execute(
        select(BookingParticipant).where(
            BookingParticipant.booking_id == booking_id,
            BookingParticipant.user_id == user_id
        )
    )
    part = p_res.scalar_one_or_none()
    if not part:
        raise HTTPException(status_code=404, detail="Not a participant of this booking")

    await session.delete(part)
    await session.commit()
    return {"status": "left", "booking_id": booking_id}
