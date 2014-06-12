#!/bin/python2 -tt

import sys                                               
sys.stdout = open('/tmp/wearablepie-gps.log','a');    
sys.stderr = open('/tmp/wearablepie-gps-err.log','w');

import gps
import json
import time

#load configuration
SleepTime = 300	#update files every 5 minutes
PushRate = 5 #Every five sleeps it will try to send the data to the server
PushCount = 0
DeviceRegistered = False
RestAPI = "catinthemap.herokuapp.com"
UserId = ""
DeviceId = ""
try:
	config = open('/etc/wearablepie/config.json','r')
	configJson =json.load(config)
	SleepTime = configJson['gps-refresh-rate']
	PushRate  = configJson['gps-push-rate']
	DeviceRegistered = configJson['registered']
	RestAPI = configJson['rest']
	UserId = configJson['user-id']
	DeviceId = configJson['device-id']
	config.close()
except Exception, e:
	print "Could not load configuration: ",e

session = gps.gps()
session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

while(True):
	try:
		report = session.next()
		# Wait for a 'TPV' report and display the current time
		if report['class'] == 'TPV':
			if time in report:
				print report.time,":",report
				lastpos = open('/var/wearablepie/last-gps.json','w')
				jsonpos= json.dumps(dict(report))
				print >> lastpos, jsonpos
				lastpos.close()
				if PushCount >= PushRate:
					PushCount = 0
					if DeviceRegistered:
						#upload data
						restPost={}
						restpost['userId']=UserId
						restpost['location']=jsonpos
						restpost['deviceId']=DeviceId
			time.sleep(SleepTime)
			PushCount += 1
			
	except KeyError:
		pass
	except KeyboardInterrupt:
		quit()
	except StopIteration:
		session = None
		print "GPSD has terminated"

