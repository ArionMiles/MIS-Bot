# -*- coding: utf-8 -*-
import logging
import os
import json
import textwrap
import sys
import ConfigParser
import random
from twisted.internet import reactor
from scrapy import cmdline
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from MIS.spiders.moodle_spider import MySpider
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from threading import Thread

from mis_functions import bunk_lecture, until80
from database import init_db, db_session
from models import Chat

# Read settings from config file
config = ConfigParser.RawConfigParser()
config.read('creds.ini')
TOKEN = config.get('BOT', 'TOKEN')
updater = Updater(TOKEN)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

#Define state
CREDENTIALS= 0

def start(bot, update):
    """Initial message sent to all users."""
    intro_message = "Hi! I'm a Telegram Bot for MIS.\
    \nMy source code lives at [Github.](https://github.com/ArionMiles/MIS-Bot)" + "👨‍💻" \
    "\nTo start using my services, please send me your MIS credentials in this format: \
    \n\n`PID password` \
    \n(in a single line, separated by a space)\
    \n\nUse /cancel to abort.\
    \nUse /help to learn more."
    bot.sendMessage(chat_id=update.message.chat_id, text=intro_message, parse_mode='markdown',\
        disable_web_page_preview=True)

    return CREDENTIALS

def register(bot, update):
    """Let all users register with their credentials."""
    messageContent = "Okay, send me your MIS credentials in this format: \
    \n`PID password` \
    \n(in a single line, separated by a space)\
    \n\nUse /cancel to abort."
    bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, parse_mode='markdown')
    return CREDENTIALS


def attendance(bot, job):
    """Core function. Fetch attendance figures from Aldel's MIS."""
    update = job.context
    # Get chatID and user details based on chatID
    chatID = update.message.chat_id
    if not Chat.query.filter(Chat.chatID == chatID).first():
        bot.sendMessage(chat_id=update.message.chat_id, text="📋 " + "Unregistered! Please use /register to start.")
        return
    userChat = Chat.query.filter(Chat.chatID == chatID).first()
    PID = userChat.PID
    password = userChat.password
    bot.send_chat_action(chat_id=update.message.chat_id, action='typing')

    #Empty the previous report contents
    with open('attendance_output.json', 'w') as att:
        pass

    configure_logging({'LOG_FORMAT': '%(levelname)s: %(message)s'})
    runner = CrawlerRunner({
        'FEED_FORMAT': 'json',
        'FEED_URI' : 'attendance_output.json'
        })

    d = runner.crawl(MySpider, USERNAME=PID, PASSWORD=password)
    d.addBoth(lambda _: reactor.stop())
    reactor.run(installSignalHandlers=0)

    with open("attendance_output.json", 'r') as file:
        contents = file.read()
        a_r = json.loads(contents)
        AM = a_r[0]['AM']
        AP = a_r[0]['AP']
        AC = a_r[0]['AC']
        EM = a_r[0]['EM']
        BEE = a_r[0]['BEE']
        EVS = a_r[0]['EVS']
        Overall = a_r[0]['Overall']
        #Practicals
        AM_prac = a_r[1]['AM_prac']
        #AP_prac = a_r[1]['AP_prac']
        AC_prac = a_r[1]['AC_prac']
        AP_prac = a_r[1]['AP_prac']
        EM_prac = a_r[1]['EM_prac']
        BEE_prac = a_r[1]['BEE_prac']
        Workshop = a_r[1]['Workshop']
        Overall_prac= a_r[1]['Overall_prac']
        message_template = textwrap.dedent("""
                LECTURES:
                AM: {AM}
                AP: {AP}
                AC: {AC}
                EM: {EM}
                BEE: {BEE}
                EVS: {EVS}
                Overall: {Overall}

                PRACTICALS:
                AM: {AM_prac}
                AC: {AC_prac}
                AP: {AP_prac}
                EM: {EM_prac}
                BEE: {BEE_prac}
                Workshop: {Workshop}
                {Overall_prac}
                """)
        messageContent = message_template.format(AM=AM, AP=AP,
                                             AC=AC, EM=EM, 
                                             BEE=BEE, EVS=EVS,
                                             Overall=Overall, AM_prac=AM_prac,
                                             AC_prac=AC_prac, AP_prac=AP_prac,
                                             EM_prac=EM_prac, BEE_prac=BEE_prac,
                                             Workshop=Workshop, Overall_prac=Overall_prac)

    bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)

    #Write contents of current report to old_report.json for difference() function
    with open('old_report.json', 'w') as old:
        json.dump(a_r, old, indent=4)

    #Restart the bot to counter ReactorNotRestartable error.
    def stop_and_restart():
        """Gracefully stop the Updater and replace the current process with a new one"""
        updater.stop()
        os.execl(sys.executable, sys.executable, *sys.argv)
    Thread(target=stop_and_restart).start()

