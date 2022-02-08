from pyb import Timer
from machine import Pin
from machine import time_pulse_us
from utime import sleep_us
from typing import overload


class LED(Pin):
    is_on = False

    def __init__(self, pid):
        super().__init__(pid, Pin.OUT)

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


class Ultrasonic:
    """
    Driver to use the untrasonic sensor HC-SR04.
    The sensor range is between 2cm and 4m.

    The timeouts received listening to echo pin are converted to OSError('Out of range')

    """
    # echo_timeout_us is based in chip range limit (400cm)
    def __init__(self, trigger_pin, echo_pin, echo_timeout_us=500*2*30):
        """
        trigger_pin: Output pin to send pulses
        echo_pin: Readonly pin to measure the distance. The pin should be protected with 1k resistor
        echo_timeout_us: Timeout in microseconds to listen to echo pin.
        By default is based in sensor limit range (4m)
        """
        self.echo_timeout_us = echo_timeout_us
        # Init trigger pin (out)
        self.trigger = Pin(trigger_pin, mode=Pin.OUT, pull=None)
        self.trigger.value(0)

        # Init echo pin (in)
        self.echo = Pin(echo_pin, mode=Pin.IN, pull=None)

    def _send_pulse_and_wait(self):
        """
        Send the pulse to trigger and listen on echo pin.
        We use the method `machine.time_pulse_us()`
        to get the microseconds until the echo is received.
        """
        self.trigger.value(0)  # Stabilize the sensor
        sleep_us(5)
        self.trigger.value(1)
        # Send a 10us pulse.
        sleep_us(10)
        self.trigger.value(0)
        try:
            pulse_time = time_pulse_us(self.echo, 1, self.echo_timeout_us)
            # time_pulse_us returns -2 if there was timeout waiting for condition;
            # and -1 if there was timeout during the main measurement.
            # It DOES NOT raise an exception
            # ...as of MicroPython 1.17:
            # http://docs.micropython.org/en/v1.17/library/machine.html#machine.time_pulse_us
            if pulse_time < 0:
                MAX_RANGE_IN_CM = 500
                # it's really ~400 but I've read people say they see it working up to ~460
                pulse_time = int(MAX_RANGE_IN_CM * 29.1)  # 1cm each 29.1us
            return pulse_time
        except OSError as ex:
            if ex.args[0] == 110:  # 110 = ETIMEDOUT
                raise OSError('Out of range')
            raise ex

    def distance_mm(self):
        """
        Get the distance in milimeters without floating point operations.
        """
        pulse_time = self._send_pulse_and_wait()

        # To calculate the distance we get the pulse_time and divide it by 2
        # (the pulse walk the distance twice) and by 29.1 becasue
        # the sound speed on air (343.2 m/s), that It's equivalent to
        # 0.34320 mm/us that is 1mm each 2.91us
        # pulse_time // 2 // 2.91 -> pulse_time // 5.82 -> pulse_time * 100 // 582
        mm = pulse_time * 100 // 582
        return mm

    def distance_cm(self):
        """
        Get the distance in centimeters with floating point operations.
        It returns a float
        """
        pulse_time = self._send_pulse_and_wait()

        # To calculate the distance we get the pulse_time and divide it by 2
        # (the pulse walk the distance twice) and by 29.1 becasue
        # the sound speed on air (343.2 m/s), that It's equivalent to
        # 0.034320 cm/us that is 1cm each 29.1us
        cms = (pulse_time / 2) / 29.1
        return cms


class MicroservoFS90(PWM):
    _angle = 0
    maxDuty = 9000
    minDuty = 1000
    duty = 1000

    @overload
    def angle(self):
        return self._angle

    @overload
    def angle(self, angle: int) -> None:
        if angle > 180: self._angle = 180
        if angle < 0: self._angle = 0
        self.duty(self._angle / 180)



