from __future__ import division
from PIL import Image
from sympy.solvers import solve
from sympy import Symbol, Eq, solveset
import requests
from sqlalchemy import and_
from scraper.database import init_db, db_session
from scraper.models import Lecture, Practical
from scraper.captcha import captcha_solver

def bunk_lecture(n, tot_lec, chatID, stype, index):
    """
    Bunk calculator.

    Parameters:
    n       -- no. of lectures for a subject to bunk
    tot_lec -- total lectures conducted for that subject
    chatID  -- user's unique 9-digit ChatID from telegram
    stype   -- Lectures or Practicals
    index   -- Index of the user-selected subject from list of subjects
    """
    init_db()
    if(stype == "Lectures"):
        subject_data = Lecture.query.filter(Lecture.chatID == chatID).all()
    else:
        subject_data = Practical.query.filter(Practical.chatID == chatID).all()
    index -= 1 # DB Tables are Zero-Index 
    attended = subject_data[index].attended
    conducted = subject_data[index].conducted

    result = (((int(attended) + int(tot_lec)) -  int(n))/(int(conducted) + tot_lec)) * 100
    return round(result, 2) #Round up to 2 decimals.

def until_x(chatID, target):
    """
    Calculates the no. of lectures user must attend in order to get overall attendance to 80%

    Parameters:
    chatID -- user's unique 9-digit ChatID from telegram
    target -- attendance percentage target
    """
    init_db()
    subject_data = Lecture.query.filter(and_(Lecture.chatID == chatID, Lecture.name == "Total")).first()
    attended = subject_data.attended
    conducted = subject_data.conducted
    x = Symbol('x')
    expr = Eq((((int(attended) + x)/(int(conducted) + x))*100), target)
    soln = solveset(expr, x)
    return next(iter(soln)) # Extracting the integer from singleton set soln.

def check_login(username, password):
    """
    Checks if user input for their credentials is correct.

    Parameters:
    username -- student's PID (format: XXXNameXXXX)
                where   X - integers
    password -- student's password for student portal
    """
    base_url = 'http://report.aldel.org/student_page.php'
    with requests.session() as s:
        r = s.get(base_url)
        sessionID = str(r.cookies.get('PHPSESSID')) #Get SessionID
        captcha_answer = captcha_solver(sessionID) #Solve the CAPTCHA
        payload = {
            'studentid':username,
            'studentpwd':password,
            'captcha_code':captcha_answer,
            'student_submit':''
        }
        s.post(base_url, data=payload)
        r = s.get('http://report.aldel.org/student/attendance_report.php')
        return username in r.text

def check_parent_login(username, dob):
    """
    Checks if user input for their credentials is correct.

    Parameters:
    username -- student's PID (format: XXXNameXXXX)
                where   X - integers
    dob      -- student's date of birth (required to log into parent's portal)
    """
    base_url = 'http://report.aldel.org/parent_page.php'
    try:
        date, month, year = dob.split('/')
    except ValueError:
        return False

    with requests.session() as s:
        r = s.get(base_url)
        sessionID = str(r.cookies.get('PHPSESSID')) #Get SessionID
        captcha_answer = captcha_solver(sessionID) #Solve the CAPTCHA
        payload = {
            'studentid':username,
            'date_of_birth': date,
            'month_of_birth': month,
            'year_of_birth': year,
            'captcha_code':captcha_answer,
            'parent_submit':''
        }
        s.post(base_url, data=payload)
        r = s.get('http://report.aldel.org/student/attendance_report.php')
        return username in r.text

def crop_image(path):
    """Crop image depending upon it's size.

    Parameters:
    path -- file path
    """
    img = Image.open(path)
    w, h = img.size

    if h>800:
        new_path = path[:-4] + "_cropped.png"
        img.crop((0, h-700, w, h)).save(new_path) #crop((left, upper, right, lower))
        return True

