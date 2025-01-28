#
# Created as a part of the INVENTOR project (TAČR Trend No. FW10010040, 2024-2026).
# Author: Dias Assatulla, xassat00@stud.fit.vutbr.cz
# Institution: Brno University of Technology, Faculty of Information Technology, Czech Republic
# Date: 22/11/2024
#

#!/usr/bin/env python3
import json
from multiprocessing import Queue
from security_ldap import run

def monitor_ldap():
    """
    Test the ntp function
    """
    # Load the configuration file:
    with open('test/input.json', 'r') as file:
        config = json.load(file) 
    
    queue = Queue()
    output = run(config,1, queue)
    result = queue.get()

    # Combine the output and queue results:
    combined = {
        "output": output,
        "queue": result
    }
    
    # Write output to the file:
    with open('test/output.json', 'w') as file:
        json.dump(combined, file, indent=4)


def test_monitor_ldap():
    monitor_ldap()