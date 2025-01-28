#
# Created as a part of the INVENTOR project (TAČR Trend No. FW10010040, 2024-2026).
# Author: Pavel Horáček, <xhorac19@fit.vutbr.cz>
# Institution: Brno University of Technology, Faculty of Information Technology, Czech Republic
# Date: 22/11/2024
#

import json
from multiprocessing import Queue
import webapp_security as security

def test_service():
    with open('test/input.json', 'r') as file:
        config = json.load(file)

    queue = Queue()
    output = security.run(config, 1, queue)
    result = queue.get()

    # Combine the output and queue results:
    combined = {
        "output": output,
        "queue": result
    }

    with open('test/output.json', 'w') as file:
        json.dump(combined, file, indent=4)
