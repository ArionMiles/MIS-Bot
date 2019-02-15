import textwrap

from misbot.decorators import signed_up
from misbot.mis_utils import until_x

@signed_up
def until_eighty(bot, update):
    """Calculate number of lectures you must consecutively attend before you attendance is 80%
    
    If :py:func:`misbot.mis_utils.until_x` returns a negative number, attendance is already over 80%

    :param bot: Telegram Bot object
    :type bot: telegram.bot.Bot
    :param update: Telegram Update object
    :type update: telegram.update.Update    
    """
    bot.send_chat_action(chat_id=update.message.chat_id, action='typing')
    no_of_lectures = int(until_x(update.message.chat_id, 80))
    if no_of_lectures < 0:
        bot.sendMessage(chat_id=update.message.chat_id, text="Your attendance is already over 80%. Relax.")
    else:
        messageContent = "No. of lectures to attend: {}".format(no_of_lectures)
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)

@signed_up
def until(bot, update, args):
    """Like :py:func:`until_eighty` but user supplies the number.

    :param bot: Telegram Bot object
    :type bot: telegram.bot.Bot
    :param update: Telegram Update object
    :type update: telegram.update.Update
    :param args: User supplied arguments
    :type args: tuple
    :return: None
    :rtype: None
    """
    if len(args) == 0:
        messageContent = textwrap.dedent("""
        You must specify a number after the command to use this feature.

        E.g: `/until 75`
        """)
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent, parse_mode='markdown')
        return

    try:
        figure = float(args[0])
    except (ValueError, IndexError):
        bot.sendMessage(chat_id=update.message.chat_id, text="You must send a number between 1-99.")
        return
    
    if figure > 99:
        bot.sendMessage(chat_id=update.message.chat_id, text="You must send a number between 1-99.")
        return

    no_of_lectures = int(until_x(update.message.chat_id, figure))
    if no_of_lectures < 0:
        bot.sendMessage(chat_id=update.message.chat_id, text="Your attendance is already over {}%. Relax.".format(figure))
    else:
        messageContent = "No. of lectures to attend: {}".format(no_of_lectures)
        bot.sendMessage(chat_id=update.message.chat_id, text=messageContent)
