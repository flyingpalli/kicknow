"""Backend integration and API test suite."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient

from sqlalchemy import delete
from backend.app.main import app
from backend.app.db.session import init_db, async_session_factory
from backend.app.models.schema import Booking, BookingParticipant, ChatMessage, Review, PitchSubmission
from backend.app.core.security import (
    create_access_token,
    chat_rate_limiter,
    booking_rate_limiter,
)


@pytest_asyncio.fixture(scope="module", autouse=True)
async def setup_database():
    await init_db(seed=True)
    async with async_session_factory() as session:
        await session.execute(delete(ChatMessage))
        await session.execute(delete(BookingParticipant))
        await session.execute(delete(Booking))
        await session.execute(delete(Review))
        await session.execute(delete(PitchSubmission))
        await session.commit()
    chat_rate_limiter.reset()
    booking_rate_limiter.reset()
    yield


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_and_legal_routes(client: AsyncClient):
    r_health = await client.get("/health")
    assert r_health.status_code == 200
    assert r_health.json()["status"] == "ok"

    r_ds = await client.get("/datenschutz")
    assert r_ds.status_code == 200
    assert "DSGVO" in r_ds.text
    assert "ephemer" in r_ds.text.lower()

    r_imp = await client.get("/impressum")
    assert r_imp.status_code == 200
    assert "§ 5 DDG" in r_imp.text


@pytest.mark.asyncio
async def test_cities_and_spatial_pitch_search(client: AsyncClient):
    r_cities = await client.get("/api/v1/pitches/cities")
    assert r_cities.status_code == 200
    cities = r_cities.json()
    for c in ["munich", "nuremberg", "berlin", "hamburg", "cologne", "frankfurt"]:
        assert c in cities

    # Spatial search in Munich around Marienplatz
    r_muc = await client.get("/api/v1/pitches/?lat=48.137154&lng=11.576124&radius_km=10")
    assert r_muc.status_code == 200
    muc_pitches = r_muc.json()
    assert len(muc_pitches) >= 20
    # Verify distance ordering
    dists = [p["dist_km"] for p in muc_pitches]
    assert dists == sorted(dists)

    # Spatial search in Berlin around Alexanderplatz
    r_ber = await client.get("/api/v1/pitches/?lat=52.520008&lng=13.404954&radius_km=15")
    assert r_ber.status_code == 200
    ber_pitches = r_ber.json()
    assert len(ber_pitches) >= 3
    assert all(p["city"] == "Berlin" for p in ber_pitches)

    # Surface filter
    r_cage = await client.get("/api/v1/pitches/?lat=48.137154&lng=11.576124&radius_km=15&surface=Käfig")
    assert r_cage.status_code == 200
    assert all(p["cage"] is True for p in r_cage.json())


@pytest.mark.asyncio
async def test_phone_auth_and_token_validation(client: AsyncClient):
    # Unauthenticated booking creation must fail with 401
    r_unauth = await client.post("/api/v1/bookings/", json={
        "pitch_id": "p1",
        "date": "2026-10-22",
        "slot_index": 3
    })
    assert r_unauth.status_code == 401

    # Request phone SMS verification code
    r_req = await client.post("/api/v1/users/auth/request-code", json={
        "phone": "+4915199887766",
        "display_name": "Lukas Test"
    })
    assert r_req.status_code == 200
    code = r_req.json()["demo_code"]

    # Verify code and obtain JWT
    r_ver = await client.post("/api/v1/users/auth/verify", json={
        "identifier": "+49151998887766",
        "code": "000000"
    })
    assert r_ver.status_code == 401

    r_ver_ok = await client.post("/api/v1/users/auth/verify", json={
        "identifier": "+4915199887766",
        "code": code
    })
    assert r_ver_ok.status_code == 200
    token = r_ver_ok.json()["access_token"]

    r_me = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert r_me.status_code == 200
    assert r_me.json()["display_name"] == "Lukas Test"


@pytest.mark.asyncio
async def test_booking_concurrency_and_matchmaking(client: AsyncClient):
    booking_rate_limiter.reset()
    token_org = create_access_token("u0", "Alex Mayer")
    token_p2 = create_access_token("u_player2", "Max Bauer")

    # Find a valid pitch ID
    r_pitches = await client.get("/api/v1/pitches/?lat=48.137154&lng=11.576124&radius_km=10")
    pitch_id = r_pitches.json()[0]["id"]

    # Create a booking on slot 1
    r_book = await client.post(
        "/api/v1/bookings/",
        headers={"Authorization": f"Bearer {token_org}"},
        json={
            "pitch_id": pitch_id,
            "date": "2026-10-25",
            "slot_index": 1,
            "group_size": 4,
            "max_players": 10,
            "level": "Locker",
            "is_open": True,
            "note": "Bringt einen Ball mit!"
        }
    )
    assert r_book.status_code == 201
    booking_id = r_book.json()["id"]

    # Concurrency lock check: duplicate booking on same pitch, date, and slot must return 409 Conflict
    r_dup = await client.post(
        "/api/v1/bookings/",
        headers={"Authorization": f"Bearer {token_p2}"},
        json={
            "pitch_id": pitch_id,
            "date": "2026-10-25",
            "slot_index": 1,
            "group_size": 2,
            "max_players": 8
        }
    )
    assert r_dup.status_code == 409

    # Second user joins the open booking
    r_join = await client.post(
        f"/api/v1/bookings/{booking_id}/join",
        headers={"Authorization": f"Bearer {token_p2}"},
        json={"count": 2, "message": "Sind zu zweit dabei!"}
    )
    assert r_join.status_code == 200
    assert r_join.json()["current_players"] == 6

    # Check slots endpoint reflects the active game
    r_slots = await client.get(f"/api/v1/pitches/{pitch_id}/slots?date=2026-10-25")
    assert r_slots.status_code == 200
    slot_1 = r_slots.json()[1]
    assert slot_1["type"] == "game"
    assert slot_1["count"] == 6
    assert slot_1["free"] == 4


@pytest.mark.asyncio
async def test_chat_rate_limiting_and_reporting(client: AsyncClient):
    chat_rate_limiter.reset()
    token = create_access_token("u0", "Alex Mayer")

    r_pitches = await client.get("/api/v1/pitches/?lat=48.137154&lng=11.576124&radius_km=10")
    pitch_id = r_pitches.json()[0]["id"]

    r_book = await client.post(
        "/api/v1/bookings/",
        headers={"Authorization": f"Bearer {token}"},
        json={"pitch_id": pitch_id, "date": "2026-10-26", "slot_index": 2}
    )
    booking_id = r_book.json()["id"]

    # Send 5 messages allowed by token bucket capacity=5
    last_msg_id = None
    for i in range(5):
        r_msg = await client.post(
            f"/api/v1/chats/{booking_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"text": f"Test Nachricht {i}"}
        )
        assert r_msg.status_code == 201
        last_msg_id = r_msg.json()["id"]

    # 6th immediate message must trigger 429 Too Many Requests
    r_rate = await client.post(
        f"/api/v1/chats/{booking_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"text": "Spam Nachricht"}
    )
    assert r_rate.status_code == 429

    # Report message for moderation
    r_rep = await client.post(
        f"/api/v1/chats/messages/{last_msg_id}/report",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert r_rep.status_code == 200
    assert r_rep.json()["status"] == "reported"


@pytest.mark.asyncio
async def test_community_pitch_submission_two_user_moderation(client: AsyncClient):
    t_sub = create_access_token("u_sub1", "Submitter")
    t_conf1 = create_access_token("u_conf1", "Confirmer 1")
    t_conf2 = create_access_token("u_conf2", "Confirmer 2")

    r_create = await client.post(
        "/api/v1/submissions/",
        headers={"Authorization": f"Bearer {t_sub}"},
        json={
            "name": "Neuer Käfig am Olympiapark",
            "city": "München",
            "district": "Milbertshofen",
            "address": "Spiridon-Louis-Ring 21, 80809 München",
            "lat": 48.1731,
            "lng": 11.5461,
            "surface": "Kunstrasen",
            "cage": True
        }
    )
    assert r_create.status_code == 201
    sub_id = r_create.json()["id"]
    assert r_create.json()["status"] == "pending"

    # First distinct user confirms -> still pending (1/2)
    r_c1 = await client.post(
        f"/api/v1/submissions/{sub_id}/confirm",
        headers={"Authorization": f"Bearer {t_conf1}"}
    )
    assert r_c1.status_code == 200
    assert r_c1.json()["status"] == "pending"
    assert r_c1.json()["confirmation_count"] == 1

    # Second distinct user confirms -> approved and promoted to Pitch table (2/2)
    r_c2 = await client.post(
        f"/api/v1/submissions/{sub_id}/confirm",
        headers={"Authorization": f"Bearer {t_conf2}"}
    )
    assert r_c2.status_code == 200
    assert r_c2.json()["status"] == "approved"
    assert r_c2.json()["promoted_pitch_id"] == f"comm_{sub_id}"

    # Verify newly approved pitch is retrievable
    r_pitch = await client.get(f"/api/v1/pitches/comm_{sub_id}")
    assert r_pitch.status_code == 200
    assert r_pitch.json()["name"] == "Neuer Käfig am Olympiapark"


@pytest.mark.asyncio
async def test_reviews_and_gdpr_account_deletion(client: AsyncClient):
    r_req = await client.post("/api/v1/users/auth/request-code", json={
        "phone": "+4917655443322",
        "display_name": "GDPR Test User"
    })
    r_ver = await client.post("/api/v1/users/auth/verify", json={
        "identifier": "+4917655443322",
        "code": r_req.json()["demo_code"]
    })
    token = r_ver.json()["access_token"]

    r_pitches = await client.get("/api/v1/pitches/?lat=48.137154&lng=11.576124&radius_km=10")
    pitch_id = r_pitches.json()[0]["id"]

    r_rev = await client.post(
        f"/api/v1/reviews/{pitch_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"stars": 5, "text": "Super Rasen!", "tags": ["Sauber"]}
    )
    assert r_rev.status_code == 201

    # Delete account under Art. 17 GDPR
    r_del = await client.delete("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert r_del.status_code == 200
    assert r_del.json()["status"] == "deleted"

    # Subsequent /me call must return 404
    r_me = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert r_me.status_code == 404


def test_websocket_realtime_broadcast():
    with TestClient(app) as tc:
        with tc.websocket_connect("/ws/test_room") as ws1, tc.websocket_connect("/ws/test_room") as ws2:
            ws1.send_json({"event": "chat_message", "text": "Servus vom Platz!"})
            msg1 = ws1.receive_json()
            msg2 = ws2.receive_json()
            assert msg1["room_id"] == "test_room"
            assert msg2["data"]["text"] == "Servus vom Platz!"


def test_frontend_map_header_and_real_geolocation():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    app_js = (root / "kicknow" / "js" / "app.js").read_text(encoding="utf-8")
    app_css = (root / "kicknow" / "css" / "app.css").read_text(encoding="utf-8")

    # 1. Permanent #city-select removed from map header; contextual city chips rendered in search dropdown & filter sheet
    assert 'id="city-select"' not in app_js
    assert "#city-select" not in app_css
    assert "suggest-city-chip" in app_js
    assert "suggest-city-chip" in app_css
    assert "renderSuggestDropdown" in app_js

    # 2. Search bar right-border overflow prevention
    assert "max-width: calc(100% - 28px)" in app_css
    assert ".search-box { position: relative; flex: 1; min-width: 0; }" in app_css
    assert "width: 100%; min-width: 0;" in app_css

    # 3. Real browser geolocation with multi-stage fallback (no "GPS nicht verfügbar" warning on iOS HTTP)
    assert "navigator.geolocation.getCurrentPosition" in app_js
    assert "navigator.geolocation.watchPosition" in app_js
    assert "fetchNetworkGeolocation" in app_js
    assert "GPS nicht verfügbar" not in app_js
    assert "if (!hasRealLocation) meEl.style.display = 'none';" in app_js
    assert "requestRealGeolocation(true);" in app_js

    server_py = (root / "kicknow" / "server" / "server.py").read_text(encoding="utf-8")
    assert "DualProtocolHTTPServer" in server_py
    assert "/api/geo" in server_py


