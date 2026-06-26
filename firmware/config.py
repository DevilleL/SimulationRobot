# Configuration du firmware ESP32 (MicroPython) — broches & paramètres.
# ⚠️ Adapter les numéros de GPIO au câblage réel (voir docs/INTEGRATION_MATERIELLE.md).

# --- Moteurs (pont en H type L298N : ENA=PWM vitesse, IN1/IN2 = sens) ---
MOTOR_L = {"pwm": 25, "in1": 26, "in2": 27}
MOTOR_R = {"pwm": 32, "in1": 33, "in2": 14}
PWM_FREQ = 1000          # Hz
PWM_MAX = 1023           # duty 10 bits (PWM ESP32 sous MicroPython)

# --- Encodeurs quadrature (voies A et B) ---
ENCODER_L = {"a": 34, "b": 35}
ENCODER_R = {"a": 36, "b": 39}
ENCODER_TICKS_PER_REV = 2048

# --- Mécanique (cohérent avec la simulation / la BOM) ---
WHEEL_DIAMETER = 0.144   # m
TRACK_WIDTH = 0.30       # m  (entraxe roues — à mesurer sur le châssis)
MOTOR_MAX_SPEED = 11.0   # rad/s (vitesse roue à pleine puissance)

# --- Asservissement (mêmes gains que la simulation, à recaler sur la vraie carte) ---
CONTROL_DT = 0.02        # s  (boucle de contrôle à 50 Hz)
KP, KI, KD = 0.7, 1.1, 0.0
ACCEL_TIME = 1.5         # s  (rampe d'accélération 0 -> max)
DECEL_TIME = 0.5         # s  (freinage plus rapide)
REVERSE_LIMIT = 0.30     # marche arrière bridée à 30 %
WATCHDOG_TIMEOUT = 0.5   # s  (perte de commande > 500 ms => arrêt)
