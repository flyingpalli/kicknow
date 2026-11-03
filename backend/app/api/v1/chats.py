"""Real-time match chats, rate limiting, content reporting, and WebSocket communication."""

import uuid
from typing import Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from backend.app.db.session import get_session
from backend.app.models.schema import ChatMessage, Booking
from backend.app.core.security import get_current_user, chat_rate_limiter, ws_hub

router = APIRouter()


class ChatCreateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


@router.get("/{booking_id}")
async def list_chat_messages(booking_id: str, session: AsyncSession = Depends(get_session)):
    res = await session.execute(
        select(ChatMessage)
        .where(ChatMessage.booking_id == booking_id, ChatMessage.is_reported == False)
        .order_by(ChatMessage.created_at.asc())
    )
    msgs = res.scalars().all()
    return [
        {
            "id": m.id,
            "booking_id": m.booking_id,
            "user_id": m.user_id,
            "text": m.text,
            "created_at": m.created_at.isoformat()
        }
        for m in msgs
    ]


@router.post("/{booking_id}", status_code=status.HTTP_201_CREATED)
async def post_chat_message(
    booking_id: str,
    payload: ChatCreateRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    user_id = user["sub"]
    chat_rate_limiter.check_or_raise(f"chat:{user_id}")

    b_res = await session.execute(select(Booking).where(Booking.id == booking_id))
    if not b_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Booking not found")

    msg = ChatMessage(
        id=f"msg_{uuid.uuid4().hex[:10]}",
        booking_id=booking_id,
        user_id=user_id,
        text=payload.text.strip()
    )
    session.add(msg)
    await session.commit()

    out = {
        "event": "chat_message",
        "id": msg.id,
        "booking_id": msg.booking_id,
        "user_id": msg.user_id,
        "user_name": user.get("name", "Spieler"),
        "text": msg.text,
        "created_at": msg.created_at.isoformat()
    }
    await ws_hub.broadcast(booking_id, out)
    return out


@router.post("/messages/{message_id}/report")
async def report_chat_message(
    message_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    res = await session.execute(select(ChatMessage).where(ChatMessage.id == message_id))
    msg = res.scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    msg.is_reported = True
    await session.commit()
    return {"status": "reported", "message_id": message_id}


@router.websocket("/ws/{room_id}")
async def websocket_chat_endpoint(websocket: WebSocket, room_id: str):
    await ws_hub.connect(room_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await ws_hub.broadcast(room_id, {
                "event": data.get("event", "chat_message"),
                "room_id": room_id,
                "data": data
            })
    except WebSocketDisconnect:
        ws_hub.disconnect(room_id, websocket)
    except Exception:
        ws_hub.disconnect(room_id, websocket)
