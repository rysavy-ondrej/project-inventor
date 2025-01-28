from dataclasses import dataclass
from typing import Dict


@dataclass
class ResultMessage:
    run_id: int
    status: str
    data: Dict

    def __init__(self, message: Dict):
        self.run_id = message["run_id"]
        self.status = message["status"]
        self.data = message["data"]
