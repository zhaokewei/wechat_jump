# -*- coding:utf-8 -*-
import socket
import time
import RPi.GPIO as gpio
import atexit

#gpio
servo_pin = 17
atexit.register(gpio.cleanup)
gpio.setmode(gpio.BCM)
gpio.setup(servo_pin, gpio.OUT, initial=False)
p = gpio.PWM(servo_pin, 50)
p.start(0)
time.sleep(6)


#socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(("0.0.0.0", 9999))
s.listen(3)

servo_down = 80
servo_up = 65


def press(t_ms):
    p.ChangeDutyCycle(2.5 + servo_down*10/180)
    time.sleep(0.02)
    time.sleep(t_ms)
    p.ChangeDutyCycle(2.5 + servo_up*10/180)
    time.sleep(1)
    p.ChangeDutyCycle(0)


def main():
    while True:
        sock, addr = s.accept()
        t_ms = sock.recv(1024)
        t_ms = t_ms.decode("utf-8")
        print("press %s ms" % t_ms)
        press(float(t_ms)/1000)


if __name__ == '__main__':
    main()
