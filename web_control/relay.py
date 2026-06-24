"""Relais WebSocket — à déployer sur Render (ou tout hébergeur Python).

Rôle : mettre en relation le PC (qui exécute la simulation) et les navigateurs,
sans que le PC ait besoin d'être joignable directement (il se connecte en sortant).

Endpoints :
  GET  /                      -> page d'état (JSON). L'interface est l'app POCAA-WEB.
  WS   /ws/robot?room=&token= -> connexion du PC (un seul robot par room)
  WS   /ws/pilot?room=&token= -> connexion d'un pilote (POCAA-WEB, plusieurs possibles)

Sécurité : un token partagé (variable d'environnement PILOT_TOKEN) protège
l'accès. À déployer derrière HTTPS/WSS (Render le fournit automatiquement).

Lancement local :  uvicorn web_control.relay:app --reload --port 8000
Sur Render        :  uvicorn web_control.relay:app --host 0.0.0.0 --port $PORT
"""
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query

from .hub import Hub

TOKEN = os.environ.get("PILOT_TOKEN", "demo-token-change-me")

app = FastAPI(title="POCAA — relais de pilotage")
hub = Hub()


@app.get("/")
async def index():
    # Le relais ne sert plus de page : l'interface est l'app POCAA-WEB,
    # qui se connecte ici via /ws/pilot. Ce point sert juste de page d'état.
    return {"service": "POCAA relay", "endpoints": ["/ws/robot", "/ws/pilot", "/health"]}


@app.get("/health")
async def health():
    return {"status": "ok", "rooms": len(hub.rooms)}


async def _safe_send(conn, text):
    try:
        await conn.send_text(text)
    except Exception:
        pass


@app.websocket("/ws/robot")
async def ws_robot(ws: WebSocket, room: str = Query("default"), token: str = Query("")):
    if token != TOKEN:
        await ws.close(code=4401)        # 4401 = non autorisé
        return
    await ws.accept()
    hub.add_robot(room, ws)
    try:
        while True:
            msg = await ws.receive_text()          # télémétrie venant du robot
            for pilot in hub.pilots_of(room):
                await _safe_send(pilot, msg)
    except WebSocketDisconnect:
        pass
    finally:
        hub.remove(room, ws)


@app.websocket("/ws/pilot")
async def ws_pilot(ws: WebSocket, room: str = Query("default"), token: str = Query("")):
    if token != TOKEN:
        await ws.close(code=4401)
        return
    await ws.accept()
    hub.add_pilot(room, ws)
    # informe le pilote si le robot est en ligne
    await _safe_send(ws, '{"type":"status","robot_online":%s}' % ("true" if hub.has_robot(room) else "false"))
    try:
        while True:
            msg = await ws.receive_text()          # commande venant du pilote
            robot = hub.robot_of(room)
            if robot is not None:
                await _safe_send(robot, msg)
    except WebSocketDisconnect:
        pass
    finally:
        hub.remove(room, ws)
