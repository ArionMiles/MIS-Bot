from __future__ import division
import json
from collections import Counter
from operator import sub
def bunk_lecture(n, tot_lec):
    with open('../attendance_output.json', 'r') as f:
        report = json.loads(f.read())
    result = (((int(report[0]['total_lec_attended']) + int(tot_lec)) -  int(n))/(int(report[0]['total_lec_conducted']) + tot_lec)) * 100
    return round(result, 2) #Round up to 2 decimals.

'''def difference():
    with open('./attendance_output.json', 'r') as f:
        d1 = json.loads(f.read())
    with open('../old_report.json', 'r') as o:
        d2 = json.loads(o.read())
    
    return d3'''

#print (difference())