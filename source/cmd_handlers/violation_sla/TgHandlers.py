import threading
from telegram.ext import ConversationHandler, MessageHandler, CallbackQueryHandler, Filters, CallbackContext
from telegram import Update, Chat, InlineKeyboardButton, InputMediaPhoto


class Event:
    def __init__(self, deal_id, text, bot):
        self.deal_id = deal_id
        self.text = text
        self.massage = None
        self.bot = bot

    def send(self):
        pass


class EventControl:
    _lock = threading.Lock()
    _events = {}

    @classmethod
    def timer(cls):
        pass

    @classmethod
    def add(cls, ):
        pass

# ==========================
def violation_event(context: CallbackContext):
    deal_id = None
    text = None


def comment_request(update: Update, context: CallbackContext):
    pass


def send_kk(update: Update, context: CallbackContext):
    pass


def create_reclamation():
    pass


def violation_not_found():
    pass

# ======================



# FESTIVE_CB_HANDLER = FestiveCBQ.FestiveCBQ(callback=festive_decision, pattern=Txt.FESTIVE_ACTION_PATTERN)
# FESTIVE_MESSAGE_HANDLER = MessageHandler(Filters.text & Filters.chat(creds.FESTIVE_APPROVAL_CHAT_ID), festive_comment)
# FESTIVE_CV_HANDLER = ConversationHandler(entry_points=[FESTIVE_CB_HANDLER],
#                                          states={
#                                              State.WRITING_DECLINE_COMMENT: [FESTIVE_MESSAGE_HANDLER]
#                                          },
#                                          fallbacks=[MessageHandler(Filters.all, fallback),
#                                                     CallbackQueryHandler(callback=fallback,
#                                                                          pattern=GlobalTxt.ANY_STRING_PATTERN)])
#
# FESTIVE_REAPPROVE_HANDLER = FestiveCBQ.FestiveUnapprovedCBQ(callback=festive_reapprove,
#                                                             pattern=Txt.FESTIVE_REAPPROVE_PATTERN)
