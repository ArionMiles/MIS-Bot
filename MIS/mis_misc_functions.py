from __future__ import division
import json

def bunk_lecture(n, tot_lec):
	with open('C:/Users/Kanishk/Documents/Projects/MIS Bot/MIS/attendance_output.json', 'r') as f:
		report = json.loads(f.read())
	result = (((int(report[0]['total_lec_attended']) + int(tot_lec)) -	int(n))/(int(report[0]['total_lec_conducted']) + tot_lec)) * 100
	return result

def difference(a, b):
	c = dict(set(a.items()) - set(b.items()))
	return c

#with open('C:/Users/Kanishk/Documents/Projects/MIS Bot/MIS/attendance_output.json', 'r') as f:
#	test = json.loads(f.read())
#	print (difference(test[0], test[1])) #Doesn't work