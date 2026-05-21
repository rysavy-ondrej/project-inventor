#
# Created as a part of the INVENTOR project (TAČR Trend No. FW10010040, 2024-2026).
# Author: Václav Korvas, xkorva03@stud.fit.vutbr.cz
# Institution: Brno University of Technology, Faculty of Information Technology, Czech Republic
# Date: 22/11/2024
#
import logging
import json
import os
from network_traceroute import run
from multiprocessing import Queue

def pytest_configure(config):
    logging.basicConfig(level=logging.INFO)

def monitor_traceroute():
    """
    Test the traceroute function
    """
    directory = 'test'
    filename = 'output.json'

    with open('test/input.json', 'r') as f:
        config = json.load(f)

    q = Queue()
    output = run(config, 1, q)
    result = q.get()

    combined = {
        "output": output if isinstance(output, dict) else json.loads(output),
        "queue": result if isinstance(result, dict) else json.loads(result)
    }

    if not os.path.exists(directory):
        os.makedirs(directory)

    filepath = os.path.join(directory, filename)
    with open(filepath, 'w') as f:
        json.dump(combined, f, indent=4)

    assert combined['output']['status'] != 'error'
    assert combined['queue']['status'] != 'error'

def test_traceroute():
    monitor_traceroute()
