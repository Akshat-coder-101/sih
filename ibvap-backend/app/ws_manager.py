from typing import List
from fastapi import WebSocket
import json


class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast_alert(self, alert_dict: dict):
        """Push a new alert to every connected dashboard. FR-5.2 requires
        this within ≤2s of the event — a direct WS push satisfies that
        trivially compared to polling."""
        dead = []
        payload = json.dumps({"event": "new_alert", "data": alert_dict}, default=str)
        for ws in self.active:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    async def broadcast_telemetry(self, telemetry_dict: dict):
        """Push real-time worker telemetry updates directly over WebSocket to connected dashboards."""
        dead = []
        payload = json.dumps({"event": "telemetry_update", "data": telemetry_dict}, default=str)
        for ws in self.active:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()
