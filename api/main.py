import asyncio
from collections import deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

app = FastAPI(title="Robot Health API", version="0.1.0")


class SnapshotPayload(BaseModel):
    telemetry: Dict[str, Any] = {}
    status: Dict[str, Any] = {}
    alerts: Dict[str, Any] = {}
    updated_at: str = ""


class ConnectionManager:
    def __init__(self) -> None:
        self.connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.connections:
            self.connections.remove(websocket)

    async def broadcast(self, payload: Dict[str, Any]) -> None:
        disconnected: List[WebSocket] = []
        for ws in self.connections:
            try:
                await ws.send_json(payload)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.disconnect(ws)


manager = ConnectionManager()
latest_snapshot: Dict[str, Any] = {
    "telemetry": {},
    "status": {"status": "unknown"},
    "alerts": {"recent_alerts": []},
    "updated_at": datetime.now(timezone.utc).isoformat(),
}
snapshot_history: Deque[Dict[str, Any]] = deque(maxlen=500)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"service": "robot-health-api", "status": "ok"}


@app.get("/api/v1/snapshot")
def get_snapshot() -> Dict[str, Any]:
    return latest_snapshot


@app.get("/api/v1/history")
def get_history(limit: int = 50) -> Dict[str, Any]:
    items = list(snapshot_history)[-max(1, min(500, limit)) :]
    return {"count": len(items), "items": items}


@app.post("/api/v1/ingest")
async def ingest_snapshot(payload: SnapshotPayload) -> Dict[str, Any]:
    global latest_snapshot
    latest_snapshot = payload.model_dump()
    if not latest_snapshot.get("updated_at"):
        latest_snapshot["updated_at"] = datetime.now(timezone.utc).isoformat()
    snapshot_history.append(latest_snapshot)
    await manager.broadcast(latest_snapshot)
    return {"accepted": True, "timestamp": latest_snapshot["updated_at"]}


@app.websocket("/ws/live")
async def websocket_live(ws: WebSocket) -> None:
    await manager.connect(ws)
    await ws.send_json(latest_snapshot)
    try:
        while True:
            await asyncio.sleep(20)
            await ws.send_json({"type": "heartbeat", "ts": datetime.now(timezone.utc).isoformat()})
    except WebSocketDisconnect:
        manager.disconnect(ws)
