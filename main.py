from motors2wd import Motors2WD
from ir import AmperkaIRC
from led import LED
from ultrasonic import Ultrasonic
from pyb import delay
from servo import ServoFS90

ircontroller = None
moving_platform = Motors2WD()
moving_platform.reverse_motors()
head_led = LED('P2')
sonar = Ultrasonic('P9', 'P8')
head_servo = ServoFS90('A5')

head_angle = 90
speed = 100


#  Функция для пульта
def ir_callback(data, addr, ctrl):
    global speed, head_angle
    btn = ircontroller.button(data)
    print(btn)

    if btn == 'TOP':
        speed = 100
        moving_platform.forward(abs(speed))
    if btn == 'BOTTOM':
        speed = -100
        moving_platform.backward(abs(speed))
    if btn == 'PLAY':
        moving_platform.stop()
    if btn == 'GREEN':
        head_led.toggle()
    if btn == 'TOP_RIGHT':
        head_angle = head_angle + 10 if head_angle < 180 else 180
    if btn == 'TOP_LEFT':
        head_angle = head_angle - 10 if head_angle > 0 else 0


ircontroller = AmperkaIRC('P1', ir_callback)

while True:
    #print(f'Distance: {sonar.distance_in_cm()} cm')
    delay(5)
    head_servo.set_angle(head_angle)

