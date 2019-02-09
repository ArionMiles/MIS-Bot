import logging
import textwrap

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ConversationHandler

from scraper.models import Misc
from scraper.database import init_db, db_session
from misbot.decorators import signed_up
from misbot.states import SELECT_YN, INPUT_TARGET, UPDATE_TARGET
from misbot.mis_utils import until_x

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


@signed_up
def attendance_target(bot, update):
    """Like :func:`until_eighty`, but with user specified target attendance percentage
    which is stored in the Misc table.
    If target isn't set, asks users whether they'd like to and passes control to 
    :func:`select_yn`
    
    :param bot: Telegram Bot object
    :type bot: telegram.bot.Bot
    :param update: Telegram Update object
    :type update: telegram.update.Update
    :return: SELECT_YN
    :rtype: int
    """

    bot.send_chat_action(chat_id=update.message.chat_id, action='typing')

    student_misc = Misc.query.filter(Misc.chatID == update.message.chat_id).first()
    
    if student_misc is None:
        new_misc_record = Misc(chatID=update.message.chat_id)
        db_session.add(new_misc_record)
        db_session.commit()
        logger.info("Created new Misc record for {}".format(update.message.chat_id))
        # bot.sendMessage(chat_id=update.message.chat_id, text="No records found!")
        student_misc = Misc.query.filter(Misc.chatID == update.message.chat_id).first()
    
    target = student_misc.attendance_target
    
    if target is None:

        messageContent = textwrap.dedent("""
        You have not set a target yet. Would you like to set it now?
        You can change it anytime using /edit_target
        """)
        keyboard = [['Yes'], ['No']]
        reply_markup = ReplyKeyboardMarkup(keyboard)
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, reply_markup=reply_markup)
        return SELECT_YN

    no_of_lectures = int(until_x(update.message.chat_id, target))
    if no_of_lectures < 0:
        messageContent = "Your attendance is already over {}%. Maybe set it higher? Use /edit_target to change it.".format(target)
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)
        return ConversationHandler.END
    
    messageContent = "You need to attend {} lectures to meet your target of {}%".format(no_of_lectures, target)
    bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)
    return ConversationHandler.END


def select_yn(bot, update):
    """If user replies no, ends the conversation,
    otherwise transfers control to :func:`input_target`.
    
    :param bot: Telegram Bot object
    :type bot: telegram.bot.Bot
    :param update: Telegram Update object
    :type update: telegram.update.Update
    :return: INPUT_TARGET
    :rtype: int
    """
    reply_markup = ReplyKeyboardRemove()
    
    if update.message.text == 'No':
        messageContent = "Maybe next time!"
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, reply_markup=reply_markup)
        return ConversationHandler.END
    messageContent = textwrap.dedent("""
    Okay, give me a figure!

    e.g: If you want a target of 80%, send `80`
    """)
    bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, parse_mode='markdown', reply_markup=reply_markup)
    return INPUT_TARGET


def input_target(bot, update):
    """If the user reply is a int/float and between 1-99, stores the figure 
    as the new attendance target.
    
    :param bot: Telegram Bot object
    :type bot: telegram.bot.Bot
    :param update: Telegram Update object
    :type update: telegram.update.Update
    :return: ConversationHandler.END
    :rtype: int
    """

    try:
        target_figure = float(update.message.text)
    except ValueError:
        bot.sendMessage(chat_id=update.message.chat_id, text="You must send a number between 1-99.")
        return
    
    if not 1 <= target_figure <= 99:
        bot.sendMessage(chat_id=update.message.chat_id, text="You must send a number between 1-99.")
        return

    db_session.query(Misc).filter(Misc.chatID == update.message.chat_id).update({'attendance_target': target_figure})
    db_session.commit()
    messageContent = "Your attendance target has been set to {}%.".format(target_figure)
    bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)
    return ConversationHandler.END


@signed_up
def edit_attendance_target(bot, update):
    """Edit existing attendance target. Shows current target and transfers
    control to `update_target`
    
    :param bot: Telegram Bot object
    :type bot: telegram.bot.Bot
    :param update: Telegram Update object
    :type update: telegram.update.Update
    :return: UPDATE_TARGET
    :rtype: int
    """    
    student_misc_model = Misc.query.filter(Misc.chatID == update.message.chat_id).first()
    messageContent = "You do not have any target records. To create one, use /target"
    if student_misc_model is None:
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)
        return ConversationHandler.END

    current_target = student_misc_model.attendance_target

    if current_target is None:
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)
        return ConversationHandler.END
    
    edit_message = textwrap.dedent("""
    Your current attendance target is {}%.
    Send a new figure to update or /cancel to cancel this operation
    """.format(current_target))

    bot.sendMessage(chat_id=update.message.chat_id, text=edit_message)
    return UPDATE_TARGET


def update_target(bot, update):
    """Takes the sent figure and sets it as new attendance target.
    
    :param bot: Telegram Bot object
    :type bot: telegram.bot.Bot
    :param update: Telegram Update object
    :type update: telegram.update.Update
    :return: ConversationHandler.END
    :rtype: int
    """

    user_reply = update.message.text

    if user_reply == '/cancel':
        bot.sendMessage(chat_id=update.message.chat_id, text="As you wish! The operation is cancelled!")
        return ConversationHandler.END
    
    try:
        new_target = int(user_reply)
    except ValueError:
        bot.sendMessage(chat_id=update.message.chat_id, text="You must send a number between 1-99.")
        return
    
    if not 1 <= new_target <= 99:
        bot.sendMessage(chat_id=update.message.chat_id, text="You must send a number between 1-99.")
        return

    db_session.query(Misc).filter(Misc.chatID == update.message.chat_id).update({'attendance_target': new_target})
    db_session.commit()
    new_target_message = "Your attendance target has been updated to {}%!".format(new_target)
    bot.sendMessage(chat_id=update.message.chat_id, text=new_target_message)
    return ConversationHandler.END
