import keyboardkeys as kb
import pyb
import machine

print(pyb.info())

for i in range(5):
    print(machine.rng())

print(dir('machine'))

pyb_dir = ['__class__',
           '__name__',
           'main',
           'stop',
           'DAC',
           'RTC',
           'ADC',
           'ADCAll', 'CAN', 'ExtInt', 'Flash', 'I2C', 'LED', 'Pin', 'SPI', 'Servo',
           'Switch', 'Timer', 'UART', 'USB_HID', 'USB_VCP',
           'bootloader', 'country', 'delay', 'dht_readinto', 'disable_irq',
           'elapsed_micros', 'elapsed_millis', 'enable_irq', 'fault_debug', 'freq', 'hard_reset',
           'have_cdc', 'hid', 'hid_keyboard', 'hid_mouse', 'info', 'micros', 'millis',
           'mount', 'pwm', 'repl_info', 'repl_uart', 'rng', 'servo', 'standby',
           'sync', 'udelay', 'unique_id', 'usb_mode', 'wfi']

pyb.usb_mode('VCP+MSC')
b = pyb.Pin('BTN1')
prev = 1
print(dir(b.board))
while True:
    curr = b.value()
    print(prev, curr)
    if curr < prev:
        print('pressed!')
        import pyb
        pyb.usb_mode('VCP+HID', hid=pyb.hid_keyboard)
        hid = pyb.USB_HID()
        buf = bytearray(8)
        buf[2] = kb.KEY_1_EXCLAMATION_MARK
        hid.send(buf)  #
        buf[2] = 0
        hid.send(buf)  #
    prev = curr
    pyb.delay(500)
    pyb.usb_mode('VCP+MSC')





