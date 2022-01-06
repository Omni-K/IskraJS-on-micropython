from time import sleep
from pyb import ADC
from machine import Pin

s = ADC(Pin('A5'))
e = ADC(Pin('A4'))

led = Pin('P1', Pin.OUT)
led2 = Pin('P0', Pin.OUT)
led_t = 0
led2_t = 0

while True:
    sound_val = s.read()
    noise_val = e.read()
    print('Sound:', int(sound_val), '\tNoise:', int(noise_val), '\tLED fade tick: ', led_t, '\t',
          led2_t)

    # LED1
    if led_t > 0:
        led.high()
        led_t -= 1
    else:
        led.low()

    if noise_val >= 250:
        led_t = 100

    # LED2
    if led2_t > 0:
        led2.high()
        led2_t -= 1
    else:
        led2.low()

    if noise_val >= 1500:
        led2_t = 100

    sleep(0.02)
