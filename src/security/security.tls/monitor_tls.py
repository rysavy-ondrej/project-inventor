#
# Created as a part of the INVENTOR project (TAČR Trend No. FW10010040, 2024-2026).
# Author: Václav Korvas, xkorva03@stud.fit.vutbr.cz
# Institution: Brno University of Technology, Faculty of Information Technology, Czech Republic
# Date: 22/11/2024
#
import logging
import os
import json
from multiprocessing import Queue
from security_tls import run 

"""
Basic test for the run function to test the dns resolve functionality
Run the test using the following command:
pytest test_dns.py

The test will generate an output.json file with the result
"""

def pytest_configure(config):
    logging.basicConfig(level=logging.INFO)

def test_dns():
    """
    Test the dns_resolve function
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

    # Write output to the file:
    with open('test/output.json', 'w') as file:
        json.dump(combined, file, indent=4)

    assert combined["output"]["status"] != 'error'
    assert combined["queue"]["status"] != 'error'
