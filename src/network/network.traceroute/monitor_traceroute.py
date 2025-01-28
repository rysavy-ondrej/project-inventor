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

def test_traceroute():
    """
    Test the traceroute function
    """
    directory = 'test'
    filename = 'output.json'

    # Load the configuration file
    with open('test/input.json', 'r') as f:
        config = json.load(f)

    # Create a queue
    q = Queue()
    output = run(config, 1, q)
    result = q.get()

    # Combine the results
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

    assert combined['output']['status'] != 'error'
    assert combined['queue']['status'] != 'error'
