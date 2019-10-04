import logging
import random
import textwrap

from telegram.ext import ConversationHandler
from telegram.error import TelegramError, Unauthorized, BadRequest, TimedOut, ChatMigrated, NetworkError
from sqlalchemy import and_

from scraper.models import Chat
from scraper.database import db_session
from misbot.mis_utils import check_login, check_parent_login, get_user_info
from misbot.decorators import signed_up
from misbot.states import CREDENTIALS, PARENT_LGN
from misbot.analytics import mp

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

def start(bot, update):
    """Initial message sent to all users.
    Starts registration conversation, passes control to :py:func:`credentials`
    """
    intro_message = textwrap.dedent("""
    Hi! I'm a Telegram Bot for Aldel MIS.
    My source code lives at [Github.](https://github.com/ArionMiles/MIS-Bot) 👨‍💻
    To start using my services, please send me your MIS credentials in this format: 
    `Student-ID password` 
    (in a single line, separated by a space)

    Use /cancel to abort.
    Use /help to learn more.
    Join the [Channel](https://t.me/joinchat/AAAAAEzdjHzLCzMiKpUw6w) to get updates about the bot's status.
    """)
    bot.sendMessage(chat_id=update.message.chat_id, text=intro_message, parse_mode='markdown',\
        disable_web_page_preview=True)
    return CREDENTIALS


def register(bot, update, user_data):
    """Let all users register with their credentials.
    Similar to :py:func:`start` but this function can be invoked by ``/register`` command.

    If user's ``chatID`` & ``DOB`` are already present in database then ends the conversation.
    Otherwise, if only ``chatID`` is present, then stores ``StudentID`` (PID) in ``user_data`` dict &
    gives control to :py:func:`parent_login` function.

    If both conditions are false, then asks user to input Student details (PID & Password)
    and gives control to :py:func:`credentials`
    """
    if Chat.query.filter(Chat.chatID == update.message.chat_id).first():
        if Chat.query.filter(and_(Chat.chatID == update.message.chat_id, Chat.DOB != None)).first():
            messageContent = "Already registered!"
            bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)
            return ConversationHandler.END

        student_data = Chat.query.filter(Chat.chatID == update.message.chat_id).first()
        user_data['Student_ID'] = student_data.PID
        
        messageContent = textwrap.dedent("""
        Now enter your Date of Birth (DOB) in the following format:
        `DD/MM/YYYY`
        """)
        update.message.reply_text(messageContent, parse_mode='markdown')
        return PARENT_LGN

    messageContent = textwrap.dedent("""
    Okay, send me your MIS credentials in this format:
    `Student-ID password`
    (in a single line, separated by a space)

    Use /cancel to abort.
    """)
    bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, parse_mode='markdown')
    return CREDENTIALS


def credentials(bot, update, user_data):
    """
    Store user credentials in a database.
    Takes student info (PID & password) from ``update.message.text`` and splits it into Student_ID &
    Password and checks if they are correct with :py:func:`misbot.mis_utils.check_login` and stores them in the ``Chat`` table.
    Finally, sends message asking users to enter DOB and gives control to :func:`parent_login` after
    storing ``Student_ID`` (PID) in user_data dict.
    """
    chatID = update.message.chat_id
    # If message contains less or more than 2 arguments, send message and stop.
    try:
        Student_ID, passwd = update.message.text.split()
    except ValueError:
        messageContent = textwrap.dedent("""
        Oops, you made a mistake! 
        You must send the Student_ID and password in a single line, separated by a space.
        This is what valid login credentials look like:
        `123name4567 password`
        """)
        bot.send_chat_action(chat_id=update.message.chat_id, action='typing')
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, parse_mode='markdown')
        return

    if not check_login(Student_ID, passwd):
        messageContent = textwrap.dedent("""
        Looks like your credentials are incorrect! Give it one more shot.
        This is what valid login credentials look like:
        `123name4567 password`
        """)
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, parse_mode='markdown')
        return

    # Create an object of Class <Chat> and store Student_ID, password, and Telegram
    # User ID, Add it to the database, commit it to the database.

    userChat = Chat(PID=Student_ID, password=passwd, chatID=chatID)
    db_session.add(userChat)
    db_session.commit()


    messageContent = textwrap.dedent("""
        Now enter your Date of Birth (DOB) in the following format:
        `DD/MM/YYYY`
        """)
    update.message.reply_text(messageContent, parse_mode='markdown')
    user_data['Student_ID'] = Student_ID
    return PARENT_LGN


def parent_login(bot, update, user_data):
    """
    user_data dict contains ``Student_ID`` key from :py:func:`credentials`.
    Extracts DOB from ``update.message.text`` and checks validity using :py:func:`misbot.mis_utils.check_parent_login`
    before adding it to database.
    Finally, sends a message to the user requesting them to start using ``/attendance`` or
    ``/itinerary`` commands.
    """
    DOB = update.message.text
    Student_ID = user_data['Student_ID']
    chatID = update.message.chat_id

    if not check_parent_login(Student_ID, DOB):
        messageContent = textwrap.dedent("""
        Looks like your Date of Birth details are incorrect! Give it one more shot.
        Send DOB in the below format:
        `DD/MM/YYYY`
        """)
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, parse_mode='markdown')
        return
    new_user = Student_ID[3:-4].title()

    db_session.query(Chat).filter(Chat.chatID == chatID).update({'DOB': DOB})
    db_session.commit()
    logger.info("New Registration! Username: {}".format((Student_ID)))
    messageContent = "Welcome {}!\nStart by checking your /attendance or /itinerary".format(new_user)
    bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, parse_mode='markdown')

    mp.track(Student_ID, 'New User')
    mp.people_set(Student_ID, {
                                'pid': Student_ID,
                                'first_name': update.message.from_user.first_name,
                                'last_name': update.message.from_user.last_name,
                                'username': update.message.from_user.username,
                                'link': update.message.from_user.link,
                                'active': True,
                            })

    return ConversationHandler.END


@signed_up
def delete(bot, update):
    """Delete a user's credentials if they wish to stop using the bot or update them."""
    chatID = update.message.chat_id
    user_details = get_user_info(chatID)
    username = user_details['PID']
    logger.info("Deleting user credentials for {}!".format(username))
    Chat.query.filter(Chat.chatID == chatID).delete() # Delete the user's record referenced by their ChatID
    db_session.commit()
    messageContent = "Your credentials have been deleted, {}\nHope to see you back soon.".format(username[3:-4].title())
    bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)
    
    mp.track(username, 'User Left')
    mp.people_set(username, {'active': False })


def cancel(bot, update):
    """Cancel registration operation (terminates conv_handler)"""
    bot.sendMessage(chat_id=update.message.chat_id, text="As you wish, the operation has been cancelled! 😊")
    return ConversationHandler.END


def unknown(bot, update):
    """Respond to incomprehensible messages/commands with some canned responses."""
    can = ["Seems like I'm not programmed to understand this yet.", "I'm not a fully functional A.I. ya know?",
        "The creator didn't prepare me for this.", "I'm not sentient...yet! 🤖", "Damn you're dumb.", "42",
        "We cannot afford machine learning to make this bot smart!", "We don't use NLP.", "I really wish we had a neural network.",
        "You make me wish I had middle fingers.", "Sorry, did you say something? I wasn't listening.",
        "Are you always such an idiot, or do you just like to show off here?", "Talk to the hand. ✋",]
    messageContent = random.choice(can)
    bot.send_chat_action(chat_id=update.message.chat_id, action='typing')
    bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)


def help_text(bot, update):
    """Display help text."""
    helpText = textwrap.dedent("""
    1. /register - Register yourself
    2. /attendance - Fetch attendance from the MIS website.
    3. /itinerary - Fetch detailed attendance.
    3. /results - Fetch unit test results
    4. /bunk - Calculate % \drop/rise.
    5. /until80 - No. of lectures to attend consecutively until total attendance is 80%
    6. /cancel - Cancel registration.
    7. /delete - Delete your credentials.
    8. /tips - Random tips.
    """)
    bot.sendMessage(chat_id=update.message.chat_id, text=helpText, parse_mode='markdown')


def tips(bot, update):
    """Send a random tip about the bot."""
    tips = ["Always use /attendance command before using /until80 or /bunk to get latest figures.",\
    "The Aldel MIS gets updated at 6PM everyday.", "The /until80 function gives you the number of lectures you must attend *consecutively* before you attendance is 80%.",\
    "The bunk calculator's figures are subject to differ from actual values depending upon a number of factors such as:\
    \nMIS not being updated.\
    \nCancellation of lectures.\
    \nMass bunks. 😝", "`/itinerary all` gives complete detailed attendance report since the start of semester."]
    messageContent = random.choice(tips)
    bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, parse_mode='markdown')

def error_callback(bot, update, error):
    """Simple error handling function. Handles PTB lib errors"""
    user = get_user_info(update.message.chat_id)
    username = update.message.chat_id if user is None else user['PID']

    try:
        raise error
    except Unauthorized:
        # remove update.message.chat_id from conversation list
        mp.track(username, 'Error', {'type': 'Unauthorized' })
        logger.warning("TelegramError: Unauthorized user. User probably blocked the bot.")
    except BadRequest as br:
        # handle malformed requests
        mp.track(username, 'Error', {'type': 'BadRequest', 'text': update.message.text, 'error': str(br) })
        logger.warning("TelegramError: {} | Text: {} | From: {}".format(str(br), update.message.text, update.message.from_user))
    except TimedOut as time_out:
        # handle slow connection problems
        mp.track(username, 'Error', {'type': 'TimedOut', 'text': update.message.text, 'error': str(time_out) })
        logger.warning("TelegramError: {} | Text: {} | From: {}".format(str(time_out), update.message.text, update.message.from_user))
    except NetworkError as ne:
        # handle other connection problems
        mp.track(username, 'Error', {'type': 'NetworkError', 'text': update.message.text, 'error': str(ne) })
        logger.warning("TelegramError: {} | Text: {} | From: {}".format(str(ne), update.message.text, update.message.from_user))
    except ChatMigrated as cm:
        # the chat_id of a group has changed, use e.new_chat_id instead
        mp.track(username, 'Error', {'type': 'ChatMigrated' })
        logger.warning("TelegramError: {} | Text: {} | From: {}".format(str(cm), update.message.text, update.message.from_user))
    except TelegramError as e:
        # handle all other telegram related errors
        mp.track(username, 'Error', {'type': 'TelegramError', 'text': update.message.text, 'error': str(e) })
        logger.warning("TelegramError: {} | Text: {} | From: {}".format(str(e), update.message.text, update.message.from_user))
