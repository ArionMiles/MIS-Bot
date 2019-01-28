# -*- coding: utf-8 -*-
import os
import logging
import textwrap
import random
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from scraper.spiders.moodle_spider import scrape_attendance
from scraper.spiders.results_spider import scrape_results
from scraper.spiders.itinerary_spider import scrape_itinerary

from mis_functions import bunk_lecture, until_x, check_login, check_parent_login, crop_image
from push_notifications import push_message_threaded, get_user_list
from scraper.database import init_db, db_session
from scraper.models import Chat, Lecture, Practical, Misc
from sqlalchemy import and_
from functools import wraps

TOKEN = os.environ['TOKEN']
updater = Updater(TOKEN)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

#Define state
CREDENTIALS, PARENT_LGN = range(2)
CHOOSING, INPUT, CALCULATING = range(3)
SET_TARGET, SELECT_YN, INPUT_TARGET = range(3)
UPDATE_TARGET = 0
NOTIF_MESSAGE, NOTIF_CONFIRM = range(2)

def signed_up(func):
    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        chatID = update.message.chat_id
        if not Chat.query.filter(Chat.chatID == chatID).first():
            bot.sendMessage(chat_id=update.message.chat_id, text="Unregistered! Use the /register command to sign up!")
            return
        return func(bot, update, *args, **kwargs)
    return wrapped


def admin(func):
    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        chatID = update.message.chat_id
        if not str(chatID) == os.environ['ADMIN_CHAT_ID']:
            messageContent = "You are not authorized to use this command. This incident has been reported."
            bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)
            user_info = Chat.query.filter(Chat.chatID == chatID).first()
            if user_info:
                logger.warning("Unauthorized Access attempt by {}".format(user_info.PID))
            else:
                logger.warning("Unauthorized Access attempt by {}".format(chatID))
            return
        return func(bot, update, *args, **kwargs)
    return wrapped


def start(bot, update):
    """
    Initial message sent to all users.
    Starts registration conversation, passes control to credentials()
    """
    intro_message = textwrap.dedent("""
    Hi! I'm a Telegram Bot for Aldel MIS.
    My source code lives at [Github.](https://github.com/ArionMiles/MIS-Bot) 👨‍💻
    To start using my services, please send me your MIS credentials in this format: 
    `Student-ID password` 
    (in a single line, separated by a space)

    Use /cancel to abort.
    Use /help to learn more.
    Join the [Channel](https://t.me/joinchat/AAAAAEzdjHzLCzMiKpUw6w) to get updates about the bot's status.
    """)
    bot.sendMessage(chat_id=update.message.chat_id, text=intro_message, parse_mode='markdown',\
        disable_web_page_preview=True)
    return CREDENTIALS

def register(bot, update, user_data):
    """
    Let all users register with their credentials.
    Similar to start() but this function can be invoked by /register command.

    If user's chatID & DOB are already present in database then ends the conversation.
    Otherwise, if only chatID is present, then stores PID(StudentID) in user_data dict &
    gives control to parent_login() function.

    If both conditions are false, then asks user to input Student details (PID & Password)
    and gives control to credentials()
    """
    init_db()
    if Chat.query.filter(Chat.chatID == update.message.chat_id).first():
        if Chat.query.filter(and_(Chat.chatID == update.message.chat_id, Chat.DOB != None)).first():
            messageContent = "Already registered!"
            bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)
            return ConversationHandler.END

        student_data = Chat.query.filter(Chat.chatID == update.message.chat_id).first()
        user_data['Student_ID'] = student_data.PID
        
        messageContent = textwrap.dedent("""
        Now enter your Date of Birth (DOB) in the following format:
        `DD/MM/YYYY`
        """)
        update.message.reply_text(messageContent, parse_mode='markdown')
        return PARENT_LGN

    messageContent = textwrap.dedent("""
    Okay, send me your MIS credentials in this format:
    `Student-ID password`
    (in a single line, separated by a space)

    Use /cancel to abort.
    """)
    bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, parse_mode='markdown')
    return CREDENTIALS

