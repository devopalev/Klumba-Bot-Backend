import logging
import platform
import sys

import requests
import os
import source.config as cfg
from logging.handlers import RotatingFileHandler
from source import secret


class TelegramHTTPHandler(logging.Handler):
    def __init__(self, token, chat_id):
        super().__init__()
        self.url = f'https://api.telegram.org/bot{token}/sendMessage'
        self.chat_id = chat_id

    def emit(self, record):
        try:
            msg = self.format(record)[:4095]
            data = {'chat_id': self.chat_id, 'text': msg, 'parse_mode': 'HTML'}
            r = requests.post(self.url, json=data)
            if not r.ok:
                self.handleError(record)
        except Exception:
            self.handleError(record)


def _init_dir():
    os_ = platform.system()

    if os_ == "Linux":
        path = "/var/log/klumba_bot"
    elif os_ == "Windows":
        path = os.path.join(os.getcwd(), os.path.abspath("log"))
    else:
        raise SystemError("unknown platform")

    if not os.path.exists(path):
        os.mkdir(path)
    return path


def init_logger():
    path_dir = _init_dir()

    logger = logging.getLogger("source")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(cfg.LOG_FORMAT)

    # Handlers FULL
    file_name = os.path.join(path_dir, "FULL.log")
    full_handler = logging.handlers.RotatingFileHandler(filename=file_name, maxBytes=cfg.LOG_FILE_SIZE, backupCount=1,
                                                        encoding="utf-8")
    full_handler.setLevel(logging.DEBUG)
    full_handler.setFormatter(formatter)
    logger.addHandler(full_handler)

    # Handlers DEBUG
    file_name = os.path.join(path_dir, "DEBUG.log")
    handler = logging.handlers.RotatingFileHandler(filename=file_name, maxBytes=cfg.LOG_FILE_SIZE, encoding="utf-8")
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Handlers INFO
    file_name = os.path.join(path_dir, "INFO.log")
    handler = logging.handlers.RotatingFileHandler(filename=file_name, maxBytes=cfg.LOG_FILE_SIZE, encoding="utf-8")
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Handlers WARNING
    file_name = os.path.join(path_dir, "WARNING.log")
    handler = logging.handlers.RotatingFileHandler(filename=file_name, maxBytes=cfg.LOG_FILE_SIZE, encoding="utf-8")
    handler.setLevel(logging.WARNING)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    handler = TelegramHTTPHandler(secret.TG_BOT_TOKEN, secret.NOTIFICATION_CHAT)
    handler.formatter = logging.Formatter(cfg.LOG_TG_FORMAT)
    handler.setLevel(logging.WARNING)
    # logger.addHandler(handler)

    # Handlers ERROR
    file_name = os.path.join(path_dir, "ERROR.log")
    handler = logging.handlers.RotatingFileHandler(filename=file_name, maxBytes=cfg.LOG_FILE_SIZE, encoding="utf-8")
    handler.setLevel(logging.ERROR)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Handlers CRITICAL
    file_name = os.path.join(path_dir, "CRITICAL.log")
    handler = logging.handlers.RotatingFileHandler(filename=file_name, maxBytes=cfg.LOG_FILE_SIZE, encoding="utf-8")
    handler.setLevel(logging.CRITICAL)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Корневой логгер (логируются библиотеки)
    logging.basicConfig(level=logging.INFO, handlers=[full_handler], format=cfg.LOG_FORMAT)
