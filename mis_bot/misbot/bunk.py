import textwrap

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ConversationHandler

from scraper.models import Lecture, Practical
from scraper.database import db_session
from misbot.mis_utils import bunk_lecture
from misbot.decorators import signed_up
from misbot.states import CHOOSING, INPUT, CALCULATING

@signed_up
def bunk(bot, update):
    """
    Starting point of bunk_handler.
    Sends a KeyboardMarkup (https://core.telegram.org/bots#keyboards)
    Passes control to :py:func:`bunk_choose`

    :param bot: Telegram Bot object
    :type bot: telegram.bot.Bot
    :param update: Telegram Update object
    :type update: telegram.update.Update
    :return: CHOOSING
    :rtype: int
    """
    bot.send_chat_action(chat_id=update.message.chat_id, action='typing')
    keyboard = [['Lectures'], ['Practicals']]
    reply_markup = ReplyKeyboardMarkup(keyboard)
    messageContent = "Select type!"
    bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, reply_markup=reply_markup)

    return CHOOSING


def bunk_choose(bot, update, user_data):
    """Removes keyboardMarkup sent in previous handler.

    Stores the response (for Lectures/Practicals message sent in previous handler) in a ``user_data``
    dictionary with the key `"stype"`.
    ``user_data`` is a user relative dictionary which holds data between different handlers/functions
    in a ConversationHandler.

    Selects the appropriate table (Lecture or Practical) based on ``stype`` value.
    Checks if records exist in the table for a user and sends a warning message or proceeds
    to list names of all subjects in the table.

    Passes control to :py:func:`bunk_input`
    
    :param bot: Telegram Bot object
    :type bot: telegram.bot.Bot
    :param update: Telegram Update object
    :type update: telegram.update.Update
    :param user_data: User data dictionary
    :type user_data: dict
    :return: ConversationHandler.END if no records else INPUT
    :rtype: int
    """
    user_data['type'] = update.message.text
    stype = user_data['type']
    reply_markup = ReplyKeyboardRemove()
    bot.sendMessage(chat_id=update.message.chat_id, text="{}".format(stype), reply_markup=reply_markup)

    if stype == "Lectures":
        subject_data = Lecture.query.filter(Lecture.chatID == update.message.chat_id).all()
    else:
        subject_data = Practical.query.filter(Practical.chatID == update.message.chat_id).all()


    if not subject_data: #If list is empty
        messageContent = textwrap.dedent("""
            No records found!
            Please use /attendance to pull your attendance from the website first.
            """)
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)
        return ConversationHandler.END

    digit = 1
    messageContent = ""

    for subject in subject_data:
        subject_name = subject.name
        messageContent += "/{digit}. {subject_name}\n".format(digit=digit, subject_name=subject_name)
        digit += 1

    bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)
    digit = 0
    return INPUT


def bunk_input(bot, update, user_data):
    """Stores index of the chosen subject in ``user_data['index']`` from ``update.message.text``.
    Passes control to :py:func:`bunk_calc`

    :param bot: Telegram Bot object
    :type bot: telegram.bot.Bot
    :param update: Telegram Update object
    :type update: telegram.update.Update
    :param user_data: User data dictionary
    :type user_data: dict
    :return: ConversationHandler.END if message is "/cancel_bunk" else CALCULATING
    :rtype: int
    """
    user_data['index'] = update.message.text
    if user_data['index'] == "/cancel_bunk":
        # Terminate bunk operation since fallback commands do not work with 
        # 2 conversation handlers present for some reason
        # if you figure it out, I'll buy you coffee
        bot.sendMessage(chat_id=update.message.chat_id, text="Bunk operation cancelled! 😊")
        return ConversationHandler.END


    messageContent = textwrap.dedent("""
        Send number of lectures you wish to bunk and total lectures conducted for that subject on that day,
        separated by a space.

        e.g: If you wish to bunk 1 out of 5 lectures (total or per subject) conducted today, send
        `1 5`
        """)
    bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, parse_mode='markdown')
    return CALCULATING


def bunk_calc(bot, update, user_data):
    """Calculate the % drop/rise with the previously given values from the user
    and send the response to the user.
    
    ``user_data`` contains: ``type``, ``index``, ``figures``.

    Incorrect no. of arguments resets the state and user is asked for input again.

    :param bot: Telegram Bot object
    :type bot: telegram.bot.Bot
    :param update: Telegram Update object
    :type update: telegram.update.Update
    :param user_data: User data dictionary
    :type user_data: dict
    :return: None if incorrect values else INPUT
    :rtype: None or int
    """
    user_data['figures'] = update.message.text
    stype = user_data['type']
    try:
        index = int(user_data['index'].split('/')[1])
    except ValueError:
        return ConversationHandler.END
    args = user_data['figures'].split(' ')

    bot.send_chat_action(chat_id=update.message.chat_id, action='typing')

    if len(args) == 2:
        current = bunk_lecture(0, 0, update.message.chat_id, stype, index)
        predicted = bunk_lecture(int(args[0]), int(args[1]), update.message.chat_id, stype, index)
        no_bunk = bunk_lecture(0, int(args[1]), update.message.chat_id, stype, index)
        loss = round((current - predicted), 2)
        gain = round((no_bunk - current), 2)

        messageContent = textwrap.dedent("""
            Current: {current}
            If you bunk: {predicted}
            If you attend: {no_bunk}

            Loss: {loss}
            Gain: {gain}

            If you wish to check for another subject, select their number from above or press /cancel_bunk to cancel
            this operation.
            """).format(current=current, predicted=predicted, no_bunk=no_bunk, loss=loss, gain=gain)
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)
        return INPUT
    else:
        messageContent = textwrap.dedent("""
            This command expects 2 arguments.
            
            e.g: If you wish to bunk 1 out of 5 total lectures conducted today, send
            `1 5`
            """)
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, parse_mode='markdown')
        return
    return ConversationHandler.END
