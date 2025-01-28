#
# Created as a part of the INVENTOR project (TAČR Trend No. FW10010040, 2024-2026).
# Author: Dias Assatulla, xassat00@stud.fit.vutbr.cz
# Institution: Brno University of Technology, Faculty of Information Technology, Czech Republic
# Date: 22/11/2024
#

#!/usr/bin/env python3
import json
from network_smtp import run
import pytest
from multiprocessing import Queue


"""
    To check how the script work just simply write in cmd:
    sudo pytest test_smtp.py <Enter>
    <Enter>

    and after that u will se the results in output.json

    IF u set send_email_flag to TRUE, run like this:
    sudo pytest -s test_smtp.py <Enter>
"""

def monitor_smtp():
    """
    Using python-nmap (nmap) tests if the targeted hostname with specified ports are opened
    """

    with open('test/input.json', 'r') as file:
        config = json.load(file)


    queue = Queue()
    output = run(config, 1, queue)
    result = queue.get()

    # Combine the output and queue results:
    combined = {
        "output": output,
        "queue": result
    }

    with open('test/output.json', 'w') as file:
        json.dump(combined, file, indent=4)


def test_monitor_smtp():
    monitor_smtp()