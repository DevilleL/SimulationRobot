"""Firmware ESP32 (MicroPython) — squelette de locomotion POCAA.

Rôle (= ce que fait le `robot_client` en simulation, mais sur la vraie carte) :
reçoit des commandes {"v":.., "w":..} en série depuis le Raspberry Pi, asservit
les deux roues par PID grâce aux encodeurs, et pilote les ponts en H.

⚠️ SQUELETTE : à flasher et à régler sur la carte réelle. Les points dépendant
du matériel sont marqués « TODO ». La logique (cinématique, PID, rampes,
watchdog, bridage marche arrière) est identique à la simulation validée.
"""
import sys
import json
import math
import time
import uselect

from machine import Pin, PWM

import config as cfg
from pid import PID, Ramp

WHEEL_R = cfg.WHEEL_DIAMETER / 2.0


class Motor:
    """Pont en H : ENA (PWM) pour la vitesse, IN1/IN2 pour le sens."""
    def __init__(self, pins):
        self.pwm = PWM(Pin(pins["pwm"]), freq=cfg.PWM_FREQ)
        self.in1 = Pin(pins["in1"], Pin.OUT)
        self.in2 = Pin(pins["in2"], Pin.OUT)

    def drive(self, u):                      # u dans [-1, 1]
        if u > 1.0:
            u = 1.0
        elif u < -1.0:
            u = -1.0
        if u >= 0:
            self.in1.value(1)
            self.in2.value(0)
        else:
            self.in1.value(0)
            self.in2.value(1)
        self.pwm.duty(int(abs(u) * cfg.PWM_MAX))


class Encoder:
    """Encodeur quadrature : comptage par interruption sur la voie A."""
    def __init__(self, pins):
        self.a = Pin(pins["a"], Pin.IN)
        self.b = Pin(pins["b"], Pin.IN)
        self.count = 0
        self._last = 0
        # TODO matériel : vérifier le sens (inverser b.value() si la roue compte à l'envers)
        self.a.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._on_edge)

    def _on_edge(self, _pin):
        self.count += 1 if self.b.value() else -1

    def speed(self, dt):                     # vitesse roue mesurée (rad/s)
        d = self.count - self._last
        self._last = self.count
        rev = d / cfg.ENCODER_TICKS_PER_REV
        return (rev * 2.0 * math.pi) / dt if dt > 0 else 0.0


def inverse_kinematics(v, w):
    """(v, w) -> vitesses angulaires roues gauche/droite (rad/s)."""
    v_left = v - w * cfg.TRACK_WIDTH / 2.0
    v_right = v + w * cfg.TRACK_WIDTH / 2.0
    return v_left / WHEEL_R, v_right / WHEEL_R


def clamp_reverse(u):
    """Bride la commande en marche arrière."""
    return max(u, -cfg.REVERSE_LIMIT) if u < 0 else u


# --- Instanciation matériel + contrôle ---
motor_l = Motor(cfg.MOTOR_L)
motor_r = Motor(cfg.MOTOR_R)
enc_l = Encoder(cfg.ENCODER_L)
enc_r = Encoder(cfg.ENCODER_R)
pid_l = PID(cfg.KP, cfg.KI, cfg.KD)
pid_r = PID(cfg.KP, cfg.KI, cfg.KD)
_rate_up = cfg.MOTOR_MAX_SPEED / cfg.ACCEL_TIME
_rate_down = cfg.MOTOR_MAX_SPEED / cfg.DECEL_TIME
ramp_l = Ramp(_rate_up, _rate_down)
ramp_r = Ramp(_rate_up, _rate_down)

# Lecture série non bloquante des commandes (USB/UART REPL)
_poll = uselect.poll()
_poll.register(sys.stdin, uselect.POLLIN)

_cmd_v = 0.0
_cmd_w = 0.0
_last_cmd = time.ticks_ms()


def read_command():
    """Lit une éventuelle ligne JSON {"v":.., "w":..} sans bloquer."""
    global _cmd_v, _cmd_w, _last_cmd
    if _poll.poll(0):
        try:
            line = sys.stdin.readline()
            m = json.loads(line)
            _cmd_v = float(m.get("v", 0.0))
            _cmd_w = float(m.get("w", 0.0))
            _last_cmd = time.ticks_ms()
        except Exception:
            pass                              # ligne incomplète / non-JSON : on ignore


def control_loop():
    dt = cfg.CONTROL_DT
    period_ms = int(dt * 1000)
    while True:
        t0 = time.ticks_ms()
        read_command()
        v, w = _cmd_v, _cmd_w

        # watchdog : plus de commande depuis trop longtemps -> arrêt
        if time.ticks_diff(time.ticks_ms(), _last_cmd) > cfg.WATCHDOG_TIMEOUT * 1000:
            v = 0.0
            w = 0.0

        target_l, target_r = inverse_kinematics(v, w)
        sp_l = ramp_l.update(target_l, dt)
        sp_r = ramp_r.update(target_r, dt)
        meas_l = enc_l.speed(dt)
        meas_r = enc_r.speed(dt)
        u_l = clamp_reverse(pid_l.update(sp_l, meas_l, dt))
        u_r = clamp_reverse(pid_r.update(sp_r, meas_r, dt))
        motor_l.drive(u_l)
        motor_r.drive(u_r)

        # tenir la cadence 50 Hz
        elapsed = time.ticks_diff(time.ticks_ms(), t0)
        if elapsed < period_ms:
            time.sleep_ms(period_ms - elapsed)


if __name__ == "__main__":
    control_loop()
