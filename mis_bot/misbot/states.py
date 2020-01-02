"""States for ConversationHandlers"""

# general.py
CREDENTIALS, PARENT_LGN = range(2)

# admin.py
NOTIF_MESSAGE, NOTIF_CONFIRM = range(2)
ASK_UUID, CONFIRM_REVERT = range(2)

# bunk.py
CHOOSING, INPUT, CALCULATING = range(3)

# attendance_target.py
SELECT_YN, INPUT_TARGET = range(2)
UPDATE_TARGET = 0

# make_premium
ASK_USERNAME, CONFIRM_USER, INPUT_TIER, INPUT_VALIDITY, CONFIRM_OTP = range(5)