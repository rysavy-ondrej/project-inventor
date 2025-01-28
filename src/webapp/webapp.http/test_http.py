#
# Created as a part of the INVENTOR project (TAČR Trend No. FW10010040, 2024-2026).
# Author: Pavel Horáček, <xhorac19@fit.vutbr.cz>
# Institution: Brno University of Technology, Faculty of Information Technology, Czech Republic
# Date: 22/11/2024
#

import logging
import json
import pytest
import webapp_http as http
import pycurl
from multiprocessing import Queue
from io import BytesIO


def pytest_configure(config):
    logging.basicConfig(level=logging.INFO)


def test_method_decode_encoding():
    assert http.decode_encoding("text/html; charset=utf-8") == "utf-8"


def test_method_decode_headers():
    headers = http.decode_headers(BytesIO(bytes("header1: body1\r\nheader2: body2\r\n", "utf-8")))
    assert headers == {"header1": "body1", "header2": "body2"}


def test_method_httpver_conversion():
    ver1 = http.curl_httpver_code_2_float(pycurl.CURL_HTTP_VERSION_1_0)
    assert ver1 == 1.0

    ver11 = http.curl_httpver_code_2_float(pycurl.CURL_HTTP_VERSION_1_1)
    assert ver11 == 1.1

    ver2 = http.curl_httpver_code_2_float(pycurl.CURL_HTTP_VERSION_2_0)
    assert ver2 == 2.0

    if http.pycurl_supports_http3():
        ver3 = http.curl_httpver_code_2_float(pycurl.CURL_HTTP_VERSION_3)
        assert ver3 == 3.0

    ver0 = http.curl_httpver_code_2_float(0)
    assert ver0 == 0.0


def test_method_error_json():
    assert http.error_json("TEST", "Test message") == \
           {"status": "error",
            "error": {"error_code": "TEST", "description": "Test message"}}


def test_redirect_true():
    with open('test/inputRedirectTrue.json', 'r') as file:
        config = json.load(file)
    output = http.run(config, 1, None)
    assert "status_code" in output and not (300 <= output["status_code"] < 400)


def test_redirect_false():
    with open('test/inputRedirectFalse.json', 'r') as file:
        config = json.load(file)
    output = http.run(config, 1, None)
    assert "status_code" in output and 300 <= output["status_code"] < 400


@pytest.mark.skipif(not http.pycurl_supports_http3(), reason="Used pycurl doesn't support HTTP/3")
def test_http3():
    with open('test/inputHTTP3.json', 'r') as file:
        config = json.load(file)
    output = http.run(config, 1, None)
    assert "http_version" in output and output["http_version"] == 3.0


def test_http2():
    with open('test/inputHTTP2.json', 'r') as file:
        config = json.load(file)
    output = http.run(config, 1, None)
    assert "http_version" in output and output["http_version"] == 2.0


def test_http11():
    with open('test/inputHTTP11.json', 'r') as file:
        config = json.load(file)
    output = http.run(config, 1, None)
    assert "http_version" in output and output["http_version"] == 1.1


def test_http1():
    with open('test/inputHTTP1.json', 'r') as file:
        config = json.load(file)
    output = http.run(config, 1, None)
    assert "http_version" in output and output["http_version"] == 1.0


def test_invalid_request():
    with open('test/inputError.json', 'r') as file:
        config = json.load(file)
    output = http.run(config, 1, None)
    assert "error" in output and "error_code" in output["error"] and output["error"]["error_code"] == "HTTP_MONITOR_ERROR"


def test_valid_request():
    with open('test/inputValid.json', 'r') as file:
        config = json.load(file)
    output = http.run(config, 1, None)
    assert "status_code" in output and output["status_code"] == 200


def test_sse():
    with open('test/inputSSE.json', 'r') as file:
        config = json.load(file)
    output = http.run(config, 1, None)
    assert output["sse_valid"]


def test_ws():
    with open('test/inputWS.json', 'r') as file:
        config = json.load(file)
    output = http.run(config, 1, None)
    assert output["ws_valid"]


def test_service():
    with open('test/input.json', 'r') as file:
        config = json.load(file)

    queue = Queue()
    output = http.run(config, 1, queue)
    result = queue.get()

    # Combine the output and queue results:
    combined = {
        "output": output,
        "queue": result
    }

    with open('test/output.json', 'w') as file:
        json.dump(combined, file, indent=4)
