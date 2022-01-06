from pyb import Timer
from time import sleep
from machine import Pin


class LED(Pin):
    is_on = False

    def __init__(self, id):
        super().__init__(id, Pin.OUT)

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


class PWM():
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


# led1 = LED('P0')
p = LED('P1')

while True:
    sleep(1)
    p.on()
    sleep(1)
    p.off()

# from time import sleep
# from pyb import ADC
# from machine import Pin
#
# s = ADC(Pin('A5'))
# e = ADC(Pin('A4'))
#
# led = Pin('P1', Pin.OUT)
# led2 = Pin('P0', Pin.OUT)
# led_t = 0
# led2_t = 0
#
# while True:
#     sound_val = s.read()
#     noise_val = e.read()
#     print('Sound:', int(sound_val), '\tNoise:', int(noise_val), '\tLED fade tick: ', led_t, '\t',
#           led2_t)
#
#     # LED1
#     if led_t > 0:
#         led.high()
#         led_t -= 1
#     else:
#         led.low()
#
#     if noise_val >= 250:
#         led_t = 100
#
#     # LED2
#     if led2_t > 0:
#         led2.high()
#         led2_t -= 1
#     else:
#         led2.low()
#
#     if noise_val >= 1500:
#         led2_t = 100
#
#     sleep(0.02)
