#!/bin/python2 -tt

import sys                                               
sys.stdout = open('/tmp/wearablepie-gps.log','w',0) 
sys.stderr = open('/tmp/wearablepie-gps-err.log','w',0)

print("Starting GPS Daemon")

import gps
import json
import time
import subprocess
import requests
import RPi.GPIO as GPIO

#setup system date
import datetime
import os

GetGPSSystemDate=False
if datetime.date.today().year < 1980:
	print("System date has an odd value: ",datetime.date.today().year)
	GetGPSSystemDate=True
	print("Setting it up to 2014-08-13T12:33:43.000Z")
	os.system("date --set '2014-08-13T12:33:43.000Z'")


#load configuration
PushRate = 300 #Every x iterations it will try to send the data to the server, if the fix is lost it will send data immediately after recovering it
PushCount = 0
DeviceRegistered = False
RestAPI = "catinthemap.herokuapp.com"
UserId = ""
DeviceId = ""

try:
	config = open('/etc/wearablepie/config.json','r')
	configJson =json.load(config)
	PushRate  = configJson['gps-push-rate']
	DeviceRegistered = configJson['registered']
	RestAPI = configJson['rest']
	UserId = configJson['user-id']
	DeviceId = configJson['device-id']
	config.close()
except Exception, e:
	print "Could not load configuration: ",e

session = None
connected = False

print("Configuration loaded: ",PushRate,DeviceRegistered,UserId)
		
while not connected:
	try:
		session = gps.gps()
		session.stream(gps.WATCH_ENABLE)
		connected = True
	except Exception, e:
		print("Could not connect to the GPS module: ", e)
		subprocess.call(["/bin/gpsd", "/dev/ttyAMA0"])
		time.sleep(2)

print("Connected to GPS Daemon")

#Feedback
fix = False
feedbackON = False
gpsFeedback = 25

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(gpsFeedback, GPIO.OUT)

def getFix():
	global report
	for satellite in report['satellites']:
		if (satellite['used'] == True):
			return True
	return False

while(True):
	try:
		report = session.next()
		if report['class'] == 'SKY':
			fix = getFix()
		if not fix:
			if not feedbackON:
				#turn led on
				GPIO.output(gpsFeedback, True)
				print("No Fix ")
				feedbackON = True

			if PushCount < PushRate:
				PushCount = PushRate
		else:
			if feedbackON:
				#turn led off
				GPIO.output(gpsFeedback, False)
				print("Fix")
				feedbackON = False
			# Wait for a 'TPV' report and display the current time
			if report['class'] == 'TPV':
				if 'time' in report:
					if (GetGPSSystemDate):
						GetGPSSystemDate = False
						os.system("date --set '%s'"%report.time)
					lastpos = open('/var/wearablepie/last-gps.json','w')
					jsonpos= json.dumps(dict(report))
					print >> lastpos, jsonpos
					lastpos.close()
					if PushCount >= PushRate:
						GpsLog.flush() #force data write for GpsLog
						PushCount = 0
						if DeviceRegistered:
							#upload data
							restPost={}
							url = 'http://catinthemap.herokuapp.com/geo/tag/'+UserId;
							headers = {'content-type':'application/json', 'connection':'close'}
							restPost['location']=dict(report)
							restPost['deviceId']=DeviceId
							tries = 3
							while tries > 0:
								try:
									r = requests.post(url, headers=headers, data=json.dumps(restPost))
									print("Sent GPS position:",r)
									if r.status_code == 200:
										r.close()
										tries = 0
								except Exception, e:
									print("Could not send GPS position ",e)
									r.close()
									time.sleep(2)
									tries =- 1
				PushCount += 1
	except KeyError:
		print("KeyError")
		pass
	except KeyboardInterrupt:
		print("Interrupted by Keyboard")
		quit()
	except StopIteration:
		print("Reached StopIteration")
		session = gps.gps()
		session.stream(gps.WATCH_ENABLE)
		continue
