from pwm import PWM
from machine import Pin


class LED(Pin):
    is_on = False
    pin = ''

    def __init__(self, pid:str):
        super().__init__(pid, Pin.OUT)
        self.pin = pid
        self.value(0)

    def value(self, v):
        super().value(v)
        self.is_on = bool(v)

    def on(self):
        self.value(1)

    def off(self):
        self.value(0)

    def high(self):
        self.value(1)

    def low(self):
        self.value(0)

    def toggle(self):
        if self.is_on:
            self.value(0)
        else:
            self.value(1)


class LEDpwm(PWM):
    _brightness = 0

    def __init__(self, p: str):
        super().__init__(p, freq=1250, width=255)

    def brightness(self, val=None) -> int:
        if val is not None:
            if val < 0:
                val = 0
            if val > 100:
                val = 100
        else:
            return self._brightness
        if val == 0:
            self.p.low()
            self.duty(0)
            self._brightness = 0

        if val is not None and val > 0:
            self.duty(val)
            self._brightness = val