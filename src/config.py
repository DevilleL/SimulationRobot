"""Paramètres physiques et de contrôle du robot POCAA.

Valeurs issues de la BOM et du cahier des charges. Tout est centralisé ici
pour pouvoir ajuster facilement (et plus tard recaler sur le robot réel).
"""
from dataclasses import dataclass


@dataclass
class RobotConfig:
    # --- Mécanique (base tri-cycle : 2 roues motrices + 1 roue folle) ---
    wheel_diameter: float = 0.144      # m  (BOM : roue motrice 144 mm)
    track_width: float = 0.30          # m  (entraxe entre les 2 roues motrices, à mesurer)

    # --- Moteurs DC brushless 12 V avec encodeur ---
    motor_max_speed: float = 11.0      # rad/s  (vitesse roue à pleine puissance)
    motor_tau: float = 0.15            # s   (constante de temps du moteur, réponse 1er ordre)
    encoder_ticks_per_rev: int = 2048  # ticks/tour d'encodeur

    # --- Asservissement ---
    control_dt: float = 0.02           # s   (boucle de contrôle à 50 Hz)
    kp: float = 0.7
    ki: float = 1.1
    kd: float = 0.0

    # --- Confort / sécurité ---
    accel_time: float = 1.5            # s   (0 -> vitesse max : rampe d'accélération)
    decel_time: float = 0.5            # s   (freinage plus rapide que l'accélération)
    reverse_limit: float = 0.30        # marche arrière bridée à 30 % de la puissance
    watchdog_timeout: float = 0.5      # s   (perte réseau > 500 ms => arrêt)

    # --- Anticollision (capteurs de proximité simulés) ---
    sensor_range: float = 0.9          # m   (portée des capteurs avant)
    collision_slow: float = 0.55       # m   (distance où l'on commence à réagir)
    collision_stop: float = 0.30       # m   (distance de standoff conservée)
    avoid_turn: float = 2.5            # rad/s (braquage d'évitement : glisser le long)

    @property
    def wheel_radius(self) -> float:
        return self.wheel_diameter / 2.0

    @property
    def max_linear_speed(self) -> float:
        return self.motor_max_speed * self.wheel_radius
