from abc import ABC, abstractmethod
from multiprocessing import Queue
from typing import Dict, Optional


class BaseTest(ABC):
    def __init__(self, queue: Queue) -> None:
        self.queue = queue

    @abstractmethod
    def run(self, params: dict, run_id: int) -> Optional[Dict]:
        pass

    def process_message(self, message: Dict) -> None:
        if self.queue is None or message is None:
            return
        self.queue.put(message)
