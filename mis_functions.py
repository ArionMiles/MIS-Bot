from __future__ import division
import json
from collections import Counter
from operator import sub
from sympy.solvers import solve
from sympy import Symbol, Eq, solveset
def bunk_lecture(n, tot_lec):
    with open('attendance_output.json', 'r') as f:
        report = json.loads(f.read())
    result = (((int(report[0]['total_lec_attended']) + int(tot_lec)) -  int(n))/(int(report[0]['total_lec_conducted']) + tot_lec)) * 100
    return round(result, 2) #Round up to 2 decimals.

def until80():
	with open('attendance_output.json', 'r') as f:
		report = json.loads(f.read())
	x = Symbol('x')
	expr = Eq((((int(report[0]['total_lec_attended']) + x)/(int(report[0]['total_lec_conducted']) + x))*100), 80)
	soln = solveset(expr, x)
	return next(iter(soln)) # Extracting the integer from singleton set soln.
