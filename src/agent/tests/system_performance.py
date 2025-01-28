from multiprocessing import Queue

import psutil
from tests.common import BaseTest

# result = {}
# transferred_bytes = {}
# data = psutil.net_io_counters(pernic=True, nowrap=True)
# for interface, net_stat in data.items():
#     transferred_bytes[interface] = {"recv": net_stat.bytes_recv, "sent": net_stat.bytes_sent}
#
# time.sleep(30)
#
# data = psutil.net_io_counters(pernic=True, nowrap=True)
# for interface, net_stat in data.items():
#     speed_recv = round((net_stat.bytes_recv - transferred_bytes[interface]["recv"]) / 1024 / 1024, 3)
#     speed_sent = round((net_stat.bytes_sent - transferred_bytes[interface]["sent"]) / 1024 / 1024, 3)
#     result[interface] = {"recv": speed_recv, "sent": speed_sent}
#
# print(result)


class Test(BaseTest):
    def __init__(self, queue: Queue):
        super().__init__(queue)

    def run(self, params: dict, run_id: int) -> None:
        message = None
        try:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            disk = psutil.disk_usage("..").percent

            message = {
                "run_id": run_id,
                "status": "success",
                "data": {"cpu": cpu, "ram": ram, "disk": disk},
            }
        except:
            message = {
                "run_id": run_id,
                "status": "error",
                "data": {"description": "exception"},
            }
        finally:
            self.process_message(message)


def deadline_calculation(params: dict):
    return 10
