#!/bin/python2 -tt

import RPi.GPIO as GPIO
import sys

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(18, GPIO.OUT)

if len(sys.argv) == 2:
	if sys.argv[1] == '1':
		GPIO.output(18, False)
		with open("/tmp/wifi-status.log", 'a') as f:
			f.write("Connected\n")
	else:
		GPIO.output(18, True)
		with open("/tmp/wifi-status.log", 'a') as f:
			f.write("Disconnected\n")
else:
	print("Not enough fields")
