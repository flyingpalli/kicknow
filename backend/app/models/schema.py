"""Database models for KickNow (PostgreSQL + PostGIS and SQLite test compatibility)."""

from datetime import datetime, timezone
from typing import Optional, Any, Dict, List
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON, String

try:
    from geoalchemy2 import Geometry
except ImportError:
    Geometry = None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    __tablename__ = "users"
    id: str = Field(primary_key=True)
    email: Optional[str] = Field(default=None, unique=True, index=True)
    phone: Optional[str] = Field(default=None, unique=True, index=True)
    display_name: str
    position: str = Field(default="Mittelfeld")
    level: str = Field(default="Fortgeschritten")
    avatar_url: Optional[str] = None
    is_verified: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utc_now)


class Pitch(SQLModel, table=True):
    __tablename__ = "pitches"
    id: str = Field(primary_key=True)
    slug: str = Field(unique=True, index=True)
    name: str
    city: str = Field(default="München", index=True)
    district: Optional[str] = None
    address: str
    lat: float
    lng: float
    geom: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True))
    surface: str
    cage: bool = False
    size_w: int = Field(default=105)
    size_h: int = Field(default=68)
    max_players: int = Field(default=22)
    access_type: str = Field(default="Öffentlich")
    club: Optional[str] = None
    desc: str = Field(default="")
    amenities: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    is_verified: bool = True


class MatchSchedule(SQLModel, table=True):
    __tablename__ = "match_schedules"
    id: str = Field(primary_key=True)
    pitch_id: str = Field(foreign_key="pitches.id", index=True)
    date: str = Field(index=True)
    slot_idx: int = Field(default=0)
    start_min: int
    end_min: int
    home_team: str
    away_team: str
    league: str
    source: str = Field(default="bfv")


class Booking(SQLModel, table=True):
    __tablename__ = "bookings"
    id: str = Field(primary_key=True)
    pitch_id: str = Field(foreign_key="pitches.id", index=True)
    date: str = Field(index=True)
    slot_index: int
    organizer_id: str = Field(foreign_key="users.id")
    group_size: int
    max_players: int
    level: str
    is_open: bool
    status: str = Field(default="active")
    created_at: datetime = Field(default_factory=utc_now)


class BookingParticipant(SQLModel, table=True):
    __tablename__ = "booking_participants"
    id: str = Field(primary_key=True)
    booking_id: str = Field(foreign_key="bookings.id", index=True)
    user_id: str = Field(foreign_key="users.id")
    count: int = 1
    joined_at: datetime = Field(default_factory=utc_now)


class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_messages"
    id: str = Field(primary_key=True)
    booking_id: str = Field(foreign_key="bookings.id", index=True)
    user_id: str = Field(foreign_key="users.id")
    text: str
    is_reported: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utc_now)


class Review(SQLModel, table=True):
    __tablename__ = "reviews"
    id: str = Field(primary_key=True)
    pitch_id: str = Field(foreign_key="pitches.id", index=True)
    user_id: str = Field(foreign_key="users.id")
    stars: int
    text: str = Field(default="")
    tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    is_reported: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utc_now)


class PitchSubmission(SQLModel, table=True):
    __tablename__ = "pitch_submissions"
    id: str = Field(primary_key=True)
    name: str
    city: str = Field(default="München")
    district: str = Field(default="")
    address: str
    lat: float
    lng: float
    surface: str = Field(default="Kunstrasen")
    cage: bool = Field(default=False)
    submitted_by: str = Field(foreign_key="users.id")
    confirmations: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    status: str = Field(default="pending")  # pending | approved | rejected
    created_at: datetime = Field(default_factory=utc_now)
