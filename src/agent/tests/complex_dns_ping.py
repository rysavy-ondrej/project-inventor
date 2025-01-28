from multiprocessing import Queue

from tests.common import BaseTest

from tests import network_dns_a_1, network_icmp_ping_1


class Test(BaseTest):
    def __init__(self, queue: Queue):
        super().__init__(queue)

    def run(self, params: dict, run_id: int) -> dict:
        message = None
        try:
            domain = params["domain"]

            dns_test = network_dns_a_1.Test(self.queue)
            dns_result = dns_test.run({"domain": domain}, run_id)
            if dns_result["status"] == "error":
                message = {
                    "run_id": run_id,
                    "status": "error",
                    "data": {"description": dns_result["data"]["description"]},
                }
            else:
                ping_test = network_icmp_ping_1.Test(self.queue)
                icmp_result = ping_test.run(
                    {"target": dns_result["data"]["ip"]}, run_id
                )
                if icmp_result["status"] == "error":
                    message = {
                        "run_id": run_id,
                        "status": "error",
                        "data": {"description": icmp_result["data"]["description"]},
                    }
                else:
                    message = {
                        "run_id": run_id,
                        "status": "success",
                        "data": {
                            "ip": dns_result["data"]["ip"],
                            "delay": icmp_result["data"]["delay"],
                        },
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
    return 60
