from __future__ import division
from sympy.solvers import solve
from sympy import Symbol, Eq, solveset
import requests

from scraper.database import init_db, db_session
from scraper.models import Attendance

def bunk_lecture(n, tot_lec, chatID):
    '''Bunk calculator'''
    init_db()
    record = db_session.query(Attendance).filter(Attendance.chatID == chatID).first()
    attended = record.total_lec_attended
    conducted = record.total_lec_conducted
    result = (((int(attended) + int(tot_lec)) -  int(n))/(int(conducted) + tot_lec)) * 100
    return round(result, 2) #Round up to 2 decimals.

def until80(chatID):
    '''Calculates the no. of lectures user must attend in order to get attendance to 80%'''
    init_db()
    record = db_session.query(Attendance).filter(Attendance.chatID == chatID).first()
    attended = record.total_lec_attended
    conducted = record.total_lec_conducted
    x = Symbol('x')
    expr = Eq((((int(attended) + x)/(int(conducted) + x))*100), 80)
    soln = solveset(expr, x)
    return next(iter(soln)) # Extracting the integer from singleton set soln.

def check_login(username, password):
    '''Checks if user input for their credentials is correct.'''
    base_url = 'http://report.aldel.org/student_page.php'
    payload = {
        'studentid':username,
        'studentpwd':password,
        'student_submit':''
        }
    with requests.session() as s:
        s.post(base_url, data=payload)
        r = s.get('http://report.aldel.org/student/attendance_report.php')
        if username in r.text:
            return True
        else:
            return False
