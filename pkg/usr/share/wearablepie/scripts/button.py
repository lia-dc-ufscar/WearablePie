#!/bin/python3 -tt


import sys
sys.stdout = open('/tmp/wearablepie-button.log','w');
sys.stderr = open('/tmp/wearablepie-button-err.log','w');

import time
import json
import picamera
import shutil
import RPi.GPIO as GPIO

#load configuration
PhotoCounter=0
configJson = json.loads('{"next-photo":0}')
try:
	config = open('/var/wearablepie/photos.json','r')
	configJson = json.load(config)
	PhotoCounter = configJson['next-photo']
	config.close()
except :
	print("Could not load configuration")

GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, GPIO.PUD_UP)

while True:
	GPIO.wait_for_edge(17, GPIO.FALLING)
	
	with picamera.PiCamera() as camera:
		#save photo
		try:
			camera.start_preview()
			camera.capture('/var/wearablepie/photos/photo%d.jpg'%PhotoCounter)
			camera.stop_preview()
			shutil.copy2('/var/wearablepie/last-gps.json', '/var/wearablepie/photos/data'+str(PhotoCounter)+'.json')
			PhotoCounter+=1
			nextphoto = open('/var/wearablepie/photos.json','w')
			jsonphoto= json.dumps({"next-photo":PhotoCounter})
			nextphoto.write(jsonphoto)
			nextphoto.close()
			
		except:
			print("Could not take photo/save gps date")
