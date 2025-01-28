#
# Created as a part of the INVENTOR project (TAČR Trend No. FW10010040, 2024-2026).
# Author: Dias Assatulla, xassat00@stud.fit.vutbr.cz
# Institution: Brno University of Technology, Faculty of Information Technology, Czech Republic
# Date: 22/11/2024
#

#!/usr/bin/env python3
import json
import pytest
from network_imap import run
from multiprocessing import Queue


"""
    To check how the script work just simply write in cmd:
    pytest test_smtp.py <Enter>
    <Enter>

    and after that u will se the results in output.json
"""

def monitor_imap():
    """
    Using python-nmap (nmap) tests if the targeted hostname with specified ports are opened
    """

    with open('test/input.json', 'r') as file:
        config = json.load(file)

    
    queue = Queue()
    output = run(config, 1, queue)
    result = queue.get()

    combined = {
        "output": output,
        "queue": result
    }

    with open('test/output.json', 'w') as file:
        json.dump(combined, file, indent=4)


def test_monitor_imap():
    monitor_imap()