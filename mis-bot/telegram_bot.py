# -*- coding: utf-8 -*-
from os import environ
import logging
import textwrap
import random
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from scraper.spiders.moodle_spider import scrape_attendance
from scraper.spiders.results_spider import scrape_results

from mis_functions import bunk_lecture, until80, check_login
from scraper.database import init_db, db_session
from scraper.models import Chat

TOKEN = environ['TOKEN']
updater = Updater(TOKEN)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

#Define state
CREDENTIALS= 0

def start(bot, update):
    """Initial message sent to all users."""
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

def register(bot, update):
    """Let all users register with their credentials."""
    messageContent = textwrap.dedent("""
    Okay, send me your MIS credentials in this format:
    `Student-ID password`
    (in a single line, separated by a space)

    Use /cancel to abort.
    """)
    bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, parse_mode='markdown')
    return CREDENTIALS


def attendance(bot, job):
    """Core function. Fetch attendance figures from Aldel's MIS."""
    update = job.context
    # Get chatID and user details based on chatID
    chatID = update.message.chat_id
    if not Chat.query.filter(Chat.chatID == chatID).first():
        bot.sendMessage(chat_id=update.message.chat_id, text="📋 Unregistered! Please use /register to start.")
        return
    userChat = Chat.query.filter(Chat.chatID == chatID).first()
    Student_ID = userChat.PID
    password = userChat.password
    bot.send_chat_action(chat_id=update.message.chat_id, action='upload_photo')

    #Run AttendanceSpider
    scrape_attendance(Student_ID, password, chatID)

    try:
        bot.send_photo(chat_id=update.message.chat_id, photo=open("files/{}_attendance.png".format(Student_ID),'rb'),
                   caption='Attendance Report for {}'.format(Student_ID))
    except IOError:
        bot.sendMessage(chat_id=update.message.chat_id, text='There were some errors.')
        logger.warning("Something went wrong! Check if the Splash server is up.")

def fetch_attendance(bot, update, job_queue):
    updater.job_queue.run_once(attendance, 0, context=update)

def results(bot, job):
    '''Fetch Unit Test results from the Aldel MIS'''
    update = job.context
    # Get chatID and user details based on chatID
    chatID = update.message.chat_id
    if not Chat.query.filter(Chat.chatID == chatID).first():
        bot.sendMessage(chat_id=update.message.chat_id, text="📋 Unregistered! Please use /register to start.")
        return
    userChat = Chat.query.filter(Chat.chatID == chatID).first()
    Student_ID = userChat.PID
    password = userChat.password
    bot.send_chat_action(chat_id=update.message.chat_id, action='upload_photo')

    #Run ResultsSpider
    scrape_results(Student_ID, password)

    try:
        bot.send_photo(chat_id=update.message.chat_id, photo=open("files/{}_tests.png".format(Student_ID),'rb'),
                   caption='Test Report for {}'.format(Student_ID))
    except IOError:
        bot.sendMessage(chat_id=update.message.chat_id, text='There were some errors.')
        logger.warning("Something went wrong! Check if the Splash server is up.")

def fetch_results(bot, update, job_queue):
    updater.job_queue.run_once(results, 0, context=update)

def bunk_lec(bot, update, args):
    """Calculate drop/rise in attendance if you bunk some lectures."""
    bot.send_chat_action(chat_id=update.message.chat_id, action='typing')
    if len(args) == 2:
        r = bunk_lecture(int(args[0]), int(args[1]), update.message.chat_id)
        messageContent = 'Projected attendance = ' + str(r) + '%'
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)
    else:
        messageContent = textwrap.dedent("""
            This command expects 2 arguments.
            
            e.g: If you wish to bunk 1 out of 5 total lectures conducted today, send
            `/bunk 1 5`
            """)
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, parse_mode='markdown')

def until_eighty(bot, update):
    """Calculate number of lectures you must consecutively attend before you attendance is 80%"""
    bot.send_chat_action(chat_id=update.message.chat_id, action='typing')
    if int(until80(update.message.chat_id)) <0:
        bot.sendMessage(chat_id=update.message.chat_id, text="Your attendance is already over 80. Relax.")
    else:
        messageContent = 'No. of lectures to attend: ' + str(until80(update.message.chat_id))
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)

