import json
import subprocess
from multiprocessing import Queue
import os

def call_node_app(queue):
    input_json_path = "src/webapp/webapp.dynamic/test/input.json"

    node_script = "src/webapp/webapp.dynamic/core/http_dynamic_analysis.js"
    arguments = [input_json_path]
    try:
        result = subprocess.run(['node', node_script] + arguments, capture_output=True, text=True)

        queue.put(json.loads(result.stdout))
        return json.loads(result.stdout)

    except Exception as e:
        print(f"Error running Node.js script: {e}")



def run(params, run_id: int):
    queue = Queue()
    node_script = "core/http_dynamic_analysis.js"
    json_data = json.dumps(params)
    try:
        result = subprocess.run(['node', node_script, json_data], capture_output=True, text=True)
        output = json.loads(result.stdout)

    except Exception as e:
        return {
            "status": "error",
            "error_msg": str(e)
        }

    return output


def test_service():
    run_id = 1
    queue = Queue()
    output = call_node_app(queue)
    result = queue.get()
    combined = {
        "output": {'run_id': run_id, **output},
        "queue": {'run_id': run_id, **result},
    }

    with open('src/webapp/webapp.dynamic/test/output.json', 'w') as file:
        json.dump(combined, file, indent=4)

