from sys import platform
import time
import gc
from machine import Pin, freq
# Import all implemented classes
import ir
import led

figure = ''
# ir_rx __init__.py Decoder for IR remote control using synchronous code
# IR_RX abstract base class for IR receivers.

# Author: Peter Hinch
# Copyright Peter Hinch 2020-2021 Released under the MIT license

from machine import Timer, Pin
from array import array
from utime import ticks_us, ticks_diff


# Save RAM
# from micropython import alloc_emergency_exception_buf
# alloc_emergency_exception_buf(100)


# On 1st edge start a block timer. While the timer is running, record the time
# of each edge. When the timer times out decode the data. Duration must exceed
# the worst case block transmission time, but be less than the interval between
# a block start and a repeat code start (~108ms depending on protocol)

class IR_RX():
    # Result/error codes
    # Repeat button code
    REPEAT = -1
    # Error codes
    BADSTART = -2
    BADBLOCK = -3
    BADREP = -4
    OVERRUN = -5
    BADDATA = -6
    BADADDR = -7

    def __init__(self, pin, nedges, tblock, callback, *args):  # Optional args for callback
        self._pin = pin
        self._nedges = nedges
        self._tblock = tblock
        self.callback = callback
        self.args = args
        self._errf = lambda _: None
        self.verbose = False

        self._times = array('i', (0 for _ in range(nedges + 1)))  # +1 for overrun
        pin.irq(handler=self._cb_pin, trigger=(Pin.IRQ_FALLING | Pin.IRQ_RISING))
        self.edge = 0
        self.tim = Timer(-1)  # Sofware timer
        self.cb = self.decode

    # Pin interrupt. Save time of each edge for later decode.
    def _cb_pin(self, line):
        t = ticks_us()
        # On overrun ignore pulses until software timer times out
        if self.edge <= self._nedges:  # Allow 1 extra pulse to record overrun
            if not self.edge:  # First edge received
                self.tim.init(period=self._tblock, mode=Timer.ONE_SHOT, callback=self.cb)
            self._times[self.edge] = t
            self.edge += 1

    def do_callback(self, cmd, addr, ext, thresh=0):
        self.edge = 0
        if cmd >= thresh:
            self.callback(cmd, addr, ext, *self.args)
        else:
            self._errf(cmd)

    def error_function(self, func):
        self._errf = func

    def close(self):
        self._pin.irq(handler=None)
        self.tim.deinit()


class NEC_ABC(IR_RX):
    def __init__(self, pin, extended, callback, *args):
        # Block lasts <= 80ms (extended mode) and has 68 edges
        super().__init__(pin, 68, 80, callback, *args)
        self._extended = extended
        self._addr = 0

    def decode(self, _):
        try:
            if self.edge > 68:
                raise RuntimeError(self.OVERRUN)
            width = ticks_diff(self._times[1], self._times[0])
            if width < 4000:  # 9ms leading mark for all valid data
                raise RuntimeError(self.BADSTART)
            width = ticks_diff(self._times[2], self._times[1])
            if width > 3000:  # 4.5ms space for normal data
                if self.edge < 68:  # Haven't received the correct number of edges
                    raise RuntimeError(self.BADBLOCK)
                # Time spaces only (marks are always 562.5µs)
                # Space is 1.6875ms (1) or 562.5µs (0)
                # Skip last bit which is always 1
                val = 0
                for edge in range(3, 68 - 2, 2):
                    val >>= 1
                    if ticks_diff(self._times[edge + 1], self._times[edge]) > 1120:
                        val |= 0x80000000
            elif width > 1700:  # 2.5ms space for a repeat code. Should have exactly 4 edges.
                raise RuntimeError(self.REPEAT if self.edge == 4 else self.BADREP)  # Treat REPEAT as error.
            else:
                raise RuntimeError(self.BADSTART)
            addr = val & 0xff  # 8 bit addr
            cmd = (val >> 16) & 0xff
            if cmd != (val >> 24) ^ 0xff:
                raise RuntimeError(self.BADDATA)
            if addr != ((val >> 8) ^ 0xff) & 0xff:  # 8 bit addr doesn't match check
                if not self._extended:
                    raise RuntimeError(self.BADADDR)
                addr |= val & 0xff00  # pass assumed 16 bit address to callback
            self._addr = addr
        except RuntimeError as e:
            cmd = e.args[0]
            addr = self._addr if cmd == self.REPEAT else 0  # REPEAT uses last address
        # Set up for new data burst and run user callback
        self.do_callback(cmd, addr, 0, self.REPEAT)


class AmperkaIRC(NEC_ABC):
    ir_remote_controller_btns = ['RED',
                                 'BLUE',
                                 'TRIANGLE',
                                 'GREEN',
                                 'BOTTOM_RIGHT',
                                 'SQUARE',
                                 'TOP',
                                 'MINUS',
                                 'LEFT',
                                 'CROSS',
                                 'TOP_LEFT',
                                 'POWER',
                                 'X',
                                 'Y',
                                 'Z',  # 14
                                 'not predefined 15',
                                 'not predefined 16',
                                 'not predefined 17',
                                 'not predefined 18',
                                 'not predefined 19',
                                 'not predefined 20',
                                 'not predefined 21',
                                 'not predefined 22',
                                 'not predefined 23',
                                 'BOTTOM_LEFT',
                                 'RIGHT',
                                 'TOP_RIGHT',
                                 'PLUS',
                                 'PLAY',
                                 'BOTTOM',
                                 'not predefined 30',
                                 'not predefined 31',
                                 'repeat',
                                 ]

    def __init__(self, pin: str, callback, *args):
        super().__init__(Pin(pin, Pin.IN), True, callback, *args)

    def button(self, code: int) -> str:
        """
        Возвращает текстовое название кнопки
        """
        name = self.ir_remote_controller_btns[code]
        self.ir_remote_controller_btns[-1] = name
        return name


irc = None


def cb(data, addr, ctrl):
    global figure
    btn = irc.button(data)
    print(btn)
    if data < 0:  # NEC protocol sends repeat codes.
        print('Repeat code.')
    else:
        # print('Data {:02x} Addr {:04x} Ctrl {:02x}'.format(data, addr, ctrl))
        if btn == 'POWER':
            led.toggle()
        if btn == 'RED':
            figure = 'Red mode'
        if btn == 'GREEN':
            figure = 'green mode'
        if btn == 'BLUE':
            figure = 'BLUE mode'


led = led.LED('P0')
irc = AmperkaIRC('P3', cb)

while True:
    print(figure)
    time.sleep(5)
    gc.collect()

"""
POWER — включить / выключить,   Data 0b Addr 9168 Ctrl 00
MINUS — минус,                  Data 07 Addr 9168 Ctrl 00
PLUS — плюс,                    Data 1b Addr 9168 Ctrl 00
RED — красный,                  Data 00 Addr 9168 Ctrl 00
GREEN — зелёный,                Data 03 Addr 9168 Ctrl 00
BLUE — синий,                   Data 01 Addr 9168 Ctrl 00
CROSS — крест,  09
SQUARE — квадрат,  05
TRIANGLE — треугольник,  02
TOP_LEFT — вверх влево,  0a
TOP — вверх,           06
TOP_RIGHT — вверх вправо, 1a
LEFT — влево, 08
PLAY — воспроизвести / пауза, 1c
RIGHT — вправо, 19
BOTTOM_LEFT — вниз влево, 18
BOTTOM — вниз, 1d
BOTTOM_RIGHT — вниз вправо,04
X — X, 0c
Y — Y, 0d
Z — Z 0e
"""


