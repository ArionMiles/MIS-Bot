from __future__ import division
import json

def bunk_overall(n, tot_lec):
	with open('C:/Users/Kanishk/Documents/Projects/MIS Bot/MIS/attendance_output.json', 'r') as f:
		report = json.loads(f.read())
	result = (((int(report[0]['total_lec_attended']) + int(tot_lec)) -	int(n))/(int(report[0]['total_lec_conducted']) + tot_lec)) * 100
	#result = float(((int(91) + int(tot_lec)) - int(n))/(int(130) + int(tot_lec)) * 100)
	print result
	return result

bunk_overall(1,5)

def difference(a, b):
	c = dict(set(a.items()) - set(b.items()))
	return c