from pyb import ADC
from machine import Pin

# Work In Progress

class LightSensor(ADC):
    R_DIVIDER = 10.0 # constant resistor  value
    LDR_10LUX = 14.0 #  LDR  resistance   at    10    lux
    LDR_GAMMA = 0.6 # gamma  slope(log10)K

    def __int__(self, pin: str):
        super(LightSensor, self).__int__(Pin(pin, Pin.IN))

    # def getLux(self):
    #     val = self.read()
    #     resistance = 10 / (1 - 1.0 / val)
    #     print(val, resistance)
    #     return val # 10.0 * (self.LDR_10LUX / resistance) ** (1.0 / self.LDR_GAMMA)


