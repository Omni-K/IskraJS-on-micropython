"""
Класс для реализации работы микросервоприводов с платой IskraJS с micropython 1.13
Поддерживаемые сервоприводы: Feetech FS90
"""
from pyb import Timer
from machine import Pin


class PWM:
    pin = None
    freq = None
    width = None
    cnl = None
    t = None
    p = None

    pin_dict = {'A0': (2, 1),
                'A1': (2, 2),
                'A2': (2, 3),
                'A3': (2, 4),
                'A5': (2, 1),
                'LED1': (4, 1),
                'LED2': (4, 2),
                'P0': (2, 4),
                'P1': (2, 3),
                'P2': (3, 1),
                'P3': (3, 2),
                'P5': (3, 4),
                'P6': (3, 3),
                'P8': (3, 1),
                'P9': (3, 2),
                'SCL': (4, 3),
                'SDA': (4, 4),
                }

    def __init__(self, p: str, freq=500, width=255):
        self.pin = p
        self.freq = freq
        self.width = width

        if p not in self.pin_dict.keys():
            raise ValueError(p + ' Pin is not PWM')
        self.p = Pin(p, Pin.OUT)
        self.t = Timer(self.pin_dict[p][0], freq=freq)
        self.cnl = self.t.channel(self.pin_dict[p][1], Timer.PWM, pin=self.p)
        self.cnl.pulse_width(width)

    def duty(self, percent):
        if percent < 0:
            percent = 0
        if percent > 100:
            percent = 100
        self.cnl.pulse_width_percent(percent)


def convert_from_angle_to_duty(angles: int):
    """
    Преобразует угол в ШИМ
    """
    dmin = 2.5
    dmax = 12.5
    delta = dmax - dmin
    amin = 0
    amax = 180
    if angles <= 0:
        angles = 0
    if angles >= 180:
        angles = 180
    val = dmin + angles * int(delta / amax * 100) / 100
    return val


class ServoFS90:
    """
    Класс работы с микросервоприводом Feetech FS90
    """
    _servo: PWM
    _angle: int = 0

    def __init__(self, pin: str):
        self._servo = PWM(pin, freq=50, width=5)

    def set_angle(self, angle):
        """
        Устанавливает угол поворота
        """
        self._angle = angle
        self._servo.duty(convert_from_angle_to_duty(angle))

    def get_angle(self):
        """
        Возвращает текущий угол
        """
        return self._angle
