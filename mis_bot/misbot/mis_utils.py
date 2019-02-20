from __future__ import division
import shutil
from datetime import datetime, timedelta
import random

from PIL import Image
from sympy.solvers import solve
from sympy import Symbol, Eq, solveset
import requests
from sqlalchemy import and_
from securimage_solver import CaptchaApi

from scraper.database import db_session
from scraper.models import Chat, Lecture, Practical, RateLimit

SECURIMAGE_ENDPOINT = "http://report.aldel.org/securimage/securimage_show.php"

list_of_gifs = ["https://media.giphy.com/media/uSJF1fS5c3fQA/giphy.gif",
                "https://media.giphy.com/media/lRmjNrQZkKVuE/giphy.gif",
                "https://media.giphy.com/media/1zSz5MVw4zKg0/giphy.gif",
                "https://media.giphy.com/media/jWOLrt5JSNyXS/giphy.gif",
                "https://media.giphy.com/media/27tE5WpzjK0QEEm0WC/giphy.gif",
                "https://media.giphy.com/media/46itMIe0bkQeY/giphy.gif",
                "https://i.imgur.com/CoWZ05t.gif",
                "https://media.giphy.com/media/48YKCwrp4Kt8I/giphy.gif"]

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
        session_id = str(r.cookies.get('PHPSESSID')) #Get SessionID
        captcha_answer = solve_captcha(session_id) #Solve the CAPTCHA
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
    :param dob: User's Date of Birth
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
        session_id = str(r.cookies.get('PHPSESSID')) #Get SessionID
        captcha_answer = solve_captcha(session_id) #Solve the CAPTCHA
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
    """Crop image if the image height is > 800px.
    
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


def clean_attendance_records():
    """Delete all lectures and practical records from the DB.
    To be used at the beginning of a new semester so that ``/bunk`` command
    doesn't display lectures of previous semester(s).
    
    :return: Number of records deleted from Lecture and Practical tables.
    :rtype: tuple
    """
    lecture_records = db_session.query(Lecture).delete()
    practical_records = db_session.query(Practical).delete()
    db_session.commit()
    return lecture_records, practical_records


def get_user_info(chat_id):
    """Give user data.
    
    :param chat_id: 9-Digit unique user ID
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
    """Solve captcha using ``securimage_solver`` library.
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


def rate_limited(bot, chat_id, command):
    """Checks if user has made a request in the past 5 minutes.
    
    :param bot: Telegram Bot object
    :type bot: telegram.bot.Bot
    :param chat_id: 9-Digit unique user ID
    :type chat_id: str
    :param command: Telegram command
    :type command: str
    :return: True if user has made a request in past 5 mins, else False
    :rtype: bool
    """
    rate_limit = RateLimit.query.filter(and_(RateLimit.chatID == chat_id, RateLimit.command == command)).first()

    if rate_limit is None:
        new_rate_limit_record = RateLimit(chatID=chat_id, status='new', command=command, count=0)
        db_session.add(new_rate_limit_record)
        db_session.commit()
        rate_limit = RateLimit.query.filter(and_(RateLimit.chatID == chat_id, RateLimit.command == command)).first()

    if abs(datetime.now() - rate_limit.requested_at) < timedelta(minutes=5):
        if rate_limit.count < 1:
            RateLimit.query.filter(and_(RateLimit.chatID == chat_id, RateLimit.command == command))\
                           .update({'count': rate_limit.count + 1})
            db_session.commit()
            return False
        elif rate_limit.count < 2:
            RateLimit.query.filter(and_(RateLimit.chatID == chat_id, RateLimit.command == command))\
                           .update({'count': rate_limit.count + 1})
            db_session.commit()
            message_content = "You've already requested attendance in the past 5 minutes. Please wait 5 minutes before sending another request."
            bot.send_message(chat_id=chat_id, text=message_content)
            return True

        elif rate_limit.count in range(2, 1000):
            RateLimit.query.filter(and_(RateLimit.chatID == chat_id, RateLimit.command == command))\
                           .update({'count': rate_limit.count + 1})
            db_session.commit()
            bot.send_animation(chat_id=chat_id, animation=random.choice(list_of_gifs))
            return True
    else:
        RateLimit.query.filter(and_(RateLimit.chatID == chat_id, RateLimit.command == command))\
                       .update({'count': 1, 'requested_at': datetime.now()})
        db_session.commit()
        return False