import re
import subprocess
from multiprocessing import Queue

from tests.common import BaseTest


class Test(BaseTest):
    def __init__(self, queue: Queue):
        super().__init__(queue)

    def run(self, params: dict, run_id: int) -> dict:
        message = None
        try:
            target = params["target"]
            ping = subprocess.Popen(
                ["ping", target, "-n", "1"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
            )
            output = ping.communicate()
            if ping.returncode == 0:
                pattern = r"Average = (\d+)"
                delay = re.findall(pattern, output[0].decode())[0]
                message = {
                    "run_id": run_id,
                    "status": "success",
                    "data": {"delay": delay},
                }
            else:
                message = {
                    "run_id": run_id,
                    "status": "error",
                    "data": {"description": "no reply"},
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
    return params["packet_count"] * params["timeout"] + 10
