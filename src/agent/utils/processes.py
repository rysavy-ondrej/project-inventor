import json
import multiprocessing

import psutil

from tests.common import BaseTest
from utils import logs


def kill_process(pid: int) -> None:
    logs.debug(f"Killing process with PID {pid}.")
    try:
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            child.kill()
        parent.kill()
    except psutil.NoSuchProcess:
        logs.debug(
            f"Unable to kill the process with PID {pid} because it's no longer running."
        )
    except psutil.Error as e:
        logs.warning(f"Unable to kill the process with PID {pid} because of - {e}.")


def terminate_process(pid: int) -> None:
    logs.debug(f"Terminating process with PID {pid}.")
    try:
        p = psutil.Process(pid)
        p.terminate()
    except psutil.NoSuchProcess:
        logs.debug(
            f"Unable to terminate the process with PID {pid} because it's no longer running."
        )
    except psutil.Error as e:
        logs.warning(
            f"Unable to terminate the process with PID {pid} because of - {e}."
        )


def is_process_alive(pid: int) -> bool:
    return psutil.pid_exists(pid)


def start_new_process(
    test_name: str, test_object: BaseTest, params_json: str, run_id: int
) -> int:
    pid = None
    try:
        params = json.loads(params_json)
        p = multiprocessing.Process(
            target=test_object.run, args=(params, run_id)
        )
        p.start()
        pid = p.pid
    except json.decoder.JSONDecodeError:
        logs.error(f"Test parameters are not in a valid JSON format. Value: {params_json}.")
    except multiprocessing.ProcessError:
        logs.error(
            f"Unable to start a new process for function {test_name} with parameters {params_json}."
        )

    if pid is None:
        logs.error(
            f"Unable to get PID for a new process for function {test_name} with parameters {params_json}."
        )
    else:
        logs.debug(f"Started a new process for function {test_name} with PID {pid}.")
    return pid
