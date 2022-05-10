from pyb import ADC
from machine import Pin


class Thermo(ADC):

    def __int__(self, pin: str):
        super(Thermo, self).__int__(Pin(pin, Pin.OUT))

    def get_temperature_in_celsium(self, digits=2):
        """
        Возвращает температуру по шкале Цельсия
        :pagam digits: количество знаков после запятой, по-умолчанию 2
        """
        celsium = (3.3 / 2 ** 12) * self.read() * 100 - 50
        celsium = round(celsium, digits)
        return celsium

    def get_temperature_in_kelvin(self, digits=2):
        """
        Возвращает температуру по шкале Кельвина
        :pagam digits: количество знаков после запятой, по-умолчанию 2
        """
        return round(self.get_temperature_in_celsium(digits) + 273.15, digits)

    def get_temperature_in_farenheit(self, digits=2):
        """
        Возвращает температуру по шкале Фаренгейта
        :pagam digits: количество знаков после запятой, по-умолчанию 2
        """
        return round((9/5) * self.get_temperature_in_celsium() + 32, digits)

    def get_temperature_in_reaumur(self, digits=2):
        """
        Возвращает температуру по шкале Реомюра
        :pagam digits: количество знаков после запятой, по-умолчанию 2
        """
        return round(8 * self.get_temperature_in_celsium() / 10, digits)

    def get_temp(self, litera='c', digits=2):
        """
        Возвращает температуру по выбранной шкале
        :param litera: выбор шкалы 'c' - Цельсия, 'k' - Кельвина, 'f' - Фаренгейта, 'r' - Реомюра
        :pagam digits: количество знаков после запятой, по-умолчанию 2
        """
        if litera == 'c' or litera == 'celsium':
            return self.get_temperature_in_celsium(digits)
        elif litera == 'k' or litera == 'kelvin':
            return self.get_temperature_in_kelvin(digits)
        elif litera == 'f' or litera == 'farenheit':
            return self.get_temperature_in_farenheit(digits)
        elif litera == 'r' or litera == 'reomura':
            return self.get_temperature_in_reaumur(digits)
