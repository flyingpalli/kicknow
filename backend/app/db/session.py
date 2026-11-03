"""Asynchronous database session management and seed initialization."""

import os
import re
import json
import math
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel, select

from backend.app.models.schema import User, Pitch, MatchSchedule

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./kicknow.db"
)

IS_POSTGRES = DATABASE_URL.startswith("postgresql")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Compute great-circle distance in kilometers between two WGS84 points."""
    r = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lng2 - lng1)
    a = math.sin(d_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2.0) ** 2
    return round(2.0 * r * math.asin(math.sqrt(a)), 2)


def slugify(text: str, pid: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return f"{base}-{pid}"


async def init_db(seed: bool = True) -> None:
    """Create tables and optionally seed initial pitches from data/scraped_pitches.json + multi-city."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    if not seed:
        return

    async with async_session_factory() as session:
        existing = await session.execute(select(Pitch).limit(1))
        if existing.scalar_one_or_none() is not None:
            return

        # Seed default demo user
        default_user = User(
            id="u0",
            email="alex@kicknow.app",
            phone="+491701234567",
            display_name="Alex Mayer",
            position="Mittelfeld",
            level="Fortgeschritten",
            is_verified=True
        )
        session.add(default_user)

        # Load Munich pitches from data/scraped_pitches.json if available
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        pitches_path = os.path.join(repo_root, "data", "scraped_pitches.json")
        raw_pitches = []
        if os.path.exists(pitches_path):
            with open(pitches_path, "r", encoding="utf-8") as f:
                raw_pitches = json.load(f)

        # Also include multi-city curated pitches
        try:
            from scraper.osm_importer import get_multi_city_pitches
            from scraper.fussball_de_scraper import scrape_all_cities_matches
            from scraper.matcher import connect_pitches_and_matches
            multi_pitches = get_multi_city_pitches(live_osm=False)
            multi_matches = scrape_all_cities_matches(live=False)
            multi_pitches, _ = connect_pitches_and_matches(multi_pitches, multi_matches, verbose=False)
            raw_pitches.extend(multi_pitches)
        except Exception:
            pass

        seen_ids = set()
        for p in raw_pitches:
            pid = str(p["id"])
            if pid in seen_ids:
                continue
            seen_ids.add(pid)
            size = p.get("size", [105, 68])
            pitch_obj = Pitch(
                id=pid,
                slug=slugify(p.get("name", pid), pid),
                name=p.get("name", "Bolzplatz"),
                city=p.get("city", "München"),
                district=p.get("district", "München"),
                address=p.get("address", ""),
                lat=float(p["lat"]),
                lng=float(p["lng"]),
                geom=f"POINT({p['lng']} {p['lat']})",
                surface=p.get("surface", "Rasenplatz"),
                cage=bool(p.get("cage", False)),
                size_w=int(size[0]) if len(size) > 0 else 105,
                size_h=int(size[1]) if len(size) > 1 else 68,
                max_players=int(p.get("maxPlayers", 22)),
                access_type=p.get("access", "Öffentlich"),
                club=p.get("club"),
                desc=p.get("desc", ""),
                amenities=p.get("amenities", {}),
                is_verified=True
            )
            session.add(pitch_obj)

            for occ in p.get("occupations", []):
                sched_id = occ.get("id") or f"{pid}_{occ['date']}_{occ['slot_idx']}"
                sched = MatchSchedule(
                    id=sched_id,
                    pitch_id=pid,
                    date=occ["date"],
                    slot_idx=int(occ.get("slot_idx", 0)),
                    start_min=int(occ.get("start", 840)),
                    end_min=int(occ.get("end", 930)),
                    home_team=occ.get("home", "Heim"),
                    away_team=occ.get("away", "Gast"),
                    league=occ.get("league", "Kreisliga"),
                    source="bfv"
                )
                session.add(sched)

        await session.commit()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency yielding an AsyncSession."""
    async with async_session_factory() as session:
        yield session
