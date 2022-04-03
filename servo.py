"""
Класс для реализации работы микросервоприводов с платой IskraJS с micropython 1.13
Поддерживаемые сервоприводы: Feetech FS90
"""
from pwm import PWM

__author__ = "Nikolay Putko"
__copyright__ = "Nikolay Putko, 2022 onwards."
__license__ = "MIT https://opensource.org/licenses/MIT (as used by MicroPython)."
__version__ = "1.0.0"

def _convert_from_angle_to_duty(angles: int):
    """
    Преобразует угол в ШИМ-процент
    """
    dmin = 2.5
    dmax = 12.5
    delta = dmax - dmin
    if angles <= 0:
        angles = 0
    if angles >= 180:
        angles = 180
    val = dmin + angles * int(delta / 180 * 100) / 100
    return val


class ServoFS90:
    """
    Класс работы с микросервоприводом Feetech FS90
    """
    __slots__ = ['_servo', '_angle']

    def __init__(self, pin: str):
        self._servo = PWM(pin, freq=50, width=5)
        self._angle = 0
        self.set_angle(0)

    def set_angle(self, angle):
        """
        Устанавливает угол поворота
        """
        self._angle = angle
        self._servo.duty(_convert_from_angle_to_duty(angle))

    def get_angle(self):
        """
        Возвращает текущий угол
        """
        return self._angle
