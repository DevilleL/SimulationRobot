"""Client « robot » : tourne sur le PC, exécute la simulation et se connecte
en SORTANT vers le relais (donc pas besoin d'ouvrir de port sur la box).

Il reçoit les commandes des pilotes et renvoie la télémétrie ~25 fois/s.
Si plus aucune commande n'arrive (déconnexion), le watchdog interne arrête
le robot — la sécurité est conservée.

Lancement :
  python -m web_control.robot_client --url wss://mon-relais.onrender.com \
         --room demo --token demo-token-change-me
"""
import argparse
import asyncio
import json

from src.robot import Robot
from src.config import RobotConfig


class RobotSession:
    """Cœur testable, sans réseau : applique les commandes et fait avancer la sim."""
    def __init__(self, cfg: RobotConfig = None, win_w=900, win_h=700, ppm=200):
        self.cfg = cfg or RobotConfig()
        self.robot = Robot(self.cfg)
        self.t = 0.0
        margin = self.cfg.track_width / 2
        self.x_limit = (win_w / 2) / ppm - margin
        self.y_limit = (win_h / 2) / ppm - margin

    def on_command(self, v, w):
        # rafraîchit l'horodatage -> le watchdog reste satisfait tant qu'on reçoit
        self.robot.command(float(v), float(w), self.t)

    def step(self, dt):
        self.t += dt
        tel = self.robot.step(dt, self.t)
        # bornage dans le cadre (cohérent avec la fenêtre pygame)
        bx = max(-self.x_limit, min(self.x_limit, tel["x"]))
        by = max(-self.y_limit, min(self.y_limit, tel["y"]))
        self.robot.pose = (bx, by, self.robot.pose[2])
        tel["x"], tel["y"] = bx, by
        return tel

    def telemetry(self, tel):
        """Message JSON envoyé aux pilotes (bornes incluses pour les retardataires)."""
        return json.dumps({
            "type": "tel",
            "x": round(tel["x"], 4), "y": round(tel["y"], 4), "theta": round(tel["theta"], 4),
            "vL": round(tel["meas_l"], 3), "vR": round(tel["meas_r"], 3),
            "spL": round(tel["sp_l"], 3), "spR": round(tel["sp_r"], 3),
            "v": round(tel["v"], 3), "w": round(tel["w"], 3),
            "state": tel["state"],
            "xlim": round(self.x_limit, 3), "ylim": round(self.y_limit, 3),
            "track": self.cfg.track_width,
        })


async def run(url, room, token):
    import websockets  # importé ici pour que les tests n'aient pas besoin du paquet
    endpoint = f"{url.rstrip('/')}/ws/robot?room={room}&token={token}"
    session = RobotSession()
    dt = session.cfg.control_dt          # 0.02 s -> 50 Hz
    print(f"Connexion au relais : {endpoint}")
    async with websockets.connect(endpoint, ping_interval=20) as ws:
        print("Robot en ligne. En attente de pilotes…")

        async def receive():
            async for raw in ws:
                try:
                    m = json.loads(raw)
                    if m.get("type") == "cmd":
                        session.on_command(m.get("v", 0.0), m.get("w", 0.0))
                    elif m.get("type") == "ping":
                        # renvoie le ping tel quel pour la mesure de latence
                        await ws.send(json.dumps({"type": "pong", "id": m.get("id")}))
                except (ValueError, TypeError):
                    pass

        async def loop():
            send_every = 2          # 50 Hz / 2 = 25 Hz de télémétrie
            i = 0
            while True:
                tel = session.step(dt)
                i += 1
                if i % send_every == 0:
                    await ws.send(session.telemetry(tel))
                await asyncio.sleep(dt)

        await asyncio.gather(receive(), loop())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True, help="URL du relais, ex: wss://xxx.onrender.com")
    ap.add_argument("--room", default="demo")
    ap.add_argument("--token", default="demo-token-change-me")
    args = ap.parse_args()
    try:
        asyncio.run(run(args.url, args.room, args.token))
    except KeyboardInterrupt:
        print("\nArrêt.")


if __name__ == "__main__":
    main()
