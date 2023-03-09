import source.logger
import threading
import source.TelegramWorker as TgWorker
import source.StorageWorker as StorageWorker
import source.http_server.HTTPServer as HTTPServer


def main():
    source.logger.init_logger()
    http_daemon = threading.Thread(name='bot_http_server', daemon=True,
                                   target=HTTPServer.http_serve)
    http_daemon.start()

    StorageWorker.maintain_storage()
    TgWorker.run()


if __name__ == "__main__":
    main()
