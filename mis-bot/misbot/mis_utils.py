from __future__ import division
import shutil

from PIL import Image
from sympy.solvers import solve
from sympy import Symbol, Eq, solveset
import requests
from sqlalchemy import and_
from securimage_solver import CaptchaApi

from scraper.database import init_db, db_session
from scraper.models import Chat, Lecture, Practical
from scraper.captcha import captcha_solver

SECURIMAGE_ENDPOINT = "http://report.aldel.org/securimage/securimage_show.php"

def bunk_lecture(n, tot_lec, chatID, stype, index):
    """Calculates % drop/rise if one chooses to bunk certain lectures. 
    
    :param n: number of lectures for a subject to bunk
    :type n: int
    :param tot_lec: total lectures conducted for that subject
    :type tot_lec: int
    :param chatID: user's unique 9-digit ChatID from telegram
    :type chatID: int | str
    :param stype: Subject type (Lectures or Practicals)
    :type stype: str
    :param index: Index of the user-selected subject from list of subjects
    :type index: int
    :return: Percentage drop/rise
    :rtype: float
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
    """Calculates the no. of lectures user must attend in order 
    to get overall attendance to their specified target.
    
    :param chatID: user's unique 9-digit ChatID from telegram
    :type chatID: int | str
    :param target: attendance percentage target
    :type target: float
    :return: Number of lectures to attend
    :rtype: int
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
    """Checks if user input for their credentials is correct
    for the student portal.
    
    :param username: student's PID (format: XXXNameXXXX)
                     where   X - integers
    :type username: str
    :param password: student's password for student portal
    :type password: str
    :return: True for correct credentials, false otherwise.
    :rtype: bool
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
    """Checks if user input for their credentials is correct
    for parent's portal.
    
    :param username: student's PID (format: XXXNameXXXX)
                     where   X - integers
    :type username: str
    :param dob: Student's Date of Birth
    :type dob: str
    :return: True for correct credentials, false otherwise.
    :rtype: bool
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
    
    :param path: image file path
    :type path: str
    :return: True for image height larger than 800px in length.
    :rtype: bool
    """
    img = Image.open(path)
    w, h = img.size

    if h>800:
        new_path = path[:-4] + "_cropped.png"
        img.crop((0, h-700, w, h)).save(new_path) #crop((left, upper, right, lower))
        return True


def get_user_info(chat_id):
    """Give user data.
    
    :param chat_id: user's unique 9-digit ChatID from telegram
    :type chat_id: str
    :return: Dictionary of all user data
    :rtype: dict
    """
    userChat = Chat.query.filter(Chat.chatID == chat_id).first()
    Student_ID = userChat.PID
    password = userChat.password
    DOB = userChat.DOB
    return {'PID': Student_ID,
            'password': password,
            'DOB': DOB}


def solve_captcha(session_id):
    """Solve captcha using securimage_solver library.
    Downloads the image from the securimage_endpoint and
    feeds it to securimage_solver lib.
    
    :param session_id: Session cookie
    :type session_id: str
    :return: Captcha answer
    :rtype: str
    """

    cookie = {'PHPSESSID': session_id}
    response = requests.get(SECURIMAGE_ENDPOINT, cookies=cookie, stream=True)
    path = "files/captcha/{}.png".format(session_id)
    if response.status_code == 200:
        with open(path, 'wb') as f:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, f)   

        c = CaptchaApi()
        captcha_answer = c.predict(path)
        return captcha_answer
