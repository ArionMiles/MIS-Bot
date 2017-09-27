import logging
import os
import ConfigParser
import json
import textwrap
import sys
import time
from twisted.internet import reactor
from scrapy import cmdline
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, RegexHandler
from MIS.spiders.moodle_spider import MySpider
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from MIS.mis_misc_functions import bunk_lecture

# Read settings from config file
config = ConfigParser.RawConfigParser()
config.read('MIS/spiders/creds.ini')
TOKEN = config.get('BOT', 'TOKEN')
#APP_NAME = config.get('BOT', 'APP_NAME')
#PORT = int(os.environ.get('PORT', '5000'))
updater = Updater(TOKEN)

# Setting Webhook
#updater.start_webhook(listen="0.0.0.0",
#                      port=PORT,
#                      url_path=TOKEN)
#updater.bot.setWebhook(APP_NAME + TOKEN)

logging.basicConfig(format='%(asctime)s -# %(name)s - %(levelname)s - %(message)s',level=logging.INFO)

dispatcher = updater.dispatcher

def start(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text="Hi! I'm a telegram Bot for MIS")

def attendance(bot, update):
    #Empty the previous report contents
    with open('attendance_output.json', 'w') as att:
        pass

    configure_logging({'LOG_FORMAT': '%(levelname)s: %(message)s'})
    runner = CrawlerRunner({
        'FEED_FORMAT': 'json',
        'FEED_URI' : 'attendance_output.json'
        })

    d = runner.crawl(MySpider)
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
                EM: {EM_prac}
                BEE: {BEE_prac}
                Workshop: {Workshop}
                Overall: {Overall_prac}
                """)
        messageContent = message_template.format(AM=AM, AP=AP,
                                             AC=AC, EM=EM, 
                                             BEE=BEE, EVS=EVS,
                                             Overall=Overall, AM_prac=AM_prac,
                                             AC_prac=AC_prac,
                                             EM_prac=EM_prac, BEE_prac=BEE_prac,
                                             Workshop=Workshop, Overall_prac=Overall_prac)

    bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)

    #Write contents of current report to old_report.json for difference() function
    with open('old_report.json', 'w') as old:
        json.dump(a_r, old, indent=4)

    #Restart the bot to counter ReactorNotRestartable error.
    time.sleep(0.2)
    os.execl(sys.executable, sys.executable, *sys.argv)

def bunk_lec(bot, update, args):
    r = bunk_lecture(int(args[0]), int(args[1]))
    messageContent = 'Projected attendance = ' + str(r) + '%'

    bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)

def unknown(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text="Sorry, I didn't get that.")


# Handlers
start_handler = CommandHandler('start', start)
attendance_handler = CommandHandler('attendance', attendance)
args_handler = CommandHandler('bunklecture', bunk_lec, pass_args=True)
unknown_handler = MessageHandler(Filters.command, unknown)
unknown_message = MessageHandler(Filters.text, unknown)

# Dispatchers
dispatcher.add_handler(start_handler)
dispatcher.add_handler(attendance_handler)
dispatcher.add_handler(args_handler)
dispatcher.add_handler(unknown_handler)
dispatcher.add_handler(unknown_message)

updater.start_polling()
updater.idle()