def credentials(bot, update):
    """Store user credentials in a database."""
    user = update.message.from_user
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

    if Chat.query.filter(Chat.chatID == chatID).first():
        bot.sendMessage(chat_id=update.message.chat_id, text="Already Registered!")
        return ConversationHandler.END

    if check_login(Student_ID, passwd) == False:
        messageContent = textwrap.dedent("""
        Looks like your credentials are incorrect! Give it one more shot.
        This is what valid login credentials look like:
        `123name4567 password`
        """)
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, parse_mode='markdown')
        return

    logger.info("New Registration! Username: %s" % (Student_ID))
    
    # Create an object of Class <Chat> and store Student_ID, password, and Telegeram
    # User ID, Add it to the database, commit it to the database. 

    userChat = Chat(PID = Student_ID, password = passwd, chatID = chatID)
    db_session.add(userChat)
    db_session.commit()

    new_user = Student_ID[3:-4].title()
    update.message.reply_text("Welcome {}!\nStart by checking your /attendance".format(new_user))
    return ConversationHandler.END

def delete(bot, update):
    """Delete a user's credentials if they wish to stop using the bot."""
    chatID = update.message.chat_id
    if not Chat.query.filter(Chat.chatID == chatID).first():
        bot.sendMessage(chat_id=update.message.chat_id, text="Unregistered!")
        return
    user_details = db_session.query(Chat).filter(Chat.chatID == chatID).first() #Pull user's username from the DB
    username = user_details.PID
    logger.info("Deleting user credentials for %s!" % (username))
    Chat.query.filter(Chat.chatID == chatID).delete() #Delete the user's record referenced by their ChatID
    db_session.commit() #Save changes
    bot.sendMessage(chat_id=update.message.chat_id, text="Your credentials have been deleted, %s\nHope to see you back soon." \
        % (username[3:-4].title()))

def cancel(bot, update):
    """Cancel registration operation."""
    bot.sendMessage(chat_id=update.message.chat_id, text="As you wish, the operation has been cancelled! 😊")
    return ConversationHandler.END

def unknown(bot, update):
    """Respond to messages incomprehensible with some canned responses."""
    can = ["Seems like I'm not programmed to understand this yet.", "I'm not a fully functional A.I. ya know?", \
    "The creator didn't prepare me for this.", "I'm not sentient...yet! 🤖", "Damn you're dumb."]
    messageContent = random.choice(can)
    bot.send_chat_action(chat_id=update.message.chat_id, action='typing')
    bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)

def help(bot, update):
    helpText = textwrap.dedent("""
    1. /register - Register yourself
    2. /attendance - Fetch attendance from the MIS website.
    3. /results - Fetch unit test results
    4. /bunk - Calculate % \drop/rise.
    `usage: /bunk x y`
    where `x = No. of lectures to bunk`
    `y = no. of lectures conducted on that day`

    5. /until80 - No. of lectures to attend consecutively until attendance is 80%
    6. /cancel - Cancel registration.
    7. /delete - Delete your credentials.
    8. /tips - Random tips.
    """)
    bot.sendMessage(chat_id=update.message.chat_id, text=helpText, parse_mode='markdown')

def tips(bot, update):
    tips = ["Always use /attendance command before using /until80 or /bunk to get latest figures.",\
    "The Aldel MIS gets updated at 6PM everyday.", "The /until80 function gives you the number of lectures you must attend *consecutively* before you attendance is 80%.",\
    "The bunk calculator's figures are subject to differ from actual values depending upon a number of factors such as:\
    \nMIS not being updated.\
    \nCancellation of lectures.\
    \nMass bunks. 😝"]
    messageContent = random.choice(tips)
    bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, parse_mode='markdown')

def main():
    """Start the bot and use long polling to detect and respond to new messages."""
    # Init Database
    init_db()
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start), CommandHandler('register', register)],

            states={
                CREDENTIALS: [MessageHandler(Filters.text, credentials)]
            },

            fallbacks=[CommandHandler('cancel', cancel)]
        )
    # Handlers
    start_handler = CommandHandler('start', start)
    attendance_handler = CommandHandler('attendance', fetch_attendance, pass_job_queue=True)
    results_handler = CommandHandler('results', fetch_results, pass_job_queue=True)
    bunk_handler = CommandHandler('bunk', bunk_lec, pass_args=True)
    eighty_handler = CommandHandler('until80', until_eighty)
    delete_handler = CommandHandler('delete', delete)
    help_handler = CommandHandler('help', help)
    tips_handler = CommandHandler('tips', tips)
    unknown_message = MessageHandler(Filters.text, unknown)

    # Dispatchers
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(delete_handler)
    dispatcher.add_handler(attendance_handler)
    dispatcher.add_handler(results_handler)
    dispatcher.add_handler(bunk_handler)
    dispatcher.add_handler(eighty_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(tips_handler)
    dispatcher.add_handler(unknown_message)

    webhook_url = 'https://%s:8443/%s'%(environ['URL'],TOKEN)

    updater.start_webhook(listen='0.0.0.0',
                      port=8443,
                      url_path=TOKEN,
                      key='files/private.key',
                      cert='files/cert.pem',
                      webhook_url=webhook_url,
                      clean=True)
    updater.idle()

if __name__ == '__main__':
    main()
