#!/bin/python2 -tt


import sys 
#sys.stdout = open('/tmp/wearablepie-button.log','w');
#sys.stderr = open('/tmp/wearablepie-button-err.log','w');

from subprocess import Popen, PIPE
import json
import picamera
import shutil
import os
import RPi.GPIO as GPIO

def decodeFields(string):
	dictionary = {}
	if not string:
		raise ValueError
	pairs = string.split(',')
	for p in pairs:
		key,value = p.split(':')
		if key not in ('Security', 'ESSID', 'Key', 'User'): 
			raise ValueError
		dictionary[key] = value
	print("QR Code fields = "+str(dictionary))
	return dictionary

def createProfile(f, fields):
	f.write("Description='Profile for network " + fields['ESSID'] + "'\n")
	f.write("Interface=wlan0\n")
	f.write("Connection=wireless\n")
	f.write("Security="+fields['Security']+"\n")
	f.write("IP=dhcp\n")
	f.write("ESSID='"+fields['ESSID']+"'\n")
	if (fields['Security']!='none'): 
		f.write("Key='"+fields['Key']+"'\n")

#load configuration
PhotoCounter=0
configJson = json.loads('{"next-photo":0}')
try:
	config = open('/var/wearablepie/photos.json','r')
	configJson = json.load(config)
	PhotoCounter = configJson['next-photo']
	config.close()
except Exception, e:
	print("Could not load configuration: ", e)

def savePhoto():
	global PhotoCounter
	try:
		shutil.copy2('/var/wearablepie/last-gps.json', '/var/wearablepie/photos/data'+str(PhotoCounter)+'.json')
		PhotoCounter+=1
		nextphoto = open('/var/wearablepie/photos.json','w')
		jsonphoto= json.dumps({"next-photo":PhotoCounter})
		nextphoto.write(jsonphoto)
		nextphoto.close()
	except Exception, e:
		print("Could not save gps data: ", e)

button = 17
qrcodeFeedback = 23

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(button, GPIO.IN, GPIO.PUD_DOWN)
GPIO.setwarnings(False)
GPIO.setup(qrcodeFeedback, GPIO.OUT)

while True:
	GPIO.wait_for_edge(button, GPIO.FALLING)
	
	with picamera.PiCamera() as camera:
		#save photo
		try:
			path = '/var/wearablepie/photos/photo'+str(PhotoCounter)+'.jpg'
			print("Taking picture")
			camera.start_preview()
			camera.capture(path)
			camera.stop_preview()
			print("Picture taken")
		except:
			print("Could not take photo")

		p = Popen(["zbarimg", "-q", path], stdout=PIPE)
		print("Searching for QRCode.")
		output = p.communicate()[0]

		if not p.returncode:
			print("QR code detected")
			try:
				fields = decodeFields(str(output)[8:-1])
			except:
				print("QRCode invalid")
				savePhoto()
				continue

			GPIO.output(qrcodeFeedback, True)
		
			with open('/etc/wearablepie/config.json', 'r') as config:
				configJson = json.load(config)
				configJson['user-id'] = fields['User']
				configJson['registered'] = True

			with open('/etc/wearablepie/config.json', 'w') as config:
				config.write(json.dumps(configJson))

			with open('/etc/netctl/'+fields['ESSID'], 'w') as profile:
				createProfile(profile, fields)
			print("Profile "+fields['ESSID']+" created")
			os.system("systemctl stop netctl-auto@wlan0.service")
			os.system("systemctl start netctl-auto@wlan0.service")
			print("netctl-auto restarted")

			os.system("rm "+path)
			print("Photo "+path+" removed")
			GPIO.output(qrcodeFeedback, False)
		else:
			print("No QR code found")
			savePhoto()

