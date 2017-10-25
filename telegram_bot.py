# -*- coding: utf-8 -*-
import logging
import os
import json
import textwrap
import sys
import time
import ConfigParser
import random
from twisted.internet import reactor
from scrapy import cmdline
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, RegexHandler, ConversationHandler
from MIS.spiders.moodle_spider import MySpider
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from MIS.mis_misc_functions import bunk_lecture, until80
from database import init_db, db_session
from models import Chat

from threading import Thread
# Init Database
init_db()

# Read settings from config file
config = ConfigParser.RawConfigParser()
config.read('./MIS/spiders/creds.ini')
TOKEN = config.get('BOT', 'TOKEN')
#CHAT_ID = config.get('BOT', 'CHAT_ID')
updater = Updater(TOKEN)


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
CREDENTIALS= 0

def start(bot, update):
    #octocat= emojize("::", use_aliases=True)
    intro_message = "Hi! I'm a Telegram Bot for MIS.\
    \nMy source code lives at [Github.](https://github.com/ArionMiles/MIS-Bot)" + "👨‍💻" \
    "\nTo start using my services, please send me your MIS credentials in this format: \
    \n`PID password` \
    \n(in a single line, separated by a space)"
    bot.sendMessage(chat_id=update.message.chat_id, text=intro_message, parse_mode='markdown',\
        disable_web_page_preview=True)
    #user = update.message.from_user
    #logger.info("Credentials of %s: %s" % (user.first_name, update.message.text))
    #update.message.reply_text('Thank you! Your info is stored.')

    return CREDENTIALS

def register(bot, update):
    messageContent = "To register, send me your MIS credentials in this format: \
    \n`PID password` \
    \n(in a single line, separated by a space)"
    bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, parse_mode='markdown')
    return CREDENTIALS


def attendance(bot, update):
    # Get chatID and user details based on chatID
    #update = job.context
    chatID = update.message.chat_id
    if not Chat.query.filter(Chat.chatID == chatID).first():
        bot.sendMessage(chat_id=update.message.chat_id, text="📋 " + "Unregistered! Please use /register to start.")
        return
    userChat = Chat.query.filter(Chat.chatID == chatID).first()
    PID = userChat.PID
    password = userChat.password

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

def bunk_lec(bot, update, args):
    if len(args) == 2:
        r = bunk_lecture(int(args[0]), int(args[1]))
        messageContent = 'Projected attendance = ' + str(r) + '%'
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)
    else:
        bot.sendMessage(chat_id=update.message.chat_id, text='This command expects 2 arguments.')

def until_eighty(bot, update):
    if int(until80()) <0:
        bot.sendMessage(chat_id=update.message.chat_id, text="Your attendance is already over 80. Relax.")
    else:
        messageContent = 'No. of lectures to attend: ' + str(until80())
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)

def credentials(bot, update):
    user = update.message.from_user
    chatID = update.message.chat_id
    PID, passwd = update.message.text.split()
    
    
    if Chat.query.filter(Chat.chatID == chatID).first():
            bot.sendMessage(chat_id=update.message.chat_id, text="Already Registered!")
            return

    logger.info("Creds: Username %s , Password: %s" % (PID, passwd))
    
    # Create an object of Class <Chat> and store PID, password, and Telegeram
    # User ID, Add it to the database, commit it to the database. 

    userChat = Chat(PID  = PID, password = passwd, chatID = chatID)
    db_session.add(userChat)
    db_session.commit()

    update.message.reply_text("💾 " + "Credentials stored for user: {}!".format(userChat.PID))
    return ConversationHandler.END

def delete(bot, update):
    chatID = update.message.chat_id
    if not Chat.query.filter(Chat.chatID == chatID).first():
        bot.sendMessage(chat_id=update.message.chat_id, text="Unregistered!")
        return
    userChat = Chat.query.filter(Chat.chatID == chatID)
    userChat.delete()
    bot.sendMessage(chat_id=update.message.chat_id, text="Deleted User!")

def cancel(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text="As you wish, the operation has been cancelled! 😊")

def unknown(bot, update):
    can = ["Seems like I'm not programmed to understand this yet.", "I'm not a fully functional A.I. ya know?", \
    "The creator didn't prepare me for this.", "I'm not sentient...yet! 🤖", "I wish the creator imbued me with the ability to respond to your query.",\
     "I'm afraid I can't do that.", "Damn you're dumb.", "Please don't abuse me now that you found this."]
    messageContent = random.choice(can)
    bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)

def fetch_attendance(bot, update, job_queue):
    job_queue.run_once(attendance, 0, context=update)

def main():
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
    attendance_handler = CommandHandler('attendance', attendance)
    bunk_handler = CommandHandler('bunklecture', bunk_lec, pass_args=True)
    eighty_handler = CommandHandler('until80', until_eighty)
    delete_handler = CommandHandler('delete', delete)
    unknown_command = MessageHandler(Filters.command, unknown)
    unknown_message = MessageHandler(Filters.text, unknown)

    # Dispatchers
    #dispatcher.add_handler(start_handler)
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(delete_handler)
    dispatcher.add_handler(attendance_handler)
    dispatcher.add_handler(bunk_handler)
    dispatcher.add_handler(eighty_handler)
    #dispatcher.add_handler(unknown_command)
    dispatcher.add_handler(unknown_message)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()