# -*- coding: utf-8 -*-
import os
import logging

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from dotenv import load_dotenv

load_dotenv(verbose=True)

from misbot.admin import (push_notification, notification_message, notification_confirm, revert_notification,
                        ask_uuid, confirm_revert, clean_all_attendance_records, make_premium, ask_username,
                        confirm_user, input_tier, input_validity, confirm_otp, extend_premium, extend_ask_username,
                        extend_confirm_user, extend_input_days, admin_commands_list)
from misbot.attendance_target import attendance_target, select_yn, input_target, edit_attendance_target, update_target
from misbot.bunk import bunk, bunk_choose, bunk_input, bunk_calc
from misbot.decorators import signed_up, admin
from misbot.general import (start, register, credentials, parent_login, delete, cancel, unknown, help_text, 
                            tips, error_callback, subscription)
from misbot.mis_utils import bunk_lecture, until_x, check_login, check_parent_login, crop_image
from misbot.push_notifications import push_message_threaded, get_user_list, delete_threaded
from misbot.spider_functions import attendance, results, itinerary, profile
from misbot.states import *
from misbot.until_func import until, until_eighty

from scraper.database import db_session, init_db
from scraper.models import Chat, Lecture, Practical, Misc, PushNotification, PushMessage

TOKEN = os.environ['TOKEN']
updater = Updater(TOKEN)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

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
            INPUT: [MessageHandler(Filters.text, bunk_input, pass_user_data=True)],
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
    
    make_premium_handler = ConversationHandler(
        entry_points=[CommandHandler('elevate', make_premium)],

        states = {
            ASK_USERNAME: [MessageHandler(Filters.regex(r'^\d{3}\w+\d{4}$'), ask_username, pass_user_data=True)],
            CONFIRM_USER: [MessageHandler(Filters.text, confirm_user, pass_user_data=True)],
            INPUT_TIER: [MessageHandler(Filters.text, input_tier, pass_user_data=True)],
            INPUT_VALIDITY: [MessageHandler(Filters.text, input_validity, pass_user_data=True)],
            CONFIRM_OTP: [MessageHandler(Filters.text, confirm_otp, pass_user_data=True)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    
    )

    extend_premium_handler = ConversationHandler(
        entry_points=[CommandHandler('extend', extend_premium)],

        states={
            EXTEND_ASK_USERNAME: [MessageHandler(Filters.regex(r'^\d{3}\w+\d{4}$'), extend_ask_username, pass_user_data=True)],
            EXTEND_CONFIRM_USER: [MessageHandler(Filters.text, extend_confirm_user, pass_user_data=True)],
            EXTEND_INPUT_DAYS: [MessageHandler(Filters.text, extend_input_days, pass_user_data=True)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]        
    )

    clean_records_handler = CommandHandler('clean', clean_all_attendance_records)
    admin_cmds_handler = CommandHandler('admin', admin_commands_list)

    attendance_handler = CommandHandler('attendance', attendance)
    results_handler = CommandHandler('results', results)
    itinerary_handler = CommandHandler('itinerary', itinerary, pass_args=True)
    profile_handler = CommandHandler('profile', profile)
    eighty_handler = CommandHandler('until80', until_eighty)
    until_handler = CommandHandler('until', until, pass_args=True)
    delete_handler = CommandHandler('delete', delete)
    help_handler = CommandHandler('help', help_text)
    tips_handler = CommandHandler('tips', tips)
    subscription_handler = CommandHandler('subscription', subscription)
    unknown_message = MessageHandler(Filters.text | Filters.command, unknown)

    # Dispatchers

    # User Commands
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(delete_handler)
    dispatcher.add_handler(attendance_handler)
    dispatcher.add_handler(results_handler)
    dispatcher.add_handler(profile_handler)
    dispatcher.add_handler(itinerary_handler)
    dispatcher.add_handler(bunk_handler)
    dispatcher.add_handler(eighty_handler)
    dispatcher.add_handler(until_handler)
    dispatcher.add_handler(attendance_target_handler)
    dispatcher.add_handler(edit_attendance_target_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(tips_handler)
    dispatcher.add_handler(subscription_handler)

    # Admin Commands
    dispatcher.add_handler(push_notification_handler)
    dispatcher.add_handler(delete_notification_handler)
    dispatcher.add_handler(make_premium_handler)
    dispatcher.add_handler(clean_records_handler)
    dispatcher.add_handler(extend_premium_handler)
    dispatcher.add_handler(admin_cmds_handler)
    
    # Miscellaneous
    dispatcher.add_handler(unknown_message)
    dispatcher.add_error_handler(error_callback)

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
