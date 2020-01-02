"""
Contains all message string templates
"""
import textwrap

SUBSCRIPTION_MSG = textwrap.dedent("""
    There is a one-time fee of ₹50/- per semester.
    
    Payment is accepted via UPI. All UPI apps work (PayTM/PhonePe/GPay/etc.)
    To upgrade, make a payment at this link:

    [PAYMENT LINK]({})
    After payment, send me a message @Arion_Miles and 
    I'll upgrade you to premium after confirmation.
    """)
