"""
Реализация работы моторов для IskraJS и Motor Shield
Обратите внимание, что пины P4, P5, P6, P7 используются для управления моторами
P4 - H1 - направление вращения мотора 1 - 1 по часовой, 0 против часовой
P5 - E1 - работа мотора 1 - 1 работает, 0 не работает
P6 - E2 - работа мотора 1 - 1 работает, 0 не работает
P7 - H2 - направление вращения мотора 2 - 1 по часовой, 0 против часовой

"""
from pwm import PWM
from machine import Pin


class Motor(object):
    """
    Класс работы с мотором
    """
    __slots__ = ['_hpin', '_epin', '_direction', '_power', '_mode']

    def __init__(self, h_pin, e_pin, mode=1):
        self._hpin = Pin(h_pin, Pin.OUT)
        self._epin = PWM(e_pin)
        self._mode = mode

    def stop(self):
        """
        Останавливает мотор
        """
        self._epin.value(0)

    def forward(self, power=100):
        """
        Движение мотора 'вперёд'
        """
        self._hpin.value(self._mode)
        self._epin.duty(power)

    def backward(self, power=100):
        """
        Движение мотора 'назад'
        """
        self._hpin.value(int(self._mode + 1) % 2)
        self._epin.duty(power)


class Motors2WD(object):
    """
    Класс для двухколёсной системы моторов.
    """
    __slots__ = ['M1', 'M2', 'reversed']

    def __init__(self):
        self.reversed = False
        self.M1 = Motor('P4', "P5", mode=int(not self.reversed))
        self.M2 = Motor('P7', 'P6', mode=int(self.reversed))

    def forward(self, power=100):
        """
        Движение вперёд
        power - определяет влияния, по умолчанию 100%
        """
        self.M1.forward(power)
        self.M2.forward(power)

    def backward(self, power=100):
        """
        Движение назад
        power - определяет влияния, по умолчанию 100%
        """
        self.M1.backward(power)
        self.M2.backward(power)

    def stop(self):
        """
        Остановка платформы
        """
        self.M1.stop()
        self.M2.stop()

    def reverse_motors(self):
        """
        Меняет направление вращения моторов.
        """
        self.reversed = not self.reversed
        self.M1 = Motor('P4', "P5", mode=int(not self.reversed))
        self.M2 = Motor('P7', 'P6', mode=int(self.reversed))

    def left(self, power=100):
        """
        Поворот налево
        """
        self.M1.forward(power)
        self.M2.backward(power)

    def right(self, power=100):
        """
        Поворот направо
        """
        self.M1.backward(power)
        self.M2.forward(power)
