from time import sleep
from ultrasonic import Ultrasonic
from led import LED

led = LED('P0')
sonic = Ultrasonic(echo_pin='P10', trigger_pin='P12')

while True:
    led.value(int(sonic.distance_in_cm() <= 15))
    sleep(0.3)