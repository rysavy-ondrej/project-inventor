import socket
from multiprocessing import Queue

from tests.common import BaseTest


class Test(BaseTest):
    def __init__(self, queue: Queue):
        super().__init__(queue)

    def run(self, params: dict, run_id: int) -> dict:
        message = None
        try:
            domain = params["domain"]
            try:
                address_info = socket.getaddrinfo(
                    domain, 443, family=socket.AF_INET, proto=socket.IPPROTO_TCP
                )
                ip = address_info[0][4][0]
                message = {"run_id": run_id, "status": "success", "data": {"ip": ip}}
            except (socket.getaddrinfo, IndexError):
                message = {
                    "run_id": run_id,
                    "status": "error",
                    "data": {"description": "unable to translate domain name"},
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
    return 30
