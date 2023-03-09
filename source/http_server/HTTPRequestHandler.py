from http.server import BaseHTTPRequestHandler
from urllib import parse
import logging

from source.bitrix.BitrixFieldsAliases import *
import source.bitrix.BitrixFieldMappings as BFM
import source.TelegramWorker as TgWorker
import source.http_server.Jobs as Jobs
from source import secret


logger = logging.getLogger(__name__)


class PostHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            logger.info("New POST request accepted!")
            query = parse.urlparse(self.path).query
            query_components = parse.parse_qs(query, keep_blank_values=True)
            logger.info("Accepted query components: %s", query_components)

            if WEBHOOK_SECRET_ALIAS in query_components \
                    and query_components[WEBHOOK_SECRET_ALIAS][0] == creds.API_TOKEN:

                action = query_components[WEBHOOK_ACTION_ALIAS][0]

                if action == BFM.HTTP_ACTION_FESTIVE_PROCESSED:
                    TgWorker.JOB_QUEUE.run_once(callback=Jobs.festive_deal_processed, when=0, context=query_components)
                else:
                    logger.error('Wrong action passed: %s', action)

            else:
                logger.error('Wrong Bitrix webhook secret passed or not provided')

        except Exception as e:
            logger.error('HTTP request handling error: %s', e)

