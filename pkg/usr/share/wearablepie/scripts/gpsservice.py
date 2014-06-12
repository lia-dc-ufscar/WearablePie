#!/bin/python2 -tt

import sys                                               
sys.stdout = open('/tmp/wearablepie-gps.log','a');    
sys.stderr = open('/tmp/wearablepie-gps-err.log','w');

import gps
import json
import time

session = gps.gps()
session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

while(True):
	try:
		report = session.next()
		# Wait for a 'TPV' report and display the current time
		# To see all report data, uncomment the line below
		if report['class'] == 'TPV':
			print report.time,":",report
			lastpos = open('/var/wearablepie-last.json','w')
			jsonpos= json.dumps(dict(report))
			print >> lastpos, jsonpos
			lastpos.close()
			time.sleep(2)
	except KeyError:
		pass
	except KeyboardInterrupt:
		quit()
	except StopIteration:
		session = None
		print "GPSD has terminated"

