import os
from functools import wraps
import logging

from scraper.models import Chat

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

def signed_up(func):
    """Checks if user is signed up or not.
    If user isn't signed up, sends a message asking them to register.
    
    :param func: A telegram bot function
    :type func: func
    :return: None if user isn't registered or the function which decorator is applied on.
    :rtype: None or func
    """
    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        chatID = update.message.chat_id
        if not Chat.query.filter(Chat.chatID == chatID).first():
            bot.sendMessage(chat_id=update.message.chat_id, text="Unregistered! Use the /register command to sign up!")
            return
        return func(bot, update, *args, **kwargs)
    return wrapped


def admin(func):
    """Checks if the user sending the command/message is an admin or not.
    If user isn't an admin, their username (or chat ID, if unregistered) is logged
    and a message is sent saying that the incident has been reported.
    
    :param func: A telegram bot function
    :type func: func
    :return: None if user isn't registered or the function which decorator is applied on.
    :rtype: None or func
    """
    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        chatID = update.message.chat_id
        if not str(chatID) == os.environ['ADMIN_CHAT_ID']:
            messageContent = "You are not authorized to use this command. This incident has been reported."
            bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)
            user_info = Chat.query.filter(Chat.chatID == chatID).first()
            if user_info:
                logger.warning("Unauthorized Access attempt by {}".format(user_info.PID))
            else:
                logger.warning("Unauthorized Access attempt by {}".format(chatID))
            return
        return func(bot, update, *args, **kwargs)
    return wrapped
