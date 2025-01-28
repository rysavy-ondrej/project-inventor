#
# Created as a part of the INVENTOR project (TAČR Trend No. FW10010040, 2024-2026).
# Author: Václav Korvas, xkorva03@stud.fit.vutbr.cz
# Institution: Brno University of Technology, Faculty of Information Technology, Czech Republic
# Date: 22/11/2024
#
import logging
import json
import os
from multiprocessing import Queue
from network_ping import run

def pytest_configure(config):
    logging.basicConfig(level=logging.INFO)

def monitor_ping():
    """
    Test the ping function
    """
    directory = 'test'
    filename = 'output.json'

    # Load the configuration file:
    with open('test/input.json', 'r') as file:
        config = json.load(file)

    # Run the ping function:
    queue = Queue()
    output = run(config, 1, queue)
    result = queue.get()

    # Combine the output and queue results:
    combined = {
        "output": output if isinstance(output, dict) else json.loads(output),
        "queue": result if isinstance(result, dict) else json.loads(result)
    }

    # Check if the directory exists, if not, create it
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Combine the directory and filename
    filepath = os.path.join(directory, filename)

    # Check if the file exists, if not, create it
    with open(filepath, 'w') as f:
        json.dump(combined, f, indent=4)

    # Perform your assertions on combined result
    assert combined["output"]["status"] != "error"
    assert combined["queue"]["status"] != "error"

def test_monitor_ping():
    monitor_ping()
