from telegram.ext import CallbackContext, JobQueue
from telegram import Chat

import source.creds as creds
import source.TelegramCommons as TgCommons

import source.festive_approvement.BitrixHandlers as BH
import source.festive_approvement.TextSnippets as Txt

STAT_UNPROCESSED_INTERVAL = 30 * 60  # sedonds
STAT_DECLINED_INTERVAL = 30 * 60 + 1  # seconds


def stat_unprocessed(context: CallbackContext):
    unprocessed, subdivs = BH.stat_unprocessed()
    msg = ''

    if unprocessed:
        msg += Txt.UNPROCESSED_STAT_TEMPLATE.format(unprocessed)

    for s_name, s_count in subdivs.items():
        msg += Txt.DECLINED_SUBDIV_STAT_TEMPLATE.format(s_name, s_count)
        subdiv_chat_id = creds.FESTIVE_UNAPPROVED_SUBDIVS.get(s_name)
        subdiv_chat = Chat(bot=context.bot, id=subdiv_chat_id, type=Chat.SUPERGROUP)
        subdiv_msg = Txt.SPECIFIC_SUBDIV_STAT_TEMPLATE.format(s_count)
        TgCommons.send_mdv2_chat(subdiv_chat, subdiv_msg)

    chat = Chat(bot=context.bot, id=creds.FESTIVE_APPROVAL_CHAT_ID, type=Chat.SUPERGROUP)
    TgCommons.send_mdv2_chat(chat, msg)


def jq_add_festive_stats(jq: JobQueue):
    jq.run_repeating(stat_unprocessed, interval=STAT_UNPROCESSED_INTERVAL, first=1)
