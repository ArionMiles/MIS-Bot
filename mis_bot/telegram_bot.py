# -*- coding: utf-8 -*-
import os
import logging
import textwrap
import random

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from dotenv import load_dotenv
load_dotenv(verbose=True)

from misbot.admin import push_notification, notification_message, notification_confirm, revert_notification, \
ask_uuid, confirm_revert, clean_all_attendance_records
from misbot.attendance_target import attendance_target, select_yn, input_target, edit_attendance_target, update_target
from misbot.bunk import bunk, bunk_choose, bunk_input, bunk_calc
from misbot.decorators import signed_up, admin
from misbot.general import start, register, credentials, parent_login, delete, cancel, unknown, help_text, tips
from misbot.mis_utils import bunk_lecture, until_x, check_login, check_parent_login, crop_image
from misbot.push_notifications import push_message_threaded, get_user_list, delete_threaded
from misbot.spider_functions import attendance, results, itinerary
from misbot.states import *
from misbot.until_func import until, until_eighty

from scraper.database import db_session
from scraper.models import Chat, Lecture, Practical, Misc, PushNotification, PushMessage

TOKEN = os.environ['TOKEN']
updater = Updater(TOKEN)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

def main():
    """Start the bot and use webhook to detect and respond to new messages."""
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

    delete_notification_handler = ConversationHandler(
        entry_points=[CommandHandler('revert', revert_notification)],
        
        states={
            ASK_UUID: [MessageHandler(Filters.text, ask_uuid, pass_user_data=True)],
            CONFIRM_REVERT: [MessageHandler(Filters.text | Filters.command, confirm_revert, pass_user_data=True)],
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    clean_records_handler = CommandHandler('clean', clean_all_attendance_records)

    attendance_handler = CommandHandler('attendance', attendance)
    results_handler = CommandHandler('results', results)
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
    dispatcher.add_handler(delete_notification_handler)
    dispatcher.add_handler(clean_records_handler)
    dispatcher.add_handler(unknown_message)

    if DEBUG:
        updater.start_polling(clean=True)
        updater.idle()
    else:
        webhook_url = 'https://{0}:8443/{1}'.format(os.environ['URL'], TOKEN)
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
