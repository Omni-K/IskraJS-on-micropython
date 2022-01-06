from time import sleep
from iskrajs import LED

p = LED('P0')
k = LED('P1')

k.on()
while True:
    sleep(1)
    p.toggle()
    k.toggle()
