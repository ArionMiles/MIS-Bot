import os
import time
import concurrent.futures
import threading
from functools import partial

import requests
from telegram.bot import Bot
from telegram.utils.request import Request

from scraper.database import init_db, db_session
from scraper.models import Chat, PushNotification,PushMessage
from misbot.mis_utils import get_user_info

API_KEY_TOKEN = os.environ["TOKEN"]
list_of_objs = []

def get_user_list():
    """Retrieves the ``chatID`` of all users from ``Chat`` table. A tuple is returned
    which is then unpacked into a list by iterating over the tuple.
    
    :return: List of user chat IDs
    :rtype: list
    """
    users_tuple = db_session.query(Chat.chatID).all()
    users_list = [user for user, in users_tuple]
    return users_list

def get_bot():
    """Create an instance of the :py:class:`telegram.bot.Bot` object.
    
    :return: Telegram bot object.
    :rtype: telegram.bot.Bot
    """

    request = Request(con_pool_size=30) # Increasing default connection pool from 1
    bot = Bot(API_KEY_TOKEN, request=request)
    return bot

def push_message_threaded(message, user_list):
    """Use ``ThreadPoolExecutor`` to send notification message asynchronously to all
    users.
    Before sending the message, we create a record of the sent message in the ``PushMessage`` DB model.

    We pass the ``message_uuid`` generated from created the record of the message previously and pass it
    to the :py:func:`push_t`.

    After messages have been sent, we bulk commit all the ``PushNotification`` records created within
    :py:func:`push_t` to our database.
    
    :param message: Notification message
    :type message: str
    :param user_list: List of all bot users
    :type user_list: list
    :return: Time taken to send messages and the ``message_uuid``
    :rtype: tuple
    """

    push_message = PushMessage(text=message)
    db_session.add(push_message)
    db_session.commit()
    
    message_uuid = push_message.uuid
    push = partial(push_t, get_bot(), message, message_uuid) # Adding message string and uuid as function parameter
    
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        executor.map(push, user_list)
    
    elapsed = time.time() - start
    
    db_session.bulk_save_objects(list_of_objs)
    db_session.commit()
    list_of_objs.clear()
    
    return elapsed, message_uuid
 
def push_t(bot, message, message_uuid, chat_id):
    """Sends the message to the specified ``chat_id``.
    Records the ``message_id`` received into ``PushNotification`` DB Model.
    Appends the record object to ``list_of_objs`` to be bulk committed after all messages have been
    sent through ``ThreadPoolExecutor``
    
    :param bot: Telegram Bot object
    :type bot: telegram.bot.Bot
    :param message: Notification message
    :type message: str
    :param message_uuid: UUID of the notification message created in ``push_message_threaded``
    :type message_uuid: str
    :param chat_id: 9-Digit unique user ID
    :type chat_id: int|str
    """

    username = get_user_info(chat_id)['PID'][3:-4].title()
    message = "Hey {0}!\n{1}".format(username, message)
    try:
        response = bot.sendMessage(chat_id=chat_id, text=message, parse_mode='markdown')
        push_message_record = PushNotification(message_uuid=message_uuid, chatID=chat_id, message_id=response.message_id, sent=True)
        list_of_objs.append(push_message_record)
    except Exception as e:
        push_message_record = PushNotification(message_uuid=message_uuid, chatID=chat_id, failure_reason=str(e))
        list_of_objs.append(push_message_record)

def delete_threaded(message_id_list, user_list):
    """Use ``ThreadPoolExecutor`` to delete notification message asynchronously for all
    users.
    
    :param message_id_list: List of message ids stored in our DB.
    :type message_id_list: list
    :param user_list: List of all bot users
    :type user_list: list
    :return: Time taken to send all delete requests
    :rtype: float
    """

    delete_func = partial(delete, get_bot())
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        executor.map(delete_func, message_id_list, user_list)
    elapsed = time.time() - start
    return elapsed

def delete(bot, message_id, chat_id):
    """Sends a delete request for a particular ``chat_id`` and ``message_id``
    
    :param bot: Telegram Bot object
    :type bot: telegram.bot.Bot
    :param message_id: The message ID for the notification message
    :type message_id: int
    :param chat_id: 9-Digit unique user ID
    :type chat_id: int | str
    """

    bot.delete_message(chat_id, message_id)
