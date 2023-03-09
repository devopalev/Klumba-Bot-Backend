import logging
import threading
import source.TelegramWorker as TgWorker
import source.StorageWorker as StorageWorker
import source.http_server.HTTPServer as HTTPServer
from source import config as cfg

# journalctl logging when running via systemctl
logging.basicConfig(level=cfg.LOG_LEVEL, format=cfg.LOG_FORMAT)


def main():
    http_daemon = threading.Thread(name='bot_http_server', daemon=True,
                                   target=HTTPServer.http_serve)
    http_daemon.start()

    StorageWorker.maintain_storage()
    TgWorker.run()


main()
