# Pilotage de la simulation depuis le web

Permet de **piloter la simulation (qui reste sur ton PC) depuis un navigateur,
de n'importe où**, sans ouvrir de port sur ta box. C'est la story **S34**
(protocole de pilotage temps réel).

Le **front-end est l'application POCAA-WEB** (interface de Valentin : visio,
tableau blanc, avatar **et** pilotage). Ce dossier `web_control` ne fournit plus
de page : il contient seulement le **backend** (relais + client robot).

## Architecture

```
[POCAA-WEB /student]  ──cmd{v,w}──▶  [relay.py]  ──▶  [robot_client.py + simulation]
  (front, port 5173)      WSS           (relais)           (ta simulation locomotion)
       │                                                          │
       └──────────────────  télémétrie {x,y,theta,state}  ◀───────┘
```

- **WebSocket** (pas REST) : temps réel bidirectionnel, faible latence.
- Le PC se **connecte en sortant** vers le relais → pas de configuration routeur.
- Sécurité : un **token** partagé (`PILOT_TOKEN`) protège l'accès ; le **watchdog**
  arrête le robot si la connexion tombe.

POCAA-WEB envoie des commandes `move {direction, speed}` que son module
`src/lib/robot-relay.ts` traduit en `{type:"cmd", v, w}` pour le relais.

## Tester en local (3 terminaux)

Depuis `robot-locomotion` :
```powershell
py -m pip install -r web_control/requirements.txt

# Terminal 1 — le relais
py -m uvicorn web_control.relay:app --port 8000

# Terminal 2 — le robot (la simulation). ATTENTION au room : il doit
# correspondre à celui de POCAA-WEB (par défaut "demo-classroom").
py -m web_control.robot_client --url ws://localhost:8000 --room demo-classroom --token demo-token-change-me
```

Puis le front POCAA-WEB (dans le dossier `POCAA-WEB`, autre terminal) :
```powershell
npm install
npm run dev          # Vite -> http://localhost:5173
```

Enfin, dans le navigateur : ouvre **`http://localhost:5173/student`**, choisis ton
mode (caméra/avatar), et pilote (flèches ou boutons). Le badge **« simulateur
connecté »** doit être vert, et le robot bouge dans la simulation.

> Le `room` lie le pilote et le robot. POCAA-WEB utilise `demo-classroom` par
> défaut (paramètre `?room=` de l'URL) — lance donc `robot_client` avec le même.

## Configurer l'URL du relais côté POCAA-WEB

Dans `POCAA-WEB`, copie `.env.example` en `.env.local` :
```
VITE_RELAY_URL=ws://localhost:8000        # ou wss://ton-relais.onrender.com
VITE_RELAY_TOKEN=demo-token-change-me     # = PILOT_TOKEN du backend
```

## Déployer le relais sur Render

1. Pousse `robot-locomotion` sur GitHub.
2. Render : **New > Blueprint** (le `render.yaml` est détecté), ou Web Service avec
   build `pip install -r web_control/requirements.txt` et start
   `uvicorn web_control.relay:app --host 0.0.0.0 --port $PORT`.
3. Variable d'environnement **`PILOT_TOKEN`** (valeur secrète).
4. Render donne une URL `https://...onrender.com` → mets `wss://...onrender.com`
   dans `VITE_RELAY_URL` de POCAA-WEB.

> Plan gratuit Render : s'endort après inactivité (premier accès ~30 s).

## Sécurité

- **Change `PILOT_TOKEN`** (la valeur par défaut est publique).
- Le token est visible côté navigateur : OK pour une démo, prévoir une vraie
  authentification pour un usage réel.
- Le watchdog (0,5 s) reste la sécurité ultime : réseau coupé → robot arrêté.
