import socket
import time
from multiprocessing import Queue

from tests.common import BaseTest


class Test(BaseTest):
    def __init__(self, queue: Queue):
        super().__init__(queue)

    def run(self, params: dict, run_id: int) -> dict:
        message = None
        try:
            ip = params["ip"]
            port = params["port"]

            message = "version"
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            before = time.time()
            sock.sendto(message.encode("utf-8"), (ip, port))
            sock.recv(1024)
            after = time.time()
            rtt_delay = after - before
            sock.close()
            message = {
                "run_id": run_id,
                "status": "success",
                "data": {"delay": rtt_delay},
            }
        except:
            message = {
                "run_id": run_id,
                "status": "error",
                "data": {"description": "exception"},
            }
        finally:
            self.process_message(message)
        return message


def deadline_calculation(params: dict):
    return 10
