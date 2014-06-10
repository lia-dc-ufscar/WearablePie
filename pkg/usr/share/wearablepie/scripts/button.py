import time
import picamera
import RPi.GPIO as GPIO

i = 0

GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, GPIO.PUD_UP)

photoPath = ""

while True:
   GPIO.wait_for_edge(17, GPIO.FALLING)

   with picamera.PiCamera() as camera:
      camera.start_preview()
      camera.capture('/root/python-code/image'+str(i)+'.jpg')
      i+=1
      camera.stop_preview()
