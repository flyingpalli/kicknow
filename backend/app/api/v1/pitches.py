"""Spatial pitch endpoints utilizing PostGIS or in-memory Haversine radius queries.

Privacy note (GDPR / DSGVO):
Client lat/lng coordinates are used strictly ephemerally in-memory or in SQL WHERE clauses
for bounding-box and distance sorting. User coordinates are never stored in database tables.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlmodel import select

from backend.app.db.session import get_session, IS_POSTGRES, haversine_km
from backend.app.models.schema import Pitch, MatchSchedule, Booking, BookingParticipant
from scraper.config import CITIES, SLOT_STARTS, SLOT_LEN

router = APIRouter()


@router.get("/cities")
async def list_cities():
    """Return all supported cities with center coordinates and bounding boxes."""
    return {
        key: {
            "key": key,
            "name": cfg["name"],
            "center": {"lat": cfg["center"][0], "lng": cfg["center"][1]},
            "bbox": cfg["bbox"],
            "association": cfg["association"],
        }
        for key, cfg in CITIES.items()
    }


@router.get("/")
async def list_pitches(
    lat: float = Query(default=48.137154),
    lng: float = Query(default=11.576124),
    radius_km: float = Query(default=10.0),
    surface: str = Query(default="alle"),
    city: Optional[str] = Query(default=None),
    session: AsyncSession = Depends(get_session)
):
    """List verified pitches within radius_km of ephemeral (lat, lng), ordered by distance."""
    if IS_POSTGRES:
        try:
            sql = text("""
                SELECT id, name, city, district, address, lat, lng, surface, cage,
                       size_w, size_h, max_players, access_type, club, "desc", amenities,
                       ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography) / 1000.0 AS dist_km
                FROM pitches
                WHERE is_verified = true
                  AND ST_DWithin(geom::geography, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography, :radius_m)
                  AND (:surface = 'alle' OR (:surface = 'Käfig' AND cage = true) OR surface = :surface)
                ORDER BY dist_km ASC
                LIMIT 200
            """)
            res = await session.execute(sql, {
                "lat": lat,
                "lng": lng,
                "radius_m": radius_km * 1000.0,
                "surface": surface
            })
            return [dict(row._mapping) for row in res]
        except Exception:
            pass

    stmt = select(Pitch).where(Pitch.is_verified == True)
    if city:
        stmt = stmt.where(Pitch.city == city)

    result = await session.execute(stmt)
    pitches = result.scalars().all()

    items = []
    for p in pitches:
        if surface != "alle":
            if surface == "Käfig" and not p.cage:
                continue
            elif surface != "Käfig" and p.surface != surface:
                continue
        dist = haversine_km(lat, lng, p.lat, p.lng)
        if dist <= radius_km:
            items.append({
                "id": p.id,
                "slug": p.slug,
                "name": p.name,
                "city": p.city,
                "district": p.district,
                "address": p.address,
                "lat": p.lat,
                "lng": p.lng,
                "surface": p.surface,
                "cage": p.cage,
                "size": [p.size_w, p.size_h],
                "maxPlayers": p.max_players,
                "access": p.access_type,
                "access_type": p.access_type,
                "club": p.club,
                "desc": p.desc,
                "amenities": p.amenities,
                "dist_km": dist
            })

    items.sort(key=lambda x: x["dist_km"])
    return items[:200]


@router.get("/{pitch_id}")
async def get_pitch(pitch_id: str, session: AsyncSession = Depends(get_session)):
    """Get details and scheduled BFV matches for a specific pitch."""
    res = await session.execute(select(Pitch).where(Pitch.id == pitch_id))
    p = res.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Pitch not found")

    sched_res = await session.execute(select(MatchSchedule).where(MatchSchedule.pitch_id == pitch_id))
    schedules = sched_res.scalars().all()

    return {
        "id": p.id,
        "slug": p.slug,
        "name": p.name,
        "city": p.city,
        "district": p.district,
        "address": p.address,
        "lat": p.lat,
        "lng": p.lng,
        "surface": p.surface,
        "cage": p.cage,
        "size": [p.size_w, p.size_h],
        "maxPlayers": p.max_players,
        "access": p.access_type,
        "access_type": p.access_type,
        "club": p.club,
        "desc": p.desc,
        "amenities": p.amenities,
        "occupations": [
            {
                "id": s.id,
                "pitchId": s.pitch_id,
                "date": s.date,
                "slot_idx": s.slot_idx,
                "start": s.start_min,
                "end": s.end_min,
                "type": "busy",
                "label": f"BFV-Spiel: {s.home_team} – {s.away_team} ({s.league})",
                "home": s.home_team,
                "away": s.away_team,
                "league": s.league
            }
            for s in schedules
        ]
    }


@router.get("/{pitch_id}/slots")
async def get_pitch_slots(
    pitch_id: str,
    date: str = Query(...),
    session: AsyncSession = Depends(get_session)
):
    """Return 9 daily 90-minute slots for a pitch on a given YYYY-MM-DD date."""
    res = await session.execute(select(Pitch).where(Pitch.id == pitch_id))
    p = res.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Pitch not found")

    sched_res = await session.execute(
        select(MatchSchedule).where(MatchSchedule.pitch_id == pitch_id, MatchSchedule.date == date)
    )
    occ_by_idx = {s.slot_idx: s for s in sched_res.scalars().all()}

    book_res = await session.execute(
        select(Booking).where(
            Booking.pitch_id == pitch_id,
            Booking.date == date,
            Booking.status == "active"
        )
    )
    book_by_idx = {b.slot_index: b for b in book_res.scalars().all()}

    slots = []
    for idx, start_min in enumerate(SLOT_STARTS):
        slot_id = f"{pitch_id}_{date}_{idx}"
        if idx in occ_by_idx:
            occ = occ_by_idx[idx]
            slots.append({
                "id": slot_id,
                "pitchId": pitch_id,
                "dk": date,
                "idx": idx,
                "start": start_min,
                "end": start_min + SLOT_LEN,
                "type": "busy",
                "label": f"BFV-Spiel: {occ.home_team} – {occ.away_team} ({occ.league})"
            })
        elif idx in book_by_idx:
            b = book_by_idx[idx]
            part_res = await session.execute(
                select(BookingParticipant).where(BookingParticipant.booking_id == b.id)
            )
            parts = part_res.scalars().all()
            joined_count = b.group_size + sum(pt.count for pt in parts if pt.user_id != b.organizer_id)
            slots.append({
                "id": b.id,
                "pitchId": pitch_id,
                "dk": date,
                "idx": idx,
                "start": start_min,
                "end": start_min + SLOT_LEN,
                "type": "game",
                "organizer": b.organizer_id,
                "groupSize": b.group_size,
                "count": joined_count,
                "maxPlayers": b.max_players,
                "free": max(0, b.max_players - joined_count),
                "level": b.level,
                "open": b.is_open
            })
        else:
            slots.append({
                "id": slot_id,
                "pitchId": pitch_id,
                "dk": date,
                "idx": idx,
                "start": start_min,
                "end": start_min + SLOT_LEN,
                "type": "free"
            })
    return slots
