#
# Created as a part of the INVENTOR project (TAČR Trend No. FW10010040, 2024-2026).
# Author: Pavel Horáček, <xhorac19@fit.vutbr.cz>
# Institution: Brno University of Technology, Faculty of Information Technology, Czech Republic
# Date: 22/11/2024
#

import base64
import json
import random
import hashlib

import pycurl
import certifi
from multiprocessing import Queue
from io import BytesIO

STATUS_CODES = {
    100: "Continue",
    101: "Switching Protocols",
    102: "Processing",
    103: "Early Hints",
    200: "OK",
    201: "Created",
    202: "Accepted",
    203: "Non-Authoritative Information",
    204: "No Content",
    205: "Reset Content",
    206: "Partial Content",
    207: "Multi-Status",
    208: "Already Reported",
    226: "IM Used",
    300: "Multiple Choices",
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    304: "Not Modified",
    305: "Use Proxy",
    307: "Temporary Redirect",
    308: "Permanent Redirect",
    400: "Bad Request",
    401: "Unauthorized",
    402: "Payment Required",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    407: "Proxy Authentication Required",
    408: "Request Timeout",
    409: "Conflict",
    410: "Gone",
    411: "Length Required",
    412: "Precondition Failed",
    413: "Payload Too Large",
    414: "URI Too Long",
    415: "Unsupported Media Type",
    416: "Range Not Satisfiable",
    417: "Expectation Failed",
    418: "I'm a teapot",  # Very important :)
    421: "Misdirected Request",
    422: "Unprocessable Content",
    423: "Locked",
    424: "Failed Dependency",
    425: "Too Early",
    426: "Upgrade Required",
    428: "Precondition Required",
    429: "Too Many Requests",
    431: "Request Header Fields Too Large",
    451: "Unavailable For Legal Reasons",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
    505: "HTTP Version Not Supported",
    506: "Variant Also Negotiates",
    507: "Insufficient Storage",
    508: "Loop Detected",
    510: "Not Extended",
    511: "Network Authentication Required"
}

WS_RANDCHARS = "!\"#$%&\\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"
WS_MAGICVALUE = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"  # See RFC 6455 Section 1.3
SSE_TIMEOUT = 3000  # How long in ms to wait for SSE response
CURL_HTTP_VERSION_3ONLY = 31  # Missing constant in pycurl


def pycurl_supports_http3() -> bool:
    """
    Returns: True if pycurl has been complied against libcurl compatible with HTTP/3
    """
    return hasattr(pycurl, 'CURL_HTTP_VERSION_3')


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


def curl_httpver_code_2_float(code) -> float:
    """
    Converts the libcurl HTTP version representation to float of that version

    Parameters:
    -   code (int):  The HTTP version code

    Returns:
    -   float: The HTTP version as a float
    """
    if code == pycurl.CURL_HTTP_VERSION_1_0:
        return 1.0
    elif code == pycurl.CURL_HTTP_VERSION_1_1:
        return 1.1
    elif code == pycurl.CURL_HTTP_VERSION_2_0:
        return 2.0
    elif pycurl_supports_http3() and code == pycurl.CURL_HTTP_VERSION_3:
        return 3.0
    elif code == 0:
        return 0.0


