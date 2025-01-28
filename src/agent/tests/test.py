import json
import time
from multiprocessing import Queue
from random import random

from tests.common import BaseTest


class Test(BaseTest):
    def __init__(self, queue: Queue):
        super().__init__(queue)

    def run(self, params: str, run_id: int) -> None:
        state = random()
        if state < 0.1 and False:  # deadlock
            time.sleep(3600)
            status = "error"
            data = {'description': 'deadlock'}
        elif state < 0.3 and False:  # long task
            seconds = int(100 + random() * 200)
            for _ in range(seconds):
                time.sleep(1)
            status = "error"
            data = {'description': 'long task'}
        else:  # task will finish
            seconds = int(random() * 30)
            for _ in range(seconds):
                time.sleep(1)
            if random() < 0.1:
                status = "error"
                data = {'description': 'bad luck'}
            else:
                status = "success"
                data = {'value': 1}

        message = {"run_id": run_id, "status": status, "data": data}
        self.process_message(message)


def deadline_calculation(params: dict):
    return 300
