import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BOARD)
GPIO.setup(37, GPIO.OUT)

while True:
	GPIO.output(37, 1)
	print('on')
	sleep(2)
	GPIO.output(37, 0)
	print('off')
	sleep(2)

GPIO.cleanup()