def credentials(bot, update, user_data):
    """
    Store user credentials in a database.
    Takes student info (PID & password) from update.message.text and splits it into Student_ID &
    Password and checks if they are correct with check_login() and stores them in the Chat table.
    Finally, sends message asking users to enter DOB and gives control to parent_login() after
    storing Student_ID(PID) in user_data dict.
    """
    chatID = update.message.chat_id
    #If message contains less or more than 2 arguments, send message and stop.
    try:
        Student_ID, passwd = update.message.text.split()
    except ValueError:
        messageContent = textwrap.dedent("""
        Oops, you made a mistake! 
        You must send the Student_ID and password in a single line, separated by a space.
        This is what valid login credentials look like:
        `123name4567 password`
        """)
        bot.send_chat_action(chat_id=update.message.chat_id, action='typing')
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, parse_mode='markdown')
        return

    if not check_login(Student_ID, passwd):
        messageContent = textwrap.dedent("""
        Looks like your credentials are incorrect! Give it one more shot.
        This is what valid login credentials look like:
        `123name4567 password`
        """)
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, parse_mode='markdown')
        return

    # Create an object of Class <Chat> and store Student_ID, password, and Telegeram
    # User ID, Add it to the database, commit it to the database.

    userChat = Chat(PID=Student_ID, password=passwd, chatID=chatID)
    db_session.add(userChat)
    db_session.commit()


    messageContent = textwrap.dedent("""
        Now enter your Date of Birth (DOB) in the following format:
        `DD/MM/YYYY`
        """)
    update.message.reply_text(messageContent, parse_mode='markdown')
    user_data['Student_ID'] = Student_ID
    return PARENT_LGN

def parent_login(bot, update, user_data):
    """
    user_data dict contains Student_ID key from credentials().
    Extracts DOB from update.message.text and checks validity using check_parent_login()
    before adding it to database.
    Finally, sends a message to the user requesting them to start using /attendance or
    /itinerary commands.
    """
    DOB = update.message.text
    Student_ID = user_data['Student_ID']
    chatID = update.message.chat_id

    if not check_parent_login(Student_ID, DOB):
        messageContent = textwrap.dedent("""
        Looks like your Date of Birth details are incorrect! Give it one more shot.
        Send DOB in the below format:
        `DD/MM/YYYY`
        """)
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, parse_mode='markdown')
        return
    new_user = Student_ID[3:-4].title()

    db_session.query(Chat).filter(Chat.chatID == chatID).update({'DOB': DOB})
    db_session.commit()
    logger.info("New Registration! Username: %s" % (Student_ID))

    messageContent = "Welcome {}!\nStart by checking your /attendance or /itinerary".format(new_user)
    bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, parse_mode='markdown')
    return ConversationHandler.END

def attendance(bot, job):
    """
    Core function. Fetch attendance figures from Aldel's MIS.
    Runs AttendanceSpider for registered users and passes it their Student_ID(PID),
    Password, & ChatID (necessary for AttendancePipeline)

    AttendanceSpider creates a image file of the format: <Student_ID>_attendance.png
    File is deleted after being sent to the user.
    If the file is unavailable, error message is sent to the user.
    """
    update = job.context
    # Get chatID and user details based on chatID
    chatID = update.message.chat_id
    userChat = Chat.query.filter(Chat.chatID == chatID).first()
    Student_ID = userChat.PID
    password = userChat.password
    bot.send_chat_action(chat_id=update.message.chat_id, action='upload_photo')

    #Run AttendanceSpider
    scrape_attendance(Student_ID, password, chatID)

    student_misc = Misc.query.filter(Misc.chatID == update.message.chat_id).first()

    try:
        bot.send_photo(chat_id=update.message.chat_id, photo=open("files/{}_attendance.png".format(Student_ID), 'rb'),
                       caption='Attendance Report for {}'.format(Student_ID))
        if student_misc is not None and student_misc.attendance_target is not None:
            target = student_misc.attendance_target
            no_of_lectures = int(until_x(update.message.chat_id, target))
            if no_of_lectures > 0:
                messageContent = "You need to attend {} lectures to meet your target of {}%".format(no_of_lectures, target)
                bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)

        os.remove('files/{}_attendance.png'.format(Student_ID)) #Delete saved image
    except IOError:
        bot.sendMessage(chat_id=update.message.chat_id, text='There were some errors.')
        logger.warning("Something went wrong! Check if the Splash server is up.")

@signed_up
def fetch_attendance(bot, update, job_queue):
    updater.job_queue.run_once(attendance, 0, context=update)

def results(bot, job):
    """
    Fetch Unit Test results from the Aldel MIS.
    Core function. Fetch Test Reports from Aldel's MIS.
    Runs ResultsSpider for registered users and passes it their Student_ID(PID) &
    Password.

    ResultsSpider creates a image file of the format: <Student_ID>_tests.png
    File is deleted after being sent to the user.
    If the file is unavailable, error message is sent to the user.
    """
    update = job.context
    # Get chatID and user details based on chatID
    chatID = update.message.chat_id
    userChat = Chat.query.filter(Chat.chatID == chatID).first()
    Student_ID = userChat.PID
    password = userChat.password
    bot.send_chat_action(chat_id=update.message.chat_id, action='upload_photo')

    #Run ResultsSpider
    scrape_results(Student_ID, password)

    try:
        bot.send_photo(chat_id=update.message.chat_id, photo=open("files/{}_tests.png".format(Student_ID), 'rb'),
                       caption='Test Report for {}'.format(Student_ID))
        os.remove('files/{}_tests.png'.format(Student_ID)) #Delete saved image
    except IOError:
        bot.sendMessage(chat_id=update.message.chat_id, text='There were some errors.')
        logger.warning("Something went wrong! Check if the Splash server is up.")

@signed_up
def fetch_results(bot, update, job_queue):
    updater.job_queue.run_once(results, 0, context=update)

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

    userChat = Chat.query.filter(Chat.chatID == chatID).first()
    Student_ID = userChat.PID
    DOB = userChat.DOB

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

@signed_up
def until_eighty(bot, update):
    """
    Calculate number of lectures you must consecutively attend before you attendance is 80%
    If until80() returns a negative number, attendance is already over 80%
    """
    bot.send_chat_action(chat_id=update.message.chat_id, action='typing')
    no_of_lectures = int(until_x(update.message.chat_id, 80))
    if no_of_lectures < 0:
        bot.sendMessage(chat_id=update.message.chat_id, text="Your attendance is already over 80%. Relax.")
    else:
        messageContent = "No. of lectures to attend: {}".format(no_of_lectures)
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)

@signed_up
def until(bot, update, args):
    """Like `until_eighty` but user supplies the number.

    :param bot: Telegram Bot object
    :type bot: telegram.bot.Bot
    :param update: Telegram Update object
    :type update: telegram.update.Update
    :param args: User supplied arguments
    :type args: tuple
    :return: None
    :rtype: None
    """
    if len(args) == 0:
        messageContent = textwrap.dedent("""
        You must specify a number after the command to use this feature.

        E.g: `/until 75`
        """)
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, parse_mode='markdown')
        return

    try:
        figure = float(args[0])
    except (ValueError, IndexError):
        bot.sendMessage(chat_id=update.message.chat_id, text="You must send a number between 1-99.")
        return
    
    if figure > 99:
        bot.sendMessage(chat_id=update.message.chat_id, text="You must send a number between 1-99.")
        return

    no_of_lectures = int(until_x(update.message.chat_id, figure))
    if no_of_lectures < 0:
        bot.sendMessage(chat_id=update.message.chat_id, text="Your attendance is already over {}%. Relax.".format(figure))
    else:
        messageContent = "No. of lectures to attend: {}".format(no_of_lectures)
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)

@signed_up
def attendance_target(bot, update):
    """Like `until_eighty`, but with user specified target attendance percentage
    which is stored in the Misc table.
    If target isn't set, asks users whether they'd like to and passes control to 
    `select_yn`
    
    :param bot: Telegram Bot object
    :type bot: telegram.bot.Bot
    :param update: Telegram Update object
    :type update: telegram.update.Update
    :return: SELECT_YN
    :rtype: int
    """

    bot.send_chat_action(chat_id=update.message.chat_id, action='typing')

    student_misc = Misc.query.filter(Misc.chatID == update.message.chat_id).first()
    
    if student_misc is None:
        new_misc_record = Misc(chatID=update.message.chat_id)
        db_session.add(new_misc_record)
        db_session.commit()
        logger.info("Created new Misc record for {}".format(update.message.chat_id))
        # bot.sendMessage(chat_id=update.message.chat_id, text="No records found!")
        student_misc = Misc.query.filter(Misc.chatID == update.message.chat_id).first()
    
    target = student_misc.attendance_target
    
    if target is None:

        messageContent = textwrap.dedent("""
        You have not set a target yet. Would you like to set it now?
        You can change it anytime using /edit_target
        """)
        keyboard = [['Yes'], ['No']]
        reply_markup = ReplyKeyboardMarkup(keyboard)
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, reply_markup=reply_markup)
        return SELECT_YN

    no_of_lectures = int(until_x(update.message.chat_id, target))
    if no_of_lectures < 0:
        messageContent = "Your attendance is already over {}%. Maybe set it higher? Use /edit_target to change it.".format(target)
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)
        return ConversationHandler.END
    
    messageContent = "You need to attend {} lectures to meet your target of {}%".format(no_of_lectures, target)
    bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)
    return ConversationHandler.END


def select_yn(bot, update):
    """If user replies no, ends the conversation,
    otherwise transfers control to `input_target`.
    
    :param bot: Telegram Bot object
    :type bot: telegram.bot.Bot
    :param update: Telegram Update object
    :type update: telegram.update.Update
    :return: INPUT_TARGET
    :rtype: int
    """
    reply_markup = ReplyKeyboardRemove()
    
    if update.message.text == 'No':
        messageContent = "Maybe next time!"
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, reply_markup=reply_markup)
        return ConversationHandler.END
    messageContent = textwrap.dedent("""
    Okay, give me a figure!

    e.g: If you want a target of 80%, send `80`
    """)
    bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, parse_mode='markdown', reply_markup=reply_markup)
    return INPUT_TARGET


def input_target(bot, update):
    """If the user reply is a int/float and between 1-99, stores the figure 
    as the new attendance target.
    
    :param bot: Telegram Bot object
    :type bot: telegram.bot.Bot
    :param update: Telegram Update object
    :type update: telegram.update.Update
    :return: ConversationHandler.END
    :rtype: int
    """

    try:
        target_figure = float(update.message.text)
    except ValueError:
        bot.sendMessage(chat_id=update.message.chat_id, text="You must send a number between 1-99.")
        return
    
    if target_figure > 99:
        bot.sendMessage(chat_id=update.message.chat_id, text="You must send a number between 1-99.")
        return

    db_session.query(Misc).filter(Misc.chatID == update.message.chat_id).update({'attendance_target': target_figure})
    db_session.commit()
    messageContent = "Your attendance target has been set to {}%.".format(target_figure)
    bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)
    return ConversationHandler.END

@signed_up
def edit_attendance_target(bot, update):
    """Edit existing attendance target. Shows current target and transfers
    control to `update_target`
    
    :param bot: Telegram Bot object
    :type bot: telegram.bot.Bot
    :param update: Telegram Update object
    :type update: telegram.update.Update
    :return: UPDATE_TARGET
    :rtype: int
    """    
    student_misc_model = Misc.query.filter(Misc.chatID == update.message.chat_id).first()
    messageContent = "You do not have any target records. To create one, use /target"
    if student_misc_model is None:
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)
        return ConversationHandler.END

    current_target = student_misc_model.attendance_target

    if current_target is None:
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)
        return ConversationHandler.END
    
    edit_message = textwrap.dedent("""
    Your current attendance target is {}%.
    Send a new figure to update or /cancel to cancel this operation
    """.format(current_target))

    bot.sendMessage(chat_id=update.message.chat_id, text=edit_message)
    return UPDATE_TARGET

def update_target(bot, update):
    """Takes the sent figure and sets it as new attendance target.
    
    :param bot: Telegram Bot object
    :type bot: telegram.bot.Bot
    :param update: Telegram Update object
    :type update: telegram.update.Update
    :return: ConversationHandler.END
    :rtype: int
    """

    user_reply = update.message.text

    if user_reply == '/cancel':
        bot.sendMessage(chat_id=update.message.chat_id, text="As you wish! The operation is cancelled!")
        return ConversationHandler.END
    
    try:
        new_target = int(user_reply)
    except ValueError:
        bot.sendMessage(chat_id=update.message.chat_id, text="You must send a number between 1-99.")
        return
    
    if new_target > 99:
        bot.sendMessage(chat_id=update.message.chat_id, text="You must send a number between 1-99.")
        return

    db_session.query(Misc).filter(Misc.chatID == update.message.chat_id).update({'attendance_target': new_target})
    db_session.commit()
    new_target_message = "Your attendance target has been updated to {}%!".format(new_target)
    bot.sendMessage(chat_id=update.message.chat_id, text=new_target_message)
    return ConversationHandler.END


@signed_up
def delete(bot, update):
    """
    Delete a user's credentials if they wish to stop using the bot or update them.
    """
    chatID = update.message.chat_id
    user_details = db_session.query(Chat).filter(Chat.chatID == chatID).first() #Pull user's username from the DB
    username = user_details.PID
    logger.info("Deleting user credentials for %s!" % (username))
    Chat.query.filter(Chat.chatID == chatID).delete() #Delete the user's record referenced by their ChatID
    db_session.commit() #Save changes
    bot.sendMessage(chat_id=update.message.chat_id, text="Your credentials have been deleted, %s\nHope to see you back soon." \
        % (username[3:-4].title()))

def cancel(bot, update):
    """
    Cancel registration operation (terminates conv_handler)
    """
    bot.sendMessage(chat_id=update.message.chat_id, text="As you wish, the operation has been cancelled! 😊")
    return ConversationHandler.END

def unknown(bot, update):
    """
    Respond to incomprehensible messages/commands with some canned responses.
    """
    can = ["Seems like I'm not programmed to understand this yet.", "I'm not a fully functional A.I. ya know?",
    "The creator didn't prepare me for this.", "I'm not sentient...yet! 🤖", "Damn you're dumb.", "42",
    "We cannot afford machine learning to make this bot smart!", "We don't use NLP.", "I really wish we had a neural network."]
    messageContent = random.choice(can)
    bot.send_chat_action(chat_id=update.message.chat_id, action='typing')
    bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)

def help_text(bot, update):
    """
    Display help text.
    """
    helpText = textwrap.dedent("""
    1. /register - Register yourself
    2. /attendance - Fetch attendance from the MIS website.
    3. /itinerary - Fetch detailed attendance.
    3. /results - Fetch unit test results
    4. /bunk - Calculate % \drop/rise.
    5. /until80 - No. of lectures to attend consecutively until total attendance is 80%
    6. /cancel - Cancel registration.
    7. /delete - Delete your credentials.
    8. /tips - Random tips.
    """)
    bot.sendMessage(chat_id=update.message.chat_id, text=helpText, parse_mode='markdown')

def tips(bot, update):
    """
    Send a random tip about the bot.
    """
    tips = ["Always use /attendance command before using /until80 or /bunk to get latest figures.",\
    "The Aldel MIS gets updated at 6PM everyday.", "The /until80 function gives you the number of lectures you must attend *consecutively* before you attendance is 80%.",\
    "The bunk calculator's figures are subject to differ from actual values depending upon a number of factors such as:\
    \nMIS not being updated.\
    \nCancellation of lectures.\
    \nMass bunks. 😝", "`/itinerary all` gives complete detailed attendance report since the start of semester."]
    messageContent = random.choice(tips)
    bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, parse_mode='markdown')

@signed_up
def bunk(bot, update):
    """
    Starting point of bunk_handler.
    Sends a KeyboardMarkup (https://core.telegram.org/bots#keyboards)
    Passes control to bunk_choose()
    """
    bot.send_chat_action(chat_id=update.message.chat_id, action='typing')
    keyboard = [['Lectures'], ['Practicals']]
    reply_markup = ReplyKeyboardMarkup(keyboard)
    messageContent = "Select type!"
    bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, reply_markup=reply_markup)

    return CHOOSING

def bunk_choose(bot, update, user_data):
    """
    Removes keyboardMarkup sent in previous handler.

    Stores the response (for Lectures/Practicals message sent in previous handler) in a user_data
    dictionary with the key "stype".
    user_data is a user relative dictionary which holds data between different handlers/functions
    in a ConversationHandler.

    Selects the appropriate table (Lecture or Practical) based on stype value.
    Checks if records exist in the table for a user and sends a warning message or proceeds
    to list names of all subjects in the table.

    Passes control to bunk_input()
    """
    user_data['type'] = update.message.text
    stype = user_data['type']
    reply_markup = ReplyKeyboardRemove()
    bot.sendMessage(chat_id=update.message.chat_id, text="{}".format(stype), reply_markup=reply_markup)

    if stype == "Lectures":
        subject_data = Lecture.query.filter(Lecture.chatID == update.message.chat_id).all()
    else:
        subject_data = Practical.query.filter(Practical.chatID == update.message.chat_id).all()


    if not subject_data: #If list is empty
        messageContent = textwrap.dedent("""
            No records found!
            Please use /attendance to pull your attendance from the website first.
            """)
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)
        return ConversationHandler.END

    digit = 1
    messageContent = ""

    for subject in subject_data:
        subject_name = subject.name
        messageContent += "/{digit}. {subject_name}\n".format(digit=digit, subject_name=subject_name)
        digit += 1

    bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)
    digit = 0
    return INPUT

def bunk_input(bot, update, user_data):
    """
    Stores index of the chosen subject in user_data['index'] from message.text.
    Passes control to bunk_calc()
    """
    user_data['index'] = update.message.text
    if user_data['index'] == "/cancel_bunk":
        # Terminate bunk operation since fallback commands do not work with 
        # 2 conversation handlers present for some reason
        # if you figure it out, I'll buy you coffee
        bot.sendMessage(chat_id=update.message.chat_id, text="Bunk operation cancelled! 😊")
        return ConversationHandler.END


    messageContent = textwrap.dedent("""
        Send number of lectures you wish to bunk and total lectures conducted for that subject on that day,
        separated by a space.

        e.g: If you wish to bunk 1 out of 5 lectures (total or per subject) conducted today, send
        `1 5`
        """)
    bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, parse_mode='markdown')
    return CALCULATING

def bunk_calc(bot, update, user_data):
    """
    user_data keys: type, index, figures.

    """
    user_data['figures'] = update.message.text
    stype = user_data['type']
    try:
        index = int(user_data['index'].split('/')[1])
    except ValueError:
        return ConversationHandler.END
    args = user_data['figures'].split(' ')

    bot.send_chat_action(chat_id=update.message.chat_id, action='typing')

    if len(args) == 2:
        current = bunk_lecture(0, 0, update.message.chat_id, stype, index)
        predicted = bunk_lecture(int(args[0]), int(args[1]), update.message.chat_id, stype, index)
        no_bunk = bunk_lecture(0, int(args[1]), update.message.chat_id, stype, index)
        loss = round((current - predicted), 2)
        gain = round((no_bunk - current), 2)

        messageContent = textwrap.dedent("""
            Current: {current}
            Predicted: {predicted}
            If you attend: {no_bunk}

            Loss: {loss}
            Gain: {gain}

            If you wish to check for another subject, select their number from above or press /cancel_bunk to cancel
            this operation.
            """).format(current=current, predicted=predicted, no_bunk=no_bunk, loss=loss, gain=gain)
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)
        return INPUT
    else:
        messageContent = textwrap.dedent("""
            This command expects 2 arguments.
            
            e.g: If you wish to bunk 1 out of 5 total lectures conducted today, send
            `1 5`
            """)
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, parse_mode='markdown')
        return
    return ConversationHandler.END

@admin
def push_notification(bot, update):
    """Starts Push notification conversation. Asks for message.
    
    :param bot: Telegram Bot object
    :type bot: telegram.bot.Bot
    :param update: Telegram Update object
    :type update: telegram.update.Update
    :return: NOTIF_MESSAGE
    :rtype: int
    """

    bot.sendMessage(chat_id=update.message.chat_id, text="Send me the text")
    return NOTIF_MESSAGE


def notification_message(bot, update, user_data):
    """Ask for confirmation, stores the message in `user_data`,
    transfer control to :py:func:`notification_confirm`
    
    :param bot: Telegram Bot object
    :type bot: telegram.bot.Bot
    :param update: Telegram Update object
    :type update: telegram.update.Update
    :param user_data: User data dictionary
    :type user_data: dict
    :return: NOTIF_CONFIRM
    :rtype: int
    """


    user_data['notif_message']= update.message.text
    keyboard = [['Yes'], ['No']]
    reply_markup = ReplyKeyboardMarkup(keyboard)
    messageContent = "This message will be sent to {} users. Requesting confirmation...".format(len(get_user_list()))
    bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, reply_markup=reply_markup)
    return NOTIF_CONFIRM


def notification_confirm(bot, update, user_data):
    """Sends message if "Yes" is sent. Aborts if "No" is sent.
    Sends a message with statistics like users reached, time taken after sending
    push notification.
    
    :param bot: Telegram Bot object
    :type bot: telegram.bot.Bot
    :param update: Telegram Update object
    :type update: telegram.update.Update
    :param user_data: User data dictionary
    :type user_data: dict
    :return: ConversationHandler.END
    :rtype: int
    """

    reply_markup = ReplyKeyboardRemove()
    if update.message.text == "Yes":
        users = get_user_list()
        bot.sendMessage(chat_id=update.message.chat_id, text="Sending push message...", reply_markup=reply_markup)
        time_taken = push_message_threaded(user_data['notif_message'], users)
        stats_message = "Sent to {} users in {:.2f}secs".format(len(users), time_taken)
        bot.sendMessage(chat_id=update.message.chat_id, text=stats_message)
        return ConversationHandler.END
    elif update.message.text == "No":
        bot.sendMessage(chat_id=update.message.chat_id, text="Aborted!", reply_markup=reply_markup)
        return ConversationHandler.END
    return

def main():
    """Start the bot and use webhook to detect and respond to new messages."""
    init_db()
    dispatcher = updater.dispatcher

    # Handlers
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CommandHandler('register', register, pass_user_data=True)],

        states={
            CREDENTIALS: [MessageHandler(Filters.text, credentials, pass_user_data=True)],
            PARENT_LGN: [MessageHandler(Filters.text, parent_login, pass_user_data=True)]
            },

        fallbacks=[CommandHandler('cancel', cancel)]
        )

    bunk_handler = ConversationHandler(
        entry_points=[CommandHandler('bunk', bunk)],

        states={
            CHOOSING: [MessageHandler(Filters.text | Filters.command, bunk_choose, pass_user_data=True)],
            INPUT: [MessageHandler(Filters.command | Filters.command, bunk_input, pass_user_data=True)],
            CALCULATING: [MessageHandler(Filters.text | Filters.command, bunk_calc, pass_user_data=True)]
            },

        fallbacks=[CommandHandler('cancel', cancel)]
        )

    attendance_target_handler = ConversationHandler(
        entry_points=[CommandHandler('target', attendance_target)],
        states={
            SELECT_YN: [MessageHandler(Filters.text, select_yn)],
            INPUT_TARGET: [MessageHandler(Filters.text, input_target)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    edit_attendance_target_handler = ConversationHandler(
        entry_points=[CommandHandler('edit_target', edit_attendance_target)],
        states={
            UPDATE_TARGET: [MessageHandler(Filters.text | Filters.command, update_target)],
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    push_notification_handler = ConversationHandler(
        entry_points=[CommandHandler('push', push_notification)],
        
        states={
            NOTIF_MESSAGE: [MessageHandler(Filters.text, notification_message, pass_user_data=True)],
            NOTIF_CONFIRM: [MessageHandler(Filters.text, notification_confirm, pass_user_data=True)],
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    attendance_handler = CommandHandler('attendance', fetch_attendance, pass_job_queue=True)
    results_handler = CommandHandler('results', fetch_results, pass_job_queue=True)
    itinerary_handler = CommandHandler('itinerary', itinerary, pass_args=True)
    eighty_handler = CommandHandler('until80', until_eighty)
    until_handler = CommandHandler('until', until, pass_args=True)
    delete_handler = CommandHandler('delete', delete)
    help_handler = CommandHandler('help', help_text)
    tips_handler = CommandHandler('tips', tips)
    unknown_message = MessageHandler(Filters.text | Filters.command, unknown)

    # Dispatchers
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(delete_handler)
    dispatcher.add_handler(attendance_handler)
    dispatcher.add_handler(results_handler)
    dispatcher.add_handler(itinerary_handler)
    dispatcher.add_handler(bunk_handler)
    dispatcher.add_handler(eighty_handler)
    dispatcher.add_handler(until_handler)
    dispatcher.add_handler(attendance_target_handler)
    dispatcher.add_handler(edit_attendance_target_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(tips_handler)
    dispatcher.add_handler(push_notification_handler)
    dispatcher.add_handler(unknown_message)

    if DEBUG:
        updater.start_polling(clean=True)
        updater.idle()
    else:
        webhook_url = 'https://%s:8443/%s'%(os.environ['URL'], TOKEN)
        updater.start_webhook(listen='0.0.0.0',
                            port=8443,
                            url_path=TOKEN,
                            key='files/private.key',
                            cert='files/cert.pem',
                            webhook_url=webhook_url,
                            clean=True)
        updater.idle()

if __name__ == '__main__':
    DEBUG = False # Do not have this variable as True in production
    main()
