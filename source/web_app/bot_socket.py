import json
import socket
import logging
import platform
import sys
import threading
import queue
import time
import uuid
import pickle
from source.web_app.Tasks import Task


logger = logging.getLogger(__name__)


class ApiConnector:
    def __init__(self):
        os_ = platform.system()
        if os_ == "Linux":
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.bind("api.sock")
        elif os_ == "Windows":
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.bind(("127.0.0.1", 1250))
        else:
            raise SystemError("Неизвестная ОС")
        self.sock.listen(1)
        self._lock = threading.Lock()
        self._queue_recv = queue.Queue()
        self._conn = None
        logger.info("Create bot api socket")
        threading.Thread(target=self._core, daemon=True).start()

    def _core(self):
        conn = None
        while True:
            try:
                logger.debug("Listen bot api socket")
                conn, addr = self.sock.accept()
                with self._lock:
                    self._conn = conn
                logger.info(f"{addr} connect bot api socket")
                while True:
                    data = conn.recv(1048576)
                    task: Task = pickle.loads(data)
                    if task.this_ping:
                        with self._lock:
                            self._conn.sendall(Task(Task.action_pong).dumps())
                    else:
                        logger.debug(f"RECV Api Socket: {task}")
                        self._queue_recv.put(task)

            except Exception as err:
                with self._lock:
                    self._conn = None
                logger.error(f"Error bot api socket: {err}", exc_info=True)
            finally:
                if conn:
                    conn.close()

    def recv(self):
        return self._queue_recv.get()

    def send(self, task: Task):
        try:
            with self._lock:
                if self._conn:
                    self._conn.sendall(task.dumps())
                    logger.debug(f"SEND data bot api socket: {task}")
        except Exception as err:
            logger.error(f"Не удалось отправить ответ в API: {err}")

