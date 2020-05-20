import RPi.GPIO as GPIO

bellpin = 10
from time import sleep

#GPIO pin numbering
GPIO.setmode(GPIO.BOARD)

GPIO.setup(bellpin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

while True:
	if GPIO.input(10) == GPIO.HIGH:
		print('bell pressed')
	else:
		print('no press')
	sleep(1)

GPIO.cleanup()
