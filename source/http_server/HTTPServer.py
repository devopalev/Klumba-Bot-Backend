import logging
from http.server import HTTPServer
from socketserver import ThreadingMixIn

import source.config as cfg
import source.http_server.HTTPRequestHandler as HTTPHandler

logger = logging.getLogger(__name__)


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    def finish_request(self, request, client_address):
        request.settimeout(30)
        # "super" can not be used because BaseServer is not created from object
        HTTPServer.finish_request(self, request, client_address)


def http_serve():
    try:
        server = ThreadedHTTPServer((cfg.HTTP_SERVER_ADDRESS, cfg.HTTP_SERVER_PORT),
                                    HTTPHandler.PostHandler)

        while True:
            try:
                server.serve_forever()
            except Exception as e:
                logger.error("HTTP server processing exception: ", e)

    except Exception as e:
        logger.error("HTTP server init exception: ", e)
