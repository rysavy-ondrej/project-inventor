#
# Created as a part of the INVENTOR project (TAČR Trend No. FW10010040, 2024-2026).
# Author: Pavel Horáček, <xhorac19@fit.vutbr.cz>
# Institution: Brno University of Technology, Faculty of Information Technology, Czech Republic
# Date: 22/11/2024
#

import json
import os.path
import re
import stat
import subprocess

from multiprocessing import Queue

GRADE_REASON_REGEX = re.compile(r"grade_cap_reason_\d+")
ERROR_REASON_REGEX = re.compile(r'"scanProblem"[^}]*?,[^}]*?"finding"[^}]*?:[^}]*?"([^}]*?)"')
IGNORED_FINDINGS = ["rating_spec", "rating_doc"]
SEVERITY_LEVELS = ["INFO", "OK", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
TESTSSL_DEF_PATH = "./script/testssl.sh"

def remove_finding_redundant(finding: dict) -> dict:
    """
    Removes the IP and PORT from testssl finding

    Parameters:
    -   finding (dict):  The finding

    Returns:
    -   dict: Finding without redundancy

    """
    if "ip" in finding:
        del finding["ip"]
    if "port" in finding:
        del finding["port"]
    return finding


def load_config(file):
    """
    Load the json configuration file

    Parameters:
    -   file (str):  The path to the json configuration file

    Returns:
    -   dict: The configuration file as a dictionary
    """
    try:
        with open(file, 'r') as f:
            config = json.load(f)
            return config
    except Exception as e:
        err_msg = error_json("INVALID CONFIGURATION", f'Error loading configuration file: {e}')
        print(err_msg)
        return None


def error_json(code, message) -> dict:
    """
    Create an error json message

    Parameters:
    -   code (int):  The error code
    -   message (str): The error message

    Returns:
    -   dict: The error message as a json
    """
    data = {'status': 'error',
            'error': {'error_code': code, 'description': message}}
    return data


def gather_sec_info(target_host: str, script_args: list, script_path: str, run_id: int) -> dict:
    """
    Queries an HTTP endpoint

    Parameters:
    -   target_host (str): URL/domain name/IP of endpoint
    -`  config (dict): Configuration values

    Returns:
    -   dict: Dictionary with response information
    """

    if not os.path.isfile(script_path):
        raise Exception(f"Path {script_path} does not lead to any file")

    # Make the script executable if it isn't
    fstat = os.stat(script_path)[stat.ST_MODE]
    if not stat.S_IXUSR & fstat:
        os.chmod(script_path, fstat | stat.S_IEXEC)

    # URI is always last
    script_call = [script_path] + script_args + [target_host]

    rc = subprocess.run(' '.join(script_call), shell=True, capture_output=True, text=True)

    if rc.returncode != 0:
        problem_string = ERROR_REASON_REGEX.search(rc.stderr, re.DOTALL)
        if problem_string is not None and len(problem_string.groups()) == 1:
            raise Exception(
                f"testssl.sh returned non-zero code: {rc.returncode}, and error string: \"{problem_string[1]}\"")
        else:
            raise Exception(f"testssl.sh returned non-zero code: {rc.returncode}")
    findings = json.loads(rc.stderr)

    # Elements with _ts suffix are in testssl JSON format
    # Every testssl JSON finding has a format of (every element is a string):
    # {
    #   "id": identifier
    #   "finding": explanation of the finding
    #   "severity" severity of the finding
    #   "ip": uri/ip
    #   "port": L4 port
    #   "cve": (only in vulnerabilities) CVE identifier
    #   "cwe": (only in vulnerabilities) CWE identifier
    # }

    info = {
        "run_id": run_id,
        "status": "completed"
    }

    # Remove ignored findings and remove IP/PORT from them
    findings = list(map(remove_finding_redundant, filter((lambda x: (x["id"] not in IGNORED_FINDINGS)), findings)))

    # Total grade
    grade_ts = next((x for x in findings if x["id"] == "overall_grade"), None)
    if grade_ts is not None:
        info.update({"grade": grade_ts["finding"]})

    # Reasons behind grade
    grade_reasons_ts = list(filter((lambda x: (GRADE_REASON_REGEX.match(x["id"]))), findings))
    if len(grade_reasons_ts) > 0:
        info.update({"grade_reasons": [x["finding"] for x in grade_reasons_ts]})

    # Total score
    score_ts = next((x for x in findings if x["id"] == "final_score"), None)
    if score_ts is not None:
        info.update({"final_score": int(score_ts["finding"])})

    info.update({"findings": {}})

    # Split by severity
    for level in SEVERITY_LEVELS:
        findings_bylevel = list(filter((lambda x: x["severity"] == level), findings))
        if len(findings_bylevel) > 0:
            info["findings"].update({level: findings_bylevel})

    return info


def run(params: dict, run_id: int, queue: Queue = None) -> dict:
    if params is not None:
        try:
            script_args = ["--quiet", "--color 0", "--jsonfile /dev/stderr"]

            # target_url is mandatory
            if "target_url" not in params:
                raise ValueError("Missing 'target_url' argument")
            target = params.pop("target_url")

            # Timeouts are in seconds
            if "connect_timeout" in params:
                script_args.append(f"--connect-timeout {params['connect_timeout']}")

            if "openssl_timeout" in params:
                script_args.append(f"--openssl-timeout {params['openssl_timeout']}")

            if "script_path" in params:
                res = gather_sec_info(target, script_args, params["script_path"], run_id)
            else:
                res = gather_sec_info(target, script_args, TESTSSL_DEF_PATH, run_id)

        except Exception as e:
            res = error_json("HTTP_SECURITY_MONITOR_ERROR", f'Error running HTTP security monitor: {e}')

    else:
        res = error_json("INVALID_CONFIGURATION", "Invalid configuration file")

    if queue is not None:
        queue.put(res)

    return res