def http_query(target_host: str, params: dict, run_id: int) -> dict:
    """
    Queries an HTTP endpoint

    Parameters:
    -   target_host (str): URL/domain name/IP of endpoint
    -`  config (dict): Configuration values

    Returns:
    -   dict: Dictionary with response information
    """
    curl = pycurl.Curl()
    body_bytes = BytesIO()
    headers_bytes = BytesIO()

    # Set CA path
    curl.setopt(pycurl.CAINFO, certifi.where())

    # Set configured IP version
    if params["ip_version"] == 0:
        curl.setopt(pycurl.IPRESOLVE, pycurl.IPRESOLVE_WHATEVER)
    elif params["ip_version"] == 4:
        curl.setopt(pycurl.IPRESOLVE, pycurl.IPRESOLVE_V4)
    elif params["ip_version"] == 6:
        curl.setopt(pycurl.IPRESOLVE, pycurl.IPRESOLVE_V6)

    # Set configured HTTP version
    if params["http_version"] == 1.0:
        curl.setopt(pycurl.HTTP_VERSION, pycurl.CURL_HTTP_VERSION_1_0)
    elif params["http_version"] == 1.1:
        curl.setopt(pycurl.HTTP_VERSION, pycurl.CURL_HTTP_VERSION_1_1)
    elif params["http_version"] == 2.0:
        curl.setopt(pycurl.HTTP_VERSION, pycurl.CURL_HTTP_VERSION_2_PRIOR_KNOWLEDGE)
    elif params["http_version"] == 3.0 and pycurl_supports_http3():
        # CURL_HTTP_VERSION_3ONLY isn't in pycurl as of now
        # Pull request to resolve this has been merged
        # https://github.com/pycurl/pycurl/pull/848
        curl.setopt(pycurl.HTTP_VERSION, CURL_HTTP_VERSION_3ONLY)

    elif params["http_version"] == 0:
        curl.setopt(pycurl.HTTP_VERSION, pycurl.CURL_HTTP_VERSION_NONE)

    # Set total timeout
    curl.setopt(pycurl.TIMEOUT_MS, params["timeout"])

    # Set connection timeout
    curl.setopt(pycurl.CONNECTTIMEOUT_MS, params["connect_timeout"])

    # Set custom HTTP headers
    headers = []
    for header, value in params["headers"].items():
        headers.append(f"{header}: {value}")
    curl.setopt(pycurl.HTTPHEADER, headers)

    if params["follow_redirects"]:
        curl.setopt(pycurl.FOLLOWLOCATION, 1)

    # Set custom HTTP method
    curl.setopt(pycurl.CUSTOMREQUEST, params["http_method"])

    # Authentication
    if "auth_method" in params:
        if params["auth_method"] == "BASIC":
            curl.setopt(pycurl.HTTPAUTH, pycurl.HTTPAUTH_BASIC)
            curl.setopt(pycurl.USERPWD, f"{params['username']}:{params['password']}")
        if params["auth_method"] == "DIGEST":
            curl.setopt(pycurl.HTTPAUTH, pycurl.HTTPAUTH_DIGEST)
            curl.setopt(pycurl.USERPWD, f"{params['username']}:{params['password']}")
        if params["auth_method"] == "BEARER":
            curl.setopt(pycurl.HTTPAUTH, pycurl.XOAUTH2_BEARER)
            curl.setopt(pycurl.XOAUTH2_BEARER, params['token'])

    # Set the HTTP data
    if params["http_data"] != "":
        curl.setopt(pycurl.POSTFIELDS, params["http_data"])

    # Set URL and output buffer
    curl.setopt(pycurl.URL, target_host)
    curl.setopt(pycurl.WRITEFUNCTION, body_bytes.write)
    curl.setopt(pycurl.HEADERFUNCTION, headers_bytes.write)

    # Query HTTP server
    try:
        curl.perform()
    except pycurl.error as e:
        # Skip timeout exception to output info with SSE
        if not params["check_sse"] or e.args[0] != pycurl.E_OPERATION_TIMEDOUT:
            raise pycurl.error(e)

    info = {
        "run_id": run_id,
        "status": "completed"
    }

    info["target_url"] = curl.getinfo(pycurl.EFFECTIVE_URL)

    # IP and port of destination
    info["IP_address"] = curl.getinfo(pycurl.PRIMARY_IP)
    info["port"] = curl.getinfo(pycurl.PRIMARY_PORT)

    # HTTP Status codes
    info["status_code"] = curl.getinfo(pycurl.RESPONSE_CODE)
    if info["status_code"] in STATUS_CODES:  # Search for appropriate status string
        info["status_string"] = STATUS_CODES[info["status_code"]]
    else:
        info["status_string"] = "Unknown status code"

    # HTTP Version
    info["http_version"] = curl_httpver_code_2_float(curl.getinfo(pycurl.INFO_HTTP_VERSION))

    # HTTP Method
    # The EFFECTIVE_METHOD is not yet implemented in pycurl
    # Manually creating the EFFECTIVE_METHOD constant doesn't work due to the way that pycurl is implemented
    # Pull request with a fix has been made
    # https://github.com/pycurl/pycurl/pull/849
    # info["request_method"] = curl.getinfo(pycurl.EFFECTIVE_METHOD)

    # Transfer times
    info["ttfb"] = curl.getinfo(pycurl.STARTTRANSFER_TIME)
    info["connection_time"] = curl.getinfo(pycurl.TOTAL_TIME)

    # Redirect URLs
    info["redirect_count"] = curl.getinfo(pycurl.REDIRECT_COUNT)
    info["redirect_url"] = curl.getinfo(pycurl.REDIRECT_URL)

    # Decode headers and discover body encoding
    info["headers"] = decode_headers(headers_bytes)
    lower_headers = {k.lower(): v for k, v in info["headers"].items()}
    body_encoding = "latin1"  # Default encoding is latin1 as per RFC
    if "content-type" in lower_headers:
        response_encoding = decode_encoding(lower_headers["content-type"])
        if response_encoding != "":
            body_encoding = response_encoding

    info["bytes_received"] = curl.getinfo(pycurl.SIZE_DOWNLOAD)
    info["download_speed"] = curl.getinfo(pycurl.SPEED_DOWNLOAD)

    # Decode body with discovered encoding
    # It is possible that the body is ill-formed, so replace errors with a marker '�'
    if params["body_flag"]:
        info["body"] = body_bytes.getvalue().decode(body_encoding, errors="replace")

    # Output only allowed values
    if "all" not in params["response_values"]:
        info = {k: v for (k, v) in info.items() if k in params["response_values"]}

    # Include WebSocket info if working with WS
    if params["is_ws"]:
        info["ws_key"] = base64.b64encode(params["ws_randomkey"]).decode("ascii")
        if "sec-websocket-accept" in lower_headers:
            acceptance_str = info["ws_key"] + WS_MAGICVALUE
            acceptance_hash = hashlib.sha1(acceptance_str.encode("ascii")).digest()
            acceptance_b64 = base64.b64encode(acceptance_hash).decode("ascii")
            if acceptance_b64 == lower_headers["sec-websocket-accept"]:
                info["ws_valid"] = True
            else:
                info["ws_valid"] = False
        else:
            info["ws_valid"] = False

    if params["check_sse"]:
        if "content-type" in lower_headers and lower_headers["content-type"].lower() == "text/event-stream":
            info["sse_valid"] = True
        else:
            info["sse_valid"] = False
    return info


def decode_headers(headers_bytes: BytesIO) -> dict:
    """
    Decodes HTTP headers from raw bytes into dictionary

    Parameters:
    -   bytes (BytesIO): Raw bytes of the HTTP headers

    Returns:
    -   dict: String pairs with HTTP headers
    """
    headers_lines = headers_bytes.getvalue().split(b"\r\n")  # Split headers by \r\n
    headers_list = []
    for header in headers_lines:
        if header.find(b": ") != -1:
            # RFC 7230 specifies header encoding to US-ASCII, which latin1 covers
            headers_list.append(header.decode("latin1"))
    headers_dict = dict(h.split(": ", 1) for h in headers_list)
    return headers_dict


def decode_encoding(content_type: str) -> str:
    """
    Discovers encoding from Content-Type header
    Parameters:
    -   content_type (str): String with Content-Type header

    Returns:
    -   str: String with encoding (empty of none found)
    """
    charset_pos = content_type.find("charset")
    if charset_pos == -1:
        return ""

    encoding_pos = charset_pos + 7  # Length of "charset="
    end_pos = content_type.find(" ", encoding_pos)
    if end_pos == -1:
        return content_type[encoding_pos + 1:]
    else:
        return content_type[encoding_pos + 1:end_pos]


def run(params: dict, run_id: int, queue: Queue = None) -> dict:
    if params is not None:
        try:
            # target is mandatory
            if "target_url" not in params:
                raise ValueError("Missing 'target_url' argument")
            target = params.pop("target_url")

            if "follow_redirects" not in params:
                params["follow_redirects"] = False

            if "ip_version" in params:
                if params["ip_version"] != 4 and params["ip_version"] != 6 and params["ip_version"] != 0:
                    raise ValueError(f"Invalid value of {params['ip_version']} for 'ip_version' parameter")
            else:
                params["ip_version"] = 0

            if "http_version" in params:
                if params["http_version"] != 1.0 and \
                        params["http_version"] != 1.1 and \
                        params["http_version"] != 2.0 and \
                        params["http_version"] != 3.0 and \
                        params["http_version"] != 0:
                    raise ValueError(f"Invalid value of {params['http_version']} for 'http_version' parameter")
                if params["http_version"] == 3.0 and not pycurl_supports_http3():
                    raise ValueError("Parameter 'http_version' has been set to 3.0 but pycurl version doesn't support HTTP/3")
            else:
                params["http_version"] = 0

            # Timeouts are in seconds but libcurl is set to take ms for more flexibility
            if "timeout" in params:
                params["timeout"] = int(params["timeout"] * 1000)
            else:
                params["timeout"] = 60000

            if "connect_timeout" in params:
                params["connect_timeout"] = int(params["connect_timeout"] * 1000)
            else:
                params["connect_timeout"] = 30000

            if "response_values" in params:
                params["response_values"] = {val for val in params["response_values"].split(",")}
            else:
                params["response_values"] = {"all"}

            if "http_method" not in params:
                params["http_method"] = "GET"

            if "headers" not in params:
                params["headers"] = {}

            if "auth_method" in params:
                if params["auth_method"] == "BASIC" and ("username" not in params or "password" not in params):
                    raise ValueError(f"Using BASIC authentication without username or password argument")
                if params["auth_method"] == "DIGEST" and ("username" not in params or "password" not in params):
                    raise ValueError(f"Using DIGEST authentication without username or password argument")
                if params["auth_method"] == "BEARER" and "token" not in params:
                    raise ValueError(f"Using BEARER authentication without token argument")

            if "http_data" not in params:
                params["http_data"] = ""

            if "body_flag" not in params:
                params["body_flag"] = True

            if target.startswith("wss://") or target.startswith("ws://"):
                params["is_ws"] = True

                # Generate random ws key
                params["ws_randomkey"] = bytes(''.join(random.choices(WS_RANDCHARS, k=16)), "ascii")

                # Change URI from ws to http
                if target.startswith("wss://"):
                    target = f"https://{target[6:]}"
                else:
                    target = f"http://{target[5:]}"

                # Add headers for ws upgrade
                b64_key = base64.b64encode(params["ws_randomkey"])
                params["headers"].update({
                    "Upgrade": "websocket",
                    "Connection": "Upgrade",
                    "Sec-WebSocket-Version": "13",
                    "Sec-WebSocket-Key": b64_key.decode("ascii")
                })
            else:
                params["is_ws"] = False

            # Set SSE timeout and header
            if "check_sse" in params:
                if params["check_sse"] is True:
                    params["timeout"] = SSE_TIMEOUT  # Set small timeout when checking for SSE
                    params["headers"].update({
                        "Accept": "text/event-stream",
                    })
            else:
                params["check_sse"] = False

            res = http_query(target, params, run_id)

        except Exception as e:
            res = error_json("HTTP_MONITOR_ERROR", f'Error running HTTP monitor: {e}')

    else:
        res = error_json("INVALID_CONFIGURATION", "Invalid configuration file")

    if queue is not None:
        queue.put(res)

    return res
