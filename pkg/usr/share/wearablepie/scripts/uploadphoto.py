#!/bin/python2 -tt

import sys                                               
sys.stdout = open('/tmp/wearablepie-uploadphoto.log','w',0) 
sys.stderr = open('/tmp/wearablepie-uploadphoto','w',0)

import json
import time
import requests
import RPi.GPIO as GPIO
from pyinotify import WatchManager, Notifier, EventsCodes, ProcessEvent

photoFeedback = 24 
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(photoFeedback, GPIO.OUT)

#load configuration
UploadRepeatInterval = 300	#update files every 5 minutes
PushRate = 5 #Every five sleeps it will try to send the data to the server
PushCount = 0
DeviceRegistered = False
RestAPI = "http://catinthemap.herokuapp.com"
UserId = ""
DeviceId = ""
try:
	config = open('/etc/wearablepie/config.json','r')
	configJson =json.load(config)
	UploadRepeatInterval = configJson['upload-repeat-interval']
	DeviceRegistered = configJson['registered']
	RestAPI = configJson['rest']
	UserId = configJson['user-id']
	DeviceId = configJson['device-id']
	config.close()
except Exception, e:
	print "Could not load configuration: ",e

connected = False

print("Configuration loaded: ",UploadRepeatInterval,DeviceRegistered,UserId)

#utility functions
def updatePhotosRemaining( next ):
	try:
		photosRemaining = open('/var/wearablepie/photos_remaining.json','w')
		photosRemaining.write('{"last-photo-sent": %d}'%next)
		photosRemaining.close()
	except Exception, e:
		print("Could not update file photos remaining!")
		
def getPhotosTaken():
	photosTaken = 0
	try:
		photos = open('/var/wearablepie/photos.json','r')
		photosJson = json.load(photos)
		photosTaken = photosJson['next-photo']
		photos.close()
	except Exception, e:
		print("Could not get photos taken", e)
	return photosTaken
	
def getPhotosUploaded():
	lastUploaded=0
	try:
		photosRemaining = open('/var/wearablepie/photos_remaining.json','r')
		photosRemainingJson = json.load(photosRemaining)
		lastUploaded = photosRemainingJson['last-photo-sent']
		photosRemaining.close()
	except Exception, e:
		print("Could not get photo count", e)
	return lastUploaded


#looks for photos that were not uploaded
LastPhotoUploaded=getPhotosUploaded()
PhotoCounter=getPhotosTaken() -  LastPhotoUploaded
	
def uploadPhoto(photonum):
	finalResult = True
	if DeviceRegistered:
		#upload data
		finalResult = False
		restPost={}
		url = 'http://catinthemap.herokuapp.com/geo/tag/'+UserId;
		headers = {'content-type':'application/json', 'connection': 'close'}
		oldReportFile =  open('/var/wearablepie/photos/data%d.json'%photonum,'r')
		restPost['location']=json.load(oldReportFile)
		oldReportFile.close()
		restPost['deviceId']=DeviceId
		restPost['photo']=True
		tries = 3
		while tries > 0:
			try:
				r = requests.post(url, headers=headers, data=json.dumps(restPost))
				print("Sent GPS position and photo request",r, r.text)
				if r.status_code == 200:
					url = r.json()['photoId']['url']
					files = {'file': open('/var/wearablepie/photos/photo%d.jpg'%photonum,'rb')}
					data = r.json()['photoId']['data']
					r.close()
					tries = 0
					smallTries = 3
					finalResult = True
					while smallTries > 0:
						try:
							r2 = requests.post(url, files=files,data=data)
							print("Uploaded photo",r2)
							r2.close()
							smallTries = 0
							GPIO.output(photoFeedback, True)
							time.sleep(2)
							GPIO.output(photoFeedback, False)
						except Exception, e:	
							smallTries -= 1
							print("Could not upload photo",e)
							time.sleep(2)
							continue
						
			except Exception, e:
				print("Could not send GPS position ",e)
				tries =- 1
				r.close()
				time.sleep(2)
				continue
	return finalResult

#upload photos that were not yet
if PhotoCounter > 0 and PhotoCounter < 5:
	print("Trying to upload %d photos once again"%PhotoCounter)
	while PhotoCounter > 0:
		tries = 3
		while tries > 0:
			if uploadPhoto(LastPhotoUploaded):
				tries = 0
			else:
				tries -= 1
				time.sleep(UploadRepeatInterval)
		
		PhotoCounter -= 1
		LastPhotoUploaded += 1
		updatePhotosRemaining(LastPhotoUploaded)
else:
	print("I'm not uploading these %d photos"%PhotoCounter)
	LastPhotoUploaded=getPhotosTaken()
	PhotoCounter=0
	updatePhotosRemaining(LastPhotoUploaded)
	

		
#starts the real loop
mask = EventsCodes.ALL_FLAGS['IN_CLOSE_WRITE']
wm = WatchManager()
class PCloseWrite(ProcessEvent):
	def process_IN_CLOSE_WRITE(self,event):
		print("File was modified: ",event)
		LastPhotoUploaded=getPhotosUploaded()
		PhotoCounter= getPhotosTaken() -  LastPhotoUploaded
		while PhotoCounter > 0:
			tries = 3
			while tries > 0:
				if uploadPhoto(LastPhotoUploaded):
					tries = 0
				else:
					tries -= 1
					time.sleep(UploadRepeatInterval)
		
			PhotoCounter -= 1
			LastPhotoUploaded += 1
			updatePhotosRemaining(LastPhotoUploaded)

notifier = Notifier(wm, PCloseWrite())
wdd=wm.add_watch('/var/wearablepie/photos.json',mask)
print("Started Real Loop")
while True:  # loop forever
	try:
		notifier.process_events()
		if notifier.check_events():
			notifier.read_events()

	except KeyboardInterrupt:
		print("Interrupted")
		notifier.stop()
		break