def fetch_attendance(bot, update, job_queue):
    updater.job_queue.run_once(attendance, 0, context=update)

def bunk_lec(bot, update, args):
    """Calculate drop/rise in attendance if you bunk some lectures."""
    bot.send_chat_action(chat_id=update.message.chat_id, action='typing')
    if len(args) == 2:
        r = bunk_lecture(int(args[0]), int(args[1]))
        messageContent = 'Projected attendance = ' + str(r) + '%'
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)
    else:
        bot.sendMessage(chat_id=update.message.chat_id, text='This command expects 2 arguments.\nUse /help \
            to learn how to use this command.')

def until_eighty(bot, update):
    """Calculate number of lectures you must consecutively attend before you attendance is 80%"""
    bot.send_chat_action(chat_id=update.message.chat_id, action='typing')
    if int(until80()) <0:
        bot.sendMessage(chat_id=update.message.chat_id, text="Your attendance is already over 80. Relax.")
    else:
        messageContent = 'No. of lectures to attend: ' + str(until80())
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)

def credentials(bot, update):
    """Store user credentials in a database."""
    user = update.message.from_user
    chatID = update.message.chat_id
    #If message contains less or more than 2 arguments, send message and stop. 
    try:
        PID, passwd = update.message.text.split()
    except ValueError:
        update.message.reply_text("Oops, you made a mistake! You must send the PID and password\
            in a single line, separated by a space.")
        return

    if Chat.query.filter(Chat.chatID == chatID).first():
            bot.sendMessage(chat_id=update.message.chat_id, text="Already Registered!")
            return ConversationHandler.END

    logger.info("Creds: Username %s , Password: %s" % (PID, passwd))
    
    # Create an object of Class <Chat> and store PID, password, and Telegeram
    # User ID, Add it to the database, commit it to the database. 

    userChat = Chat(PID  = PID, password = passwd, chatID = chatID)
    db_session.add(userChat)
    db_session.commit()

    update.message.reply_text("💾 " + "Credentials stored for user: {}!".format(userChat.PID))
    return ConversationHandler.END

def delete(bot, update):
    """Delete a user's credentials if they wish to stop using the bot."""
    chatID = update.message.chat_id
    if not Chat.query.filter(Chat.chatID == chatID).first():
        bot.sendMessage(chat_id=update.message.chat_id, text="Unregistered!")
        return
    userChat = Chat.query.filter(Chat.chatID == chatID)
    userChat.delete()
    bot.sendMessage(chat_id=update.message.chat_id, text="Deleted User!")

def cancel(bot, update):
    """Cancel registration operation."""
    bot.sendMessage(chat_id=update.message.chat_id, text="As you wish, the operation has been cancelled! 😊")
    return ConversationHandler.END

def unknown(bot, update):
    """Respond to messages incomprehensible with some canned responses."""
    can = ["Seems like I'm not programmed to understand this yet.", "I'm not a fully functional A.I. ya know?", \
    "The creator didn't prepare me for this.", "I'm not sentient...yet! 🤖", "I wish the creator imbued me with the ability to respond to your query.",\
     "I'm afraid I can't do that.", "Damn you're dumb.", "Please don't abuse me now that you found this."]
    messageContent = random.choice(can)
    bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)

def help(bot, update):
    helpText = "1. /register - Register yourself\
                \n2. /attendance - Fetch attendance from the MIS website.\
                \n3. /bunk - Calculate % drop/rise.\
                \n`usage: /bunk x y`\
                \nwhere `x = No. of lectures to bunk` \n`y = no. of lectures conducted on that day`\
                \n4. /until80 - No. of lectures to attend consecutively until attendance is 80%\
                \n5. /cancel - Cancel registration.\
                \n6. /delete - Delete your credentials."
    bot.sendMessage(chat_id=update.message.chat_id, text=helpText, parse_mode='markdown')

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
    bunk_handler = CommandHandler('bunk', bunk_lec, pass_args=True)
    eighty_handler = CommandHandler('until80', until_eighty)
    delete_handler = CommandHandler('delete', delete)
    help_handler = CommandHandler('help', help)
    unknown_message = MessageHandler(Filters.text, unknown)

    # Dispatchers
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(delete_handler)
    dispatcher.add_handler(attendance_handler)
    dispatcher.add_handler(bunk_handler)
    dispatcher.add_handler(eighty_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(unknown_message)

    #Long polling
    updater.start_polling(clean=True)
    updater.idle()

if __name__ == '__main__':
    main()
