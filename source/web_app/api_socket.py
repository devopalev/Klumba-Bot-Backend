import json
import socket
import logging
import platform
import threading
import queue
import time
import uuid
import pickle
from source.web_app.Tasks import Task

logger = logging.getLogger(__name__)


# Singleton - Fabric method
class BotConnector:
    _instance = None

    def __init__(self):
        self.queue = queue.Queue()
        self._lock = threading.RLock()
        self._responses = {}
        self._wait_id = []
        self._conn = None
        threading.Thread(target=self.core, daemon=True).start()
        threading.Thread(target=self.keepalive).start()

    @classmethod
    def build(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @staticmethod
    def _create_socket():
        os_ = platform.system()
        if os_ == "Linux":
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            connect_params = "api.sock"
        elif os_ == "Windows":
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            connect_params = ("127.0.0.1", 1250)
        else:
            raise SystemError("Неизвестная ОС")

        sock.connect(connect_params)
        return sock

    def keepalive(self):
        while True:
            try:
                with self._lock:
                    if self._conn:
                        self._conn.sendall(Task(Task.action_ping).dumps())
            except Exception as err:
                self.sock_error(err)
            time.sleep(1)

    def connect(self):
        count_error = 0
        while True:
            try:
                sock = self._create_socket()
                with self._lock:
                    self._conn = sock
                break
            except Exception as err:
                if count_error == 0 or count_error == 300:
                    logger.error(f"Не удалось подключиться к боту: {err}")
                    count_error = 0
                count_error += 1
            time.sleep(1)

    def sock_error(self, err):
        with self._lock:
            if self._conn:
                try:
                    self._conn.close()
                except Exception as err:
                    logger.warning(f"Не удалось закрыть сокет, возможно он уже закрыт: {err}")
            self._conn = None
            self.connect()
        logger.error(f"Error bot api socket: {err}", exc_info=True)

    def core(self):
        while True:
            try:
                self.connect()
                logger.info(f"Connect bot api socket")
                time.sleep(1)
                while True:
                    if self._conn:
                        data = self._conn.recv(1048576)
                        task: Task = pickle.loads(data)
                        if not task.this_pong:
                            logger.debug(f"RECV Bot Socket: {task}")
                            with self._lock:
                                self._responses.update({task.id: task})
                    else:
                        break
            except Exception as err:
                self.sock_error(err)

    def send(self, task: Task, wait_answer=False):
        try:
            with self._lock:
                if self._conn:
                    if wait_answer:
                        while True:
                            key = uuid.uuid4().hex
                            if key not in self._wait_id:
                                self._wait_id.append(key)
                                break
                        task.id = key
                    self._conn.sendall(task.dumps())
                    logger.debug(f"SEND data bot api socket: {task}")
                else:
                    raise ConnectionError("Не удалось отправить данные в сокет")
        except Exception as err:
            logger.error(f"Не удалось отправить запрос в API: {err}", exc_info=True)
            return

        if wait_answer:
            for _ in range(200):
                with self._lock:
                    if key in self._responses:
                        self._wait_id.remove(key)
                        return self._responses.pop(key)
                time.sleep(0.05)
            with self._lock:
                self._wait_id.remove(key)
            raise TimeoutError("Не дождался ответа от сокета")
