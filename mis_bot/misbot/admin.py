import textwrap

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ConversationHandler
from sqlalchemy import and_

from misbot.decorators import admin
from misbot.push_notifications import push_message_threaded, delete_threaded, get_user_list
from misbot.states import NOTIF_MESSAGE, NOTIF_CONFIRM, ASK_UUID, CONFIRM_REVERT
from scraper.models import PushMessage, PushNotification
from scraper.database import init_db, db_session


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
    messageContent = "Targeting {} users. Requesting confirmation...".format(len(get_user_list()))
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
        time_taken, message_uuid = push_message_threaded(user_data['notif_message'], users)
        stats_message = textwrap.dedent("""
        Sent to {} users in {:.2f}secs.
        Here's your unique notification ID: `{}`
        """.format(len(users), time_taken, message_uuid))
        bot.sendMessage(chat_id=update.message.chat_id, text=stats_message, parse_mode='markdown')
        return ConversationHandler.END
    elif update.message.text == "No":
        bot.sendMessage(chat_id=update.message.chat_id, text="Aborted!", reply_markup=reply_markup)
        return ConversationHandler.END
    return


@admin
def revert_notification(bot, update):
    """Delete a previously sent push notification.
    Ask for UUID of message to delete and pass control to :func:`ask_uuid`
    
    :param bot: Telegram Bot object
    :type bot: telegram.bot.Bot
    :param update: Telegram Update object
    :type update: telegram.update.Update
    """
    messageContent = "Send the UUID of the message you wish to revert." 
    update.message.reply_text(messageContent)
    return ASK_UUID


def ask_uuid(bot, update, user_data):
    """Store the uuid, send confirmation message
    and pass control to :func:`confirm_revert`
    
    :param bot: Telegram Bot object
    :type bot: telegram.bot.Bot
    :param update: Telegram Update object
    :type update: telegram.update.Update
    :param user_data: Conversation data
    :type user_data: dict
    """
    user_data['uuid'] = update.message.text
    keyboard = [['Yes'], ['No']]
    reply_markup = ReplyKeyboardMarkup(keyboard)
    messageContent = "Are you sure you want to revert?"
    bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, reply_markup=reply_markup)
    return CONFIRM_REVERT


def confirm_revert(bot, update, user_data):
    """If Yes, revert the specified message for all
    users and send a summary of the operation to admin.
    
    :param bot: Telegram Bot object
    :type bot: telegram.bot.Bot
    :param update: Telegram Update object
    :type update: telegram.update.Update
    :param user_data: Conversation data
    :type user_data: dict
    """
    reply_markup = ReplyKeyboardRemove()
    
    if update.message.text == "Yes":
        try:
            notification_message = PushMessage.query.filter(PushMessage.uuid == user_data['uuid']).first().text
        except AttributeError:
            bot.sendMessage(chat_id=update.message.chat_id, text="Unknown UUID. Try again.", reply_markup=reply_markup)
            return ConversationHandler.END
        notifications = PushNotification.query.filter(and_(PushNotification.message_uuid == user_data['uuid'],\
                                                           PushNotification.sent == True))
        user_list = [notification.chatID for notification in notifications]
        message_ids = [notification.message_id for notification in notifications]
        
        time_taken = delete_threaded(message_ids, user_list)
        
        
        notification_message_short = textwrap.shorten(notification_message, width=20, placeholder='...')
        
        stats_message = textwrap.dedent("""
        Deleted the notification:
        ```
        {}
        ```
        {} messages deleted in {:.2f}secs.
        """.format(notification_message_short, len(message_ids), time_taken))
        
        bot.sendMessage(chat_id=update.message.chat_id, text=stats_message, parse_mode='markdown', reply_markup=reply_markup)
        
        db_session.query(PushMessage).filter(PushMessage.uuid == user_data['uuid']).update({'deleted': True})
        db_session.commit()
        return ConversationHandler.END
    elif update.message.text == "No" or update.message.text == "/cancel":
        bot.sendMessage(chat_id=update.message.chat_id, text="Revert Aborted!", reply_markup=reply_markup)
        return ConversationHandler.END
    return
