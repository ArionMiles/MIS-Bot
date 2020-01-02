import textwrap

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ConversationHandler

from scraper.models import Lecture, Practical
from scraper.database import db_session
from misbot.mis_utils import bunk_lecture, get_subject_name, build_menu, get_user_info
from misbot.decorators import signed_up, premium
from misbot.states import CHOOSING, INPUT, CALCULATING
from misbot.analytics import mp

@signed_up
@premium(tier=1)
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
    chat_id = update.message.chat_id
    
    if update.message.text == "Lectures":
        user_data['type'] = "Lectures"
    elif update.message.text == "Practicals":
        user_data['type'] = "Practicals"
    else:
        bot.sendMessage(chat_id=chat_id, text="Please choose out of the two options.")
        return

    stype = user_data['type']
    reply_markup = ReplyKeyboardRemove()
    reply_text = "{}\nChoose `Cancel` to exit.".format(stype)
    bot.sendMessage(chat_id=chat_id, text=reply_text, reply_markup=reply_markup, parse_mode='markdown')

    if stype == "Lectures":
        subject_data = Lecture.query.filter(Lecture.chatID == chat_id).all()
    else:
        subject_data = Practical.query.filter(Practical.chatID == chat_id).all()

    if not subject_data: #If list is empty
        messageContent = textwrap.dedent("""
            No records found!
            Please use /attendance to pull your attendance from the website first.
            """)
        bot.sendMessage(chat_id=chat_id, text=messageContent)
        return ConversationHandler.END

    messageContent = ""

    for digit, subject in enumerate(subject_data):
        subject_name = subject.name
        messageContent += "{digit}. {subject_name}\n".format(digit=digit+1, subject_name=subject_name)

    keyboard = build_menu(subject_data, 3, footer_buttons='Cancel')
    reply_markup = ReplyKeyboardMarkup(keyboard)
    user_data['reply_markup'] = reply_markup
    bot.sendMessage(chat_id=chat_id, text=messageContent, reply_markup=reply_markup)
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
    :return: ConversationHandler.END if message is "Cancel" else CALCULATING
    :rtype: int
    """
    reply_markup = ReplyKeyboardRemove()
    if update.message.text == "Cancel":
        # Terminate bunk operation since fallback commands do not work with 
        # 2 conversation handlers present for some reason
        # if you figure it out, I'll buy you coffee
        bot.sendMessage(chat_id=update.message.chat_id, text="Bunk operation cancelled! 😊", reply_markup=reply_markup)
        return ConversationHandler.END
    
    try:
        user_data['index'] = int(update.message.text)
    except ValueError:
        bot.sendMessage(chat_id=update.message.chat_id, text="Please select a number from the menu.")
        return

    messageContent = textwrap.dedent("""
        Send number of lectures you wish to bunk and total lectures conducted for that subject on that day,
        separated by a space.

        e.g: If you wish to bunk 1 out of 5 lectures (total or per subject) conducted today, send
        `1 5`
        Use /cancel to exit.
        """)
    bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, parse_mode='markdown', reply_markup=reply_markup)
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
    chat_id = update.message.chat_id
    
    if user_data['figures'] == '/cancel':
        bot.sendMessage(chat_id=chat_id, text="Bunk operation cancelled! 😊")
        return ConversationHandler.END

    stype = user_data['type']
    index = user_data['index']
    args = user_data['figures'].split(' ')

    bot.send_chat_action(chat_id=chat_id, action='typing')

    if len(args) == 2:
        current = bunk_lecture(0, 0, chat_id, stype, index)
        predicted = bunk_lecture(int(args[0]), int(args[1]), chat_id, stype, index)
        no_bunk = bunk_lecture(0, int(args[1]), chat_id, stype, index)
        loss = round((current - predicted), 2)
        gain = round((no_bunk - current), 2)

        messageContent = textwrap.dedent("""
            Subject: {subject}
            Current: {current}%
            If you bunk: {predicted}%
            If you attend: {no_bunk}%

            Loss: {loss}%
            Gain: {gain}%

            If you wish to check for another subject, select the respective number or press `Cancel` to cancel
            this operation.
            """).format(current=current, predicted=predicted, no_bunk=no_bunk, loss=loss, gain=gain, 
            subject=get_subject_name(chat_id, index, stype))
        bot.sendMessage(chat_id=chat_id, text=messageContent, reply_markup=user_data['reply_markup'], parse_mode='markdown')
        
        username = get_user_info(chat_id)['PID']
        mp.track(username, 'Bunk', {'category': stype })
        return INPUT
    else:
        messageContent = textwrap.dedent("""
            This command expects 2 arguments.
            
            e.g: If you wish to bunk 1 out of 5 total lectures conducted today, send
            `1 5`
            Or, send /cancel to quit.
            """)
        bot.sendMessage(chat_id=chat_id, text=messageContent, parse_mode='markdown')
        return
    return ConversationHandler.END
