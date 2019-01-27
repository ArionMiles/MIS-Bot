import os
import time
import concurrent.futures
import threading
from functools import partial

import requests

from scraper.database import init_db, db_session
from scraper.models import Chat

thread_local = threading.local()
API_KEY_TOKEN = os.environ["TOKEN"]

def get_user_list():
    """
    Retrieves the chatID of all users from Chat table. A tuple is returned
    which is then unpacked into a list by iterating over the tuple.
    
    :return: list
    """
    users_tuple = db_session.query(Chat.chatID).all()
    users_list = [user for user, in users_tuple]
    return users_list

def push_message_threaded(message, user_list):
    start = time.time()
    push = partial(push_t, message) # Adding message string as function parameter
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        executor.map(push, user_list)
    elapsed = time.time() - start
    return elapsed
 
def push_t(message, chat_id):
    url = "https://api.telegram.org/bot{}/sendMessage".format(API_KEY_TOKEN)

    payload = {"text": message,
               "chat_id": chat_id, 
               "parse_mode": "markdown"
    }
    
    session = get_session()
    with session.post(url, payload) as resp:
        pass

def get_session():
    if not getattr(thread_local, "session", None):
        thread_local.session = requests.Session()
    return thread_local.session

if __name__ == '__main__':
    message = input("Enter message: ")
    print("No. of recepients: {}".format(len(get_user_list())))
    
    elapsed = push_message_threaded(message, get_user_list())
    
    print("Time taken for threaded func: {:.2f}s".format(elapsed))