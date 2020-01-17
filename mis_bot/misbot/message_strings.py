"""
Contains all message string templates
"""
from os import environ
import textwrap

SUBSCRIPTION_MSG = textwrap.dedent("""
There is a one-time fee of ₹50/- per semester.

Payment is accepted via UPI. All UPI apps work (PayTM/PhonePe/GPay/etc.)

*TIP:* If you sign up on Google Pay and enter my referral code *{}*, you get ₹21 back on your first payment, so you save money! 
[Use this link](https://g.co/payinvite/{}) to signup using my referral code!

To upgrade, make a payment at this link:
[PAYMENT LINK]({})

After payment, [send me a message](t.me/Arion_Miles) and 
I'll upgrade you to premium after confirmation.
""".format(environ['GPAY_REFERRAL_CODE'], environ['GPAY_REFERRAL_CODE'], environ['PAYMENT_LINK']))

ADMIN_COMMANDS_TXT = textwrap.dedent("""
1. /push - Send a push notification
2. /revert - Delete a sent push notification
3. /clean - Clean Lecture & Practical records
4. /elevate - Make a user premium
5. /extend - Extend a user's premium period
""")

REPLY_UNKNOWN = [
    "Seems like I'm not programmed to understand this yet.", 
    "I'm not a fully functional A.I. ya know?",
    "The creator didn't prepare me for this.", 
    "I'm not sentient...yet! 🤖", 
    "Damn you're dumb.", 
    "42",
    "We cannot afford machine learning to make this bot smart!", 
    "We don't use NLP.", 
    "I really wish we had a neural network.",
    "Sorry, did you say something? I wasn't listening.", 
    ]

TIPS = [
    "Always use /attendance command before using /until80 or /bunk to get latest figures.",
    "The Aldel MIS gets updated at 6PM everyday.", 
    "The /until80 function gives you the number of lectures you must attend *consecutively* before you attendance is 80%.",\
    "The bunk calculator's figures are subject to differ from actual values depending upon a number of factors such as:\
    \nMIS not being updated.\
    \nCancellation of lectures.\
    \nMass bunks. 😝", 
    "`/itinerary all` gives complete detailed attendance report since the start of semester."
    ]

HELP = textwrap.dedent("""
    1. /register - Register yourself
    2. /attendance - Fetch attendance from the MIS website
    3. /itinerary - Fetch detailed attendance
    4. /profile - See your student profile
    5. /results - Fetch unit test results
    6. /bunk - Calculate % \drop/rise
    7. /until80 - No. of lectures to attend consecutively until total attendance is 80%
    8. /until - No. of lectures until X%
    9. /target - Set a attendance percentage target
    10. /edit_target - Edit your attendance target
    11. /cancel - Cancel registration
    12. /delete - Delete your credentials
    13. /help - See this help message
    14. /tips - Random tips
    15. /subscription - See subscription details
    """)

GIFS = [
    "https://media.giphy.com/media/uSJF1fS5c3fQA/giphy.gif",
    "https://media.giphy.com/media/lRmjNrQZkKVuE/giphy.gif",
    "https://media.giphy.com/media/1zSz5MVw4zKg0/giphy.gif",
    "https://media.giphy.com/media/jWOLrt5JSNyXS/giphy.gif",
    "https://media.giphy.com/media/27tE5WpzjK0QEEm0WC/giphy.gif",
    "https://media.giphy.com/media/46itMIe0bkQeY/giphy.gif",
    "https://i.imgur.com/CoWZ05t.gif",
    "https://media.giphy.com/media/48YKCwrp4Kt8I/giphy.gif"
    ]