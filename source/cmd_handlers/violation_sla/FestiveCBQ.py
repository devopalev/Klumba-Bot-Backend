from telegram.ext import CallbackQueryHandler
from telegram import Update
from typing import Optional, Union

import source.creds as creds


class FestiveCBQ(CallbackQueryHandler):
    def check_update(self, update: object) -> Optional[Union[bool, object]]:
        if isinstance(update, Update) and update.callback_query:
            if update.callback_query.message.chat_id == creds.FESTIVE_APPROVAL_CHAT_ID:
                return super().check_update(update)
        return None


class FestiveUnapprovedCBQ(CallbackQueryHandler):
    def check_update(self, update: object) -> Optional[Union[bool, object]]:
        if isinstance(update, Update) and update.callback_query:
            if update.callback_query.message.chat_id in creds.FESTIVE_UNAPPROVED_SUBDIVS.values():
                return super().check_update(update)
        return None
