import os
#just tells the system where the file flags are
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHECKIN_FLAG = os.path.join(BASE_DIR, '.checkin_submitted')
CANCEL_FLAG  = os.path.join(BASE_DIR, '.checkin_cancelled')
