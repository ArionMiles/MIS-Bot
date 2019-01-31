import os
import time
import concurrent.futures
import threading
from functools import partial

import requests

from scraper.database import init_db, db_session
from scraper.models import Chat, PushNotification,PushMessage

API_KEY_TOKEN = os.environ["TOKEN"]
list_of_objs = []

def get_user_list():
    """
    Retrieves the chatID of all users from Chat table. A tuple is returned
    which is then unpacked into a list by iterating over the tuple.
    
    :return: list
    """
    users_tuple = db_session.query(Chat.chatID).all()
    users_list = [user for user, in users_tuple]
    return users_list

def push_message_threaded(bot, message, user_list):
    push_message = PushMessage(text=message)
    db_session.add(push_message)
    db_session.commit()
    
    message_uuid = push_message.uuid
    push = partial(push_t, bot, message, message_uuid) # Adding message string and uuid as function parameter
    
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        executor.map(push, user_list)
    
    elapsed = time.time() - start
    
    db_session.bulk_save_objects(list_of_objs)
    db_session.commit()
    list_of_objs.clear()
    
    return elapsed, message_uuid
 
def push_t(bot, message, message_uuid, chat_id):
    try:
        response = bot.sendMessage(chat_id=chat_id, text=message, parse_mode='markdown')
        push_message_record = PushNotification(message_uuid=message_uuid, chatID=chat_id, message_id=response.message_id, sent=True)
        list_of_objs.append(push_message_record)
    except Exception as e:
        push_message_record = PushNotification(message_uuid=message_uuid, chatID=chat_id, failure_reason=str(e))
        list_of_objs.append(push_message_record)

def delete_threaded(bot, message_id_list, user_list):
    delete_func = partial(delete, bot)
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        executor.map(delete_func, message_id_list, user_list)
    elapsed = time.time() - start
    return elapsed

def delete(bot, message_id, chat_id):
    bot.delete_message(chat_id, message_id)

if __name__ == '__main__':
    from telegram.bot import Bot
    bot = Bot(API_KEY_TOKEN)
    message = input("Enter message: ")
    print("No. of recepients: {}".format(len(get_user_list())))
    
    elapsed, message_uuid = push_message_threaded(bot, message, get_user_list())
    
    print("Time taken for threaded func: {:.2f}s\n {}".format(elapsed, message_uuid))