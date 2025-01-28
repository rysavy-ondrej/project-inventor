#
# Created as a part of the INVENTOR project (TAČR Trend No. FW10010040, 2024-2026).
# Author: Pavel Horáček, <xhorac19@fit.vutbr.cz>
# Institution: Brno University of Technology, Faculty of Information Technology, Czech Republic
# Date: 22/11/2024
#

import sys
import json
import xml.etree.ElementTree as ET
from multiprocessing import Queue

# Add webapp.http folder into PATH so that it can be imported
sys.path.insert(0, '../webapp.http')

from webapp_http import run as http_run


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


def ordered_json(json_obj):
    """
    Sorts a JSON object

    Parameters:
    -  json_obj: JSON object

    Returns:
    -  Sorted JSON object

    """
    if isinstance(json_obj, dict):
        new_dict = {k: ordered_json(v) for k, v in json_obj.items()}
        return new_dict
    if isinstance(json_obj, list):
        return [ordered_json(x) for x in json_obj].sort()
    else:
        return json_obj


def canonical_xml(xml_obj: str):
    """
    Returns a canonical XML data string

    Parameters:
    -  xml_obj: String with XML object

    Returns:
    -  str: Canonical XML object
    """
    return ET.canonicalize(xml_data=xml_obj)


def match_partial_json(original_json, compare_json):
    """
    Compares two JSON objects with partial match.
    The JSON objects have to be sorted with ordered_json function before calling this function.

    Parameters:
    -  original_json: Original JSON object received
    -  compare_json: JSON object to compair against

    Returns:
    -  bool: True if the JSON objects match, False otherwise
    """
    if isinstance(original_json, dict) and isinstance(compare_json, dict):
        for key in compare_json.keys():
            if key not in original_json.keys():
                return False
            return match_partial_json(original_json[key], compare_json[key])
    elif isinstance(original_json, list) and isinstance(compare_json, list):
        while original_json != [] and compare_json != []:
            matched = match_partial_json(original_json[0], compare_json[0])
            if matched:
                original_json.pop(0)
                compare_json.pop(0)
            else:
                original_json.pop(0)
        return compare_json == []
    elif original_json == compare_json:
        return True
    else:
        return False


def match_partial_xml(original_xml: ET.Element, compare_xml: ET.Element):
    """
    Compares two XML objects with partial match.
    The XML objects have to be created from their canonized versions
    with canonical_xml function before calling this function.

    Parameters:
    -  original_xml: Original XML object received
    -  compare_xml: XML object to compair against

    Returns:
    -  bool: True if the XML objects match, False otherwise
    """

    original_attribs = original_xml.attrib
    compare_attribs = compare_xml.attrib

    # Check that original contains all attributes that compare has
    # This tries to create a dictionary with attributes of compare side that aren't inside original,
    # which would indicate a fail state
    if {k:v for k,v in compare_attribs.items()
        if (k in original_attribs.keys() and original_attribs[k] != compare_attribs[k]) or
           (k not in original_attribs.keys())}:
        return False

    if original_xml.tag != compare_xml.tag:
        return False

    if original_xml.text != compare_xml.text or original_xml.tail != compare_xml.tail:
        return False

    original_queue = [e for e in original_xml]
    compare_queue = [e for e in compare_xml]

    while original_queue != [] and compare_queue != []:
        matched = match_partial_xml(original_queue[0], compare_queue[0])
        if matched:
            original_queue.pop(0)
            compare_queue.pop(0)
        else:
            original_queue.pop(0)

    return compare_queue == []


def rest_query(http_response: dict, params: dict, run_id: int) -> dict:
    """
    Queries a REST endpoint

    Parameters:
    -   target_host (str): URL/domain name/IP of endpoint
    -`  config (dict): Configuration values

    Returns:
    -   dict: Dictionary with response information
    """

    info = {
        "run_id": run_id,
        "status": "completed"
    }

    if "match_data" in params:
        if params["match_type"] == "json":
            body_json = ordered_json(json.loads(http_response["body"]))
            match_json = ordered_json(json.loads(params["match_data"]))

            if params["match_scope"] == "full":
                info["match"] = body_json == match_json
            if params["match_scope"] == "partial":
                info["match"] = match_partial_json(body_json, match_json)
        if params["match_type"] == "xml":
            body_xml = canonical_xml(http_response["body"])
            match_xml = canonical_xml(params["match_data"])

            if params["match_scope"] == "full":
                info["match"] = body_xml == match_xml
            if params["match_scope"] == "partial":
                info["match"] = match_partial_xml(ET.fromstring(body_xml), ET.fromstring(match_xml))
    return info


def run(params: dict, run_id: int, queue: Queue = None) -> dict:
    if params is not None:
        try:
            if "match_type" in params:
                params["match_type"] = params["match_type"].lower()
                if "match_data" not in params:
                    raise ValueError(f"Using 'match_type' argument without 'match_data'")
                if params["match_type"] not in ["json", "xml"]:
                    raise ValueError(f"Invalid 'match_type' argument: {params['match_type']}")

                if params["match_type"] == "json":
                    try:
                        json.loads(params["match_data"])
                    except json.JSONDecodeError:
                        raise ValueError(f"Invalid JSON data in 'match_data' argument")

                if params["match_type"] == "xml":
                    try:
                        ET.fromstring(params["match_data"])
                    except ET.ParseError:
                        raise ValueError(f"Invalid XML data in 'match_data' argument")
            else:
                params["match_type"] = "json"

            if "match_scope" in params:
                params["match_scope"] = params["match_scope"].lower()
                if "match_data" not in params:
                    raise ValueError(f"Using 'match_type' argument without 'match_data'")
                if params["match_scope"] not in ["full", "partial"]:
                    raise ValueError(f"Invalid 'match_type' argument: {params['match_scope']}")
            else:
                params["match_scope"] = "full"

            http_response = http_run(params, run_id, queue)
            if "status" in http_response and http_response["status"] == "error":
                res = http_response
            else:
                res = rest_query(http_response, params, run_id)
                res["http_outputs"] = http_response

        except Exception as e:
            res = error_json("REST_MONITOR_ERROR", f"Error running REST monitor: {e}")
    else:
        res = error_json("INVALID_CONFIGURATION", "Invalid configuration file")

    if queue is not None:
        queue.put(res)

    return res
