"""Pitch reviews and moderation reporting endpoints."""

import uuid
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from backend.app.db.session import get_session
from backend.app.models.schema import Review, Pitch
from backend.app.core.security import get_current_user

router = APIRouter()


class ReviewCreateRequest(BaseModel):
    stars: int = Field(ge=1, le=5)
    text: str = Field(default="", max_length=1000)
    tags: List[str] = Field(default_factory=list)


@router.get("/{pitch_id}")
async def list_reviews(pitch_id: str, session: AsyncSession = Depends(get_session)):
    res = await session.execute(
        select(Review)
        .where(Review.pitch_id == pitch_id, Review.is_reported == False)
        .order_by(Review.created_at.desc())
    )
    reviews = res.scalars().all()
    dist = [0, 0, 0, 0, 0]
    for r in reviews:
        if 1 <= r.stars <= 5:
            dist[r.stars - 1] += 1
    count = len(reviews)
    avg = round(sum(r.stars for r in reviews) / count, 2) if count else 0.0
    return {
        "pitch_id": pitch_id,
        "count": count,
        "avg": avg,
        "dist": dist,
        "reviews": [
            {
                "id": r.id,
                "pitch_id": r.pitch_id,
                "user_id": r.user_id,
                "stars": r.stars,
                "text": r.text,
                "tags": r.tags,
                "created_at": r.created_at.isoformat()
            }
            for r in reviews
        ]
    }


@router.post("/{pitch_id}", status_code=status.HTTP_201_CREATED)
async def create_review(
    pitch_id: str,
    payload: ReviewCreateRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    p_res = await session.execute(select(Pitch).where(Pitch.id == pitch_id))
    if not p_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Pitch not found")

    rv = Review(
        id=f"rv_{uuid.uuid4().hex[:10]}",
        pitch_id=pitch_id,
        user_id=user["sub"],
        stars=payload.stars,
        text=payload.text.strip(),
        tags=payload.tags
    )
    session.add(rv)
    await session.commit()
    return {
        "id": rv.id,
        "pitch_id": rv.pitch_id,
        "user_id": rv.user_id,
        "stars": rv.stars,
        "text": rv.text,
        "tags": rv.tags,
        "created_at": rv.created_at.isoformat()
    }


@router.post("/items/{review_id}/report")
async def report_review(
    review_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    res = await session.execute(select(Review).where(Review.id == review_id))
    rv = res.scalar_one_or_none()
    if not rv:
        raise HTTPException(status_code=404, detail="Review not found")
    rv.is_reported = True
    await session.commit()
    return {"status": "reported", "review_id": review_id}
