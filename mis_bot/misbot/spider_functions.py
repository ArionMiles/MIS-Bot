import logging
import os

from sqlalchemy import and_

from scraper.spiders.attendance_spider import scrape_attendance
from scraper.spiders.results_spider import scrape_results
from scraper.spiders.itinerary_spider import scrape_itinerary
from scraper.database import init_db, db_session
from scraper.models import Chat, Misc
from misbot.decorators import signed_up
from misbot.mis_utils import until_x, crop_image, get_user_info

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

@signed_up
def attendance(bot, update):
    """Core function. Fetch attendance figures from Aldel's MIS.
    Runs AttendanceSpider for registered users and passes it their Student_ID(PID),
    Password, & ChatID (necessary for AttendancePipeline)

    AttendanceSpider creates a image file of the format: <Student_ID>_attendance.png
    File is deleted after being sent to the user.
    If the file is unavailable, error message is sent to the user.
    
    :param bot: Telegram Bot object
    :type bot: telegram.bot.Bot
    :param job: Telegram Job object
    :type job: telegram.ext.Job
    """
    # Get chatID and user details based on chatID
    chatID = update.message.chat_id
    user_info = get_user_info(chatID)
    Student_ID = user_info['PID']
    password = user_info['password']
    bot.send_chat_action(chat_id=update.message.chat_id, action='upload_photo')

    #Run AttendanceSpider
    scrape_attendance(Student_ID, password, chatID)


@signed_up
def results(bot, update):
    """
    Fetch Unit Test results from the Aldel MIS.
    Core function. Fetch Test Reports from Aldel's MIS.
    Runs ResultsSpider for registered users and passes it their Student_ID(PID) &
    Password.

    ResultsSpider creates a image file of the format: <Student_ID>_tests.png
    File is deleted after being sent to the user.
    If the file is unavailable, error message is sent to the user.
    
    :param bot: Telegram Bot object
    :type bot: telegram.bot.Bot
    :param job: Telegram Job object
    :type job: telegram.ext.Job
    """
    # Get chatID and user details based on chatID
    chatID = update.message.chat_id
    user_info = get_user_info(chatID)
    Student_ID = user_info['PID']
    password = user_info['password']
    bot.send_chat_action(chat_id=chatID, action='upload_photo')

    #Run ResultsSpider
    scrape_results(Student_ID, password, chatID)


@signed_up
def itinerary(bot, update, args):
    """
    Core function. Fetch detailed attendance reports from Aldel's MIS (Parent's Portal).
    Runs ItinerarySpider for registered users and passes it their Student_ID(PID) &
    Password.

    AttendanceSpider creates a image file of the format: <Student_ID>_itinerary.png
    If args are present, full report is sent in the form of a document. Otherwise, it
    is cropped to the past 7 days using crop_image() and this function stores the
    resultant image as: <Student_ID>_itinerary_cropped.png and returns True.

    File is deleted after sent to the user.
    If the file is unavailable, error message is sent to the user.
    """
    chatID = update.message.chat_id

    #If registered, but DOB is absent from the DB
    if Chat.query.filter(and_(Chat.chatID == chatID, Chat.DOB == None)).first():
        bot.sendMessage(chat_id=update.message.chat_id, text="📋 Your DOB is missing! Please use /register to start.")
        return

    user_info = get_user_info(chatID)
    Student_ID = user_info['PID']
    DOB = user_info['DOB']

    if args:
        bot.send_chat_action(chat_id=update.message.chat_id, action='upload_document')
        scrape_itinerary(Student_ID, DOB, chatID, uncropped=True)
    else:
        bot.send_chat_action(chat_id=update.message.chat_id, action='upload_photo')
        scrape_itinerary(Student_ID, DOB, chatID)    
