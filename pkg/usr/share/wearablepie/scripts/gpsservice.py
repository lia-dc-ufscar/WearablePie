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

#setup system date
import datetime
import os
GetGPSSystemDate=False
if datetime.date.today().year < 1980:
	print("System date has an odd value: ",datetime.date.today().year)
	GetGPSSystemDate=True
	print("Setting it up to 2014-06-14T12:33:43.000Z")
	os.system("date --set '2014-06-14T12:33:43.000Z'")


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

connected = False
session = None

print("Configuration loaded: ",SleepTime,PushRate,DeviceRegistered,UserId)


while(not connected):
	try:
		session = gps.gps()
		session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)
		connected = True
	except Exception, e:
		print("Could not connect to the GPS module: ",e)
		subprocess.call(['/bin/gpsd', '/dev/ttyAMA0'])
		time.sleep(2)
		
#open gps log
GpsLog = open("/var/wearablepie/gps.log","a")

print("Connected to GPS Dameon")

while(True):
	try:
		report = session.next()
		# Wait for a 'TPV' report and display the current time
		if report['class'] == 'TPV':
			if 'time' in report:
				if (GetGPSSystemDate):
					GetGPSSystemDate = False
					print("Setting up system date")
					os.system("date --set '%s'"%report.time)
				GpsLog.write("%s %s\n"%(report.time,report))
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
						headers = {'content-type':'application/json'}
						restPost['location']=dict(report)
						restPost['deviceId']=DeviceId
						tries = 3
						while tries > 0:
							try:
								r = requests.post(url, headers=headers, data=json.dumps(restPost))
								print("Sent GPS position:",r)
								if r.status_code == 200:
									tries = 0
							except Exception, e:
								print("Could not send GPS position ",e)
								time.sleep(2)
								tries =- 1
			time.sleep(SleepTime)
			PushCount += 1
			
	except KeyError:
		pass
	except KeyboardInterrupt:
		print("Interrupted by Keyboard")
		GpsLog.close()
		quit()
	except StopIteration:
		print("Reached StopIteration")
		time.sleep(5)
		session = gps.gps()
		session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)


