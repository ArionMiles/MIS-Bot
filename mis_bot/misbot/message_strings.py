"""
Contains all message string templates
"""
from os import environ
import textwrap

SUBSCRIPTION_MSG = textwrap.dedent("""
There is a one-time fee of ₹50/- per semester.

Payment is accepted via UPI. All UPI apps work (PayTM/PhonePe/GPay/etc.)

To upgrade, make a payment at this link:
[PAYMENT LINK]({})

After payment, [send me a message](t.me/Arion_Miles) and 
I'll upgrade you to premium after confirmation.
""".format(environ['PAYMENT_LINK']))

ADMIN_COMMANDS_TXT = textwrap.dedent("""
1. /push - Send a push notification
2. /revert - Delete a sent push notification
3. /clean - Clean Lecture & Practical records
4. /elevate - Make a user premium
5. /extend - Extend a user's premium period
""")
