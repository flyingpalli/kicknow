"""Authentication, token verification, token-bucket rate limiting, and WebSocket hub."""

import os
import time
import hmac
import hashlib
import base64
import json
from typing import Dict, Any, Optional, List
from fastapi import Header, HTTPException, status, WebSocket

SECRET_KEY = os.getenv("SECRET_KEY", "kicknow-prod-secret-key-2026")


def create_access_token(user_id: str, display_name: str = "KickNow Spieler", exp_seconds: int = 86400 * 30) -> str:
    """Create an HMAC-SHA256 signed bearer token."""
    payload = {
        "sub": user_id,
        "name": display_name,
        "iat": int(time.time()),
        "exp": int(time.time()) + exp_seconds
    }
    raw = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8").rstrip("=")
    sig = hmac.new(SECRET_KEY.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{raw}.{sig}"


def verify_access_token(token: str) -> Dict[str, Any]:
    """Verify HMAC-SHA256 token and return decoded payload."""
    if not token or "." not in token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")
    raw, sig = token.split(".", 1)
    expected_sig = hmac.new(SECRET_KEY.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected_sig):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token signature")
    pad = "=" * (-len(raw) % 4)
    try:
        payload = json.loads(base64.urlsafe_b64decode(raw + pad).decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed token payload") from exc
    if payload.get("exp", 0) < time.time():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    return payload


async def get_current_user(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    """FastAPI dependency requiring a valid Bearer token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Bearer token")
    token = authorization.split(" ", 1)[1].strip()
    return verify_access_token(token)


async def get_optional_user(authorization: Optional[str] = Header(default=None)) -> Optional[Dict[str, Any]]:
    """FastAPI dependency returning user payload if authenticated, or None."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        return verify_access_token(authorization.split(" ", 1)[1].strip())
    except HTTPException:
        return None


class TokenBucketRateLimiter:
    """Token-bucket rate limiter (Redis compatible with in-memory fallback)."""

    def __init__(self, capacity: int = 10, refill_rate: float = 1.0):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.buckets: Dict[str, Dict[str, float]] = {}

    def allow(self, key: str, cost: int = 1) -> bool:
        now = time.monotonic()
        bucket = self.buckets.get(key)
        if bucket is None:
            self.buckets[key] = {"tokens": float(self.capacity - cost), "last": now}
            return True

        elapsed = max(0.0, now - bucket["last"])
        tokens = min(float(self.capacity), bucket["tokens"] + elapsed * self.refill_rate)
        if tokens < cost:
            bucket["tokens"] = tokens
            bucket["last"] = now
            return False

        bucket["tokens"] = tokens - cost
        bucket["last"] = now
        return True

    def check_or_raise(self, key: str, cost: int = 1) -> None:
        if not self.allow(key, cost=cost):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Bitte kurz warten."
            )

    def reset(self) -> None:
        self.buckets.clear()


chat_rate_limiter = TokenBucketRateLimiter(capacity=5, refill_rate=0.5)
booking_rate_limiter = TokenBucketRateLimiter(capacity=5, refill_rate=0.2)


class WebSocketHub:
    """Manages active WebSocket connections for real-time match chats and slot occupancy updates."""

    def __init__(self) -> None:
        self.rooms: Dict[str, List[WebSocket]] = {}

    async def connect(self, room: str, ws: WebSocket) -> None:
        await ws.accept()
        self.rooms.setdefault(room, []).append(ws)

    def disconnect(self, room: str, ws: WebSocket) -> None:
        conns = self.rooms.get(room, [])
        if ws in conns:
            conns.remove(ws)

    async def broadcast(self, room: str, message: Dict[str, Any]) -> None:
        conns = list(self.rooms.get(room, []))
        for ws in conns:
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(room, ws)


ws_hub = WebSocketHub()
