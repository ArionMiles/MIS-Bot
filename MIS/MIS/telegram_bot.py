from scrapy import cmdline
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, RegexHandler
import logging
import os
import ConfigParser
import json
import textwrap
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


#from testspiders.spiders.followall import FollowAllSpider

# Read settings from config file
config = ConfigParser.RawConfigParser()
config.read('C:/Users/Kanishk/Documents/Projects/MIS Bot/MIS/MIS/spiders/creds.ini')
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

# Real stuff
def start(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text="Hi! I'm a telegram Bot for MIS")

def attendance(bot, update):
    process = CrawlerProcess(get_project_settings())
    # 'followall' is the name of one of the spiders of the project.
    process.crawl('mis')
    process.start()
    #cmdline.execute("scrapy crawl mis".split())
    with open("C:/Users/Kanishk/Documents/Projects/MIS Bot/MIS/attendance2.json", 'r') as file:
        contents = file.read()
        a_r = json.loads(contents)

        for i in a_r:
                AM = i['AM']
                AP = i['AP']
                AC = i['AC']
                EM = i['EM']
                BEE = i['BEE']
                EVS = i['EVS']
                Overall = i['Overall']
        message_template = textwrap.dedent("""
                AM: {AM}
                AP: {AP}
                AC: {AC}
                EM: {EM}
                BEE: {BEE}
                EVS: {EVS}
                Overall: {Overall}
                """)
        messageContent = message_template.format(AM=AM, AP=AP,
                                             AC=AC, EM=EM, 
                                             BEE=BEE, EVS=EVS,
                                             Overall=Overall)
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)


def unknown(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text="Sorry, I didn't get that.")


# Handlers
start_handler = CommandHandler('start', start)
attendance_handler = CommandHandler('attendance', attendance)
unknown_handler = MessageHandler(Filters.command, unknown)
unknown_message = MessageHandler(Filters.text, unknown)

# Dispatchers
dispatcher.add_handler(start_handler)
dispatcher.add_handler(attendance_handler)
dispatcher.add_handler(unknown_handler)
dispatcher.add_handler(unknown_message)

updater.start_polling()
updater.idle()