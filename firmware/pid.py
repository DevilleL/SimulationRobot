"""PID + rampe d'accélération — port MicroPython.

Identique à src/pid.py (Python pur, donc compatible MicroPython tel quel) :
on garde une copie ici pour que le firmware ESP32 soit autonome.
"""


class PID:
    def __init__(self, kp, ki, kd, out_min=-1.0, out_max=1.0):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.out_min, self.out_max = out_min, out_max
        self._integral = 0.0
        self._prev_error = 0.0

    def reset(self):
        self._integral = 0.0
        self._prev_error = 0.0

    def update(self, setpoint, measurement, dt):
        error = setpoint - measurement
        self._integral += error * dt
        derivative = (error - self._prev_error) / dt if dt > 0 else 0.0
        output = self.kp * error + self.ki * self._integral + self.kd * derivative
        # saturation + anti-emballement
        if output > self.out_max:
            output = self.out_max
            self._integral -= error * dt
        elif output < self.out_min:
            output = self.out_min
            self._integral -= error * dt
        self._prev_error = error
        return output


class Ramp:
    """Limite la variation d'une consigne (décélération plus rapide possible)."""
    def __init__(self, max_rate, max_rate_down=None):
        self.max_rate = max_rate
        self.max_rate_down = max_rate_down if max_rate_down is not None else max_rate
        self.value = 0.0

    def update(self, target, dt):
        rate = self.max_rate_down if abs(target) < abs(self.value) else self.max_rate
        step = rate * dt
        delta = target - self.value
        if delta > step:
            delta = step
        elif delta < -step:
            delta = -step
        self.value += delta
        return self.value
