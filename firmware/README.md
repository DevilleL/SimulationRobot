# Firmware ESP32 — locomotion POCAA (MicroPython)

Squelette du contrôleur moteurs embarqué (story **S31**). Il reprend **la même
logique que la simulation validée** (cinématique, PID, rampes, watchdog, bridage
marche arrière), mais pilote le vrai matériel : ponts en H + encodeurs.

```
[Raspberry Pi] --série/USB {"v":..,"w":..}--> [ESP32 : main.py] --PWM--> [ponts en H] --> moteurs
                                                     ^—— encodeurs (rad/s) ——┘
```

## Fichiers
- `config.py` — broches (GPIO) et paramètres (à adapter au câblage réel).
- `pid.py` — PID + rampe (port du `src/pid.py`, identique).
- `main.py` — boucle de contrôle 50 Hz : lecture commandes série, PID, moteurs, watchdog.

## Flasher (quand tu auras la carte)
1. Installer MicroPython sur l'ESP32 :
   ```bash
   pip install esptool
   esptool.py --port COMx erase_flash
   esptool.py --port COMx write_flash 0x1000 esp32-micropython.bin
   ```
2. Copier les fichiers sur la carte (avec `mpremote` ou Thonny) :
   ```bash
   mpremote connect COMx fs cp config.py pid.py main.py :
   ```
3. `main.py` démarre automatiquement au boot.

## Tester
- Envoyer une commande depuis le Pi (ou un terminal série) :
  `{"v": 0.3, "w": 0.0}\n` → les roues doivent tourner.
- Couper l'envoi > 0,5 s → le **watchdog** arrête les moteurs.

## ⚠️ À régler sur la vraie carte (TODO)
- **Sens des moteurs / encodeurs** : inverser `in1`/`in2` ou la lecture `b.value()` si une roue tourne à l'envers.
- **Gains PID** : repartir des valeurs de la simulation (`config.py`) puis affiner.
- **Lien série** : `main.py` lit `sys.stdin` (USB REPL). Si le Pi utilise une UART dédiée, remplacer par `machine.UART`.
- **Type de moteur** : ce squelette suppose un pilotage type pont en H (PWM + sens). Si les moteurs brushless nécessitent un ESC, adapter `Motor.drive()`.
