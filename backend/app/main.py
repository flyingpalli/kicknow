"""KickNow Production Backend Service Entry Point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from backend.app.db.session import init_db
from backend.app.core.security import ws_hub
from backend.app.api.v1 import pitches, bookings, chats, reviews, users, submissions


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(seed=True)
    yield


app = FastAPI(
    title="KickNow API",
    version="1.0.0",
    docs_url="/docs",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://kicknow.app",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8080"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pitches.router, prefix="/api/v1/pitches", tags=["pitches"])
app.include_router(bookings.router, prefix="/api/v1/bookings", tags=["bookings"])
app.include_router(chats.router, prefix="/api/v1/chats", tags=["chats"])
app.include_router(reviews.router, prefix="/api/v1/reviews", tags=["reviews"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(submissions.router, prefix="/api/v1/submissions", tags=["submissions"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "KickNow API", "version": "1.0.0"}


@app.get("/datenschutz", response_class=HTMLResponse, tags=["legal"])
async def privacy_policy():
    """Explicit GDPR / DSGVO privacy policy explaining ephemeral location data usage."""
    return """<!DOCTYPE html>
<html lang="de"><head><meta charset="utf-8"><title>Datenschutzerklärung – KickNow</title></head>
<body>
  <h1>Datenschutzerklärung (DSGVO / GDPR)</h1>
  <p>KickNow verarbeitet personenbezogene Daten streng nach den Vorgaben der Europäischen Datenschutz-Grundverordnung (DSGVO).</p>
  <h2>1. Ephemere Standortdaten (Keine Speicherung)</h2>
  <p>Standortkoordinaten (Breiten- und Längengrad), die vom Endgerät übermittelt werden, dienen ausschließlich der flüchtigen (ephemeren) Umkreissuche und Entfernungsberechnung im Arbeitsspeicher. Nutzerstandorte werden niemals dauerhaft in Datenbanktabellen gespeichert.</p>
  <h2>2. Öffentliche Spielpläne & Amateurfußball-Daten</h2>
  <p>Bei der Einbindung von Spielplänen der Regionalverbände (z. B. BFV, HFV, FVM) werden ausschließlich Spieltags-Metadaten (Anstoßzeit, Vereinsnamen, Spielklasse, Sportanlage) gespeichert. Es werden keinerlei Spielernamen oder Kontaktdaten erfasst.</p>
  <h2>3. Recht auf Löschung (Art. 17 DSGVO)</h2>
  <p>Nutzer können ihr Konto sowie alle verknüpften Profildaten, Bewertungen und Nachrichten jederzeit über die Funktion „Konto löschen“ (`DELETE /api/v1/users/me`) vollständig und unwiderruflich entfernen.</p>
</body></html>"""


@app.get("/impressum", response_class=HTMLResponse, tags=["legal"])
async def legal_notice():
    """Legal notice in accordance with § 5 DDG (former TMG)."""
    return """<!DOCTYPE html>
<html lang="de"><head><meta charset="utf-8"><title>Impressum – KickNow</title></head>
<body>
  <h1>Impressum (gemäß § 5 DDG)</h1>
  <p><strong>KickNow – Informations- und Matchmaking-Plattform für öffentlichen Freizeitfußball</strong></p>
  <p>Marienplatz 1, 80331 München, Deutschland</p>
  <p>Kontakt: kontakt@kicknow.app</p>
  <p>Hinweis zur Haftung: KickNow ist ein reines Informations- und Koordinationswerkzeug für offene Freizeit-Fußballrunden ohne Zahlungsabwicklung oder gewerbliche Platzvermietung.</p>
</body></html>"""


@app.websocket("/ws/{room_id}")
async def root_websocket_endpoint(websocket: WebSocket, room_id: str):
    await ws_hub.connect(room_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await ws_hub.broadcast(room_id, {
                "event": data.get("event", "update"),
                "room_id": room_id,
                "data": data
            })
    except WebSocketDisconnect:
        ws_hub.disconnect(room_id, websocket)
    except Exception:
        ws_hub.disconnect(room_id, websocket)
