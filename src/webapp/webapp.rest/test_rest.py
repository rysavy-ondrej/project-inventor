#
# Created as a part of the INVENTOR project (TAČR Trend No. FW10010040, 2024-2026).
# Author: Pavel Horáček, <xhorac19@fit.vutbr.cz>
# Institution: Brno University of Technology, Faculty of Information Technology, Czech Republic
# Date: 22/11/2024
#

import logging
import json
from multiprocessing import Queue
import webapp_rest as rest


def pytest_configure(config):
    logging.basicConfig(level=logging.INFO)


def test_xml_match_partial():
    with open('test/inputXml.json', 'r') as file:
        config = json.load(file)

    output = rest.run(config, 1, None)
    assert "match" in output and output["match"] is True


def test_json_match_partial():
    with open('test/inputJson.json', 'r') as file:
        config = json.load(file)

    output = rest.run(config, 1, None)
    assert "match" in output and output["match"] is True


def test_service():
    with open('test/input.json', 'r') as file:
        config = json.load(file)

    queue = Queue()
    output = rest.run(config, 1, queue)
    result = queue.get()

    # Combine the output and queue results:
    combined = {
        "output": output,
        "queue": result
    }

    with open('test/output.json', 'w') as file:
        json.dump(combined, file, indent=4)
