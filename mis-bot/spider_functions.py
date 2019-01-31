import logging
import os

from sqlalchemy import and_

from decorators import signed_up
from mis_utils import until_x, crop_image, get_user_info
from scraper.spiders.moodle_spider import scrape_attendance
from scraper.spiders.results_spider import scrape_results
from scraper.spiders.itinerary_spider import scrape_itinerary
from scraper.database import init_db, db_session
from scraper.models import Chat, Misc

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

def attendance(bot, job):
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
    update = job.context
    # Get chatID and user details based on chatID
    chatID = update.message.chat_id
    user_info = get_user_info(chatID)
    Student_ID = user_info['PID']
    password = user_info['password']
    bot.send_chat_action(chat_id=update.message.chat_id, action='upload_photo')

    #Run AttendanceSpider
    scrape_attendance(Student_ID, password, chatID)

    student_misc = Misc.query.filter(Misc.chatID == chatID).first()

    try:
        bot.send_photo(chat_id=update.message.chat_id, photo=open("files/{}_attendance.png".format(Student_ID), 'rb'),
                       caption='Attendance Report for {}'.format(Student_ID))
        if student_misc is not None and student_misc.attendance_target is not None:
            target = student_misc.attendance_target
            no_of_lectures = int(until_x(chatID, target))
            if no_of_lectures > 0:
                messageContent = "You need to attend {} lectures to meet your target of {}%".format(no_of_lectures, target)
                bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)

        os.remove('files/{}_attendance.png'.format(Student_ID)) #Delete saved image
    except IOError:
        bot.sendMessage(chat_id=update.message.chat_id, text='There were some errors.')
        logger.warning("Something went wrong! Check if the Splash server is up.")

def results(bot, job):
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
    update = job.context
    # Get chatID and user details based on chatID
    chatID = update.message.chat_id
    user_info = get_user_info(chatID)
    Student_ID = user_info['PID']
    password = user_info['password']
    bot.send_chat_action(chat_id=chatID, action='upload_photo')

    #Run ResultsSpider
    scrape_results(Student_ID, password)

    try:
        bot.send_photo(chat_id=update.message.chat_id, photo=open("files/{}_tests.png".format(Student_ID), 'rb'),
                       caption='Test Report for {}'.format(Student_ID))
        os.remove('files/{}_tests.png'.format(Student_ID)) #Delete saved image
    except IOError:
        bot.sendMessage(chat_id=chatID, text='There were some errors.')
        logger.warning("Something went wrong! Check if the Splash server is up.")


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
        bot.sendMessage(chat_id=update.message.chat_id, text="📋 Unregistered! Please use /register to start.")
        return

    user_info = get_user_info(chatID)
    Student_ID = user_info['PID']
    DOB = user_info['DOB']

    if args:
        bot.send_chat_action(chat_id=update.message.chat_id, action='upload_document')
    else:
        bot.send_chat_action(chat_id=update.message.chat_id, action='upload_photo')

    #Run ItinerarySpider
    scrape_itinerary(Student_ID, DOB)

    try:
        with open("files/{}_itinerary.png".format(Student_ID), "rb") as f:
            pass
    except IOError:
        bot.sendMessage(chat_id=update.message.chat_id, text='There were some errors.')
        logger.warning("Something went wrong! Check if the Splash server is up.")
        return

    if args:
        #arguments supplied, sending full screenshot
        bot.send_document(chat_id=update.message.chat_id, document=open("files/{}_itinerary.png".format(Student_ID), 'rb'),
                          caption='Full Itinerary Report for {}'.format(Student_ID))
        os.remove('files/{}_itinerary.png'.format(Student_ID)) #Delete original downloaded image
        return

    if crop_image("files/{}_itinerary.png".format(Student_ID)):
        #greater than 800px. cropping and sending..
        bot.send_photo(chat_id=update.message.chat_id, photo=open("files/{}_itinerary_cropped.png".format(Student_ID), 'rb'),
                       caption='Itinerary Report for {}'.format(Student_ID))
        os.remove('files/{}_itinerary_cropped.png'.format(Student_ID)) #Delete cropped image
        os.remove('files/{}_itinerary.png'.format(Student_ID)) #Delete original downloaded image
    else:
        #less than 800px, sending as it is..
        bot.send_photo(chat_id=update.message.chat_id, photo=open("files/{}_itinerary.png".format(Student_ID), 'rb'),
                       caption='Itinerary Report for {}'.format(Student_ID))
        os.remove('files/{}_itinerary.png'.format(Student_ID)) #Delete original downloaded image
