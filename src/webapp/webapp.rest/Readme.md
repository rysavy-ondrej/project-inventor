## NAME

`webapp.rest`

## VERSION

1.0.0

## INFO

REST is an architectural style of stateless web-based application API.
It defines a set endpoints which are utilized to access a given resource through HTTP methods (called verbs in REST
context).

### Matching system

For monitoring of whether the endpoint provides expected data, the monitor implements a system for matching against a
provided set or subset of data.
For example, the REST endpoint could return following XML document:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<root>
    <city>San Jose</city>
    <firstName>John</firstName>
    <lastName>Doe</lastName>
    <state>CA</state>
</root>
```

In such a case the user could provide same or similar set of data into `match_data` input, and the monitor will try to
match against it.
There's two matching scopes which change the way that the monitor uses the provided data: `full` and `partial`.

With `full` scope, the provided data tries to be matched fully, so that all JSON/XML elements have to be exactly the
same.
In the previous case, the user would have to provide the whole XML document for the match to pass successfully.

When using `partial` scope, the user needs to provide only a subset of data, which are then matched against the total
set of data.
For example with the previous case, the user could only provide data in form
of `<root><firstName>John</firstName></root>`, and the matching system would pass successfully, because the returned
document contains all these elements.

### HTTP/3 support

The libcurl library currently considers the support for HTTP/3 experimental. To utilize this feature, the curl tool has
to be built with support for this protocol in mind. While some distributions provide pre-build packages with support
already built-in (e.g. Debian), some do not (e.g. RHEL).

In case you would like to manually build curl with HTTP/3 support, you can follow the ngtcp2 section
in [this](https://curl.se/docs/http3.html) guide. The process requires to install various 3rd party libraries that
provide support for QUIC.

The monitor is able to detect if the current libcurl version is capable of using HTTP/3 and will provide appropriate
feedback in case the user tries to use it without support.

## Requirements

| Library | Usage                                                                         |
|---------|-------------------------------------------------------------------------------|
| pycurl  | Compatibility layer for accessing libcurl API used to request HTTP endpoints. |
| certifi | Used to verify trustworthiness of endpoint certificates.                      |

## INPUT

This monitor utilized the implementation of [webapp.http](../webapp.http) for making HTTP calls, the inputs are
therefore fully compatible.
The following tables showcase both types of available parameters in this monitor:

### REST parameters

| Parameter   | Type | Description                                                                                                                                                        | Default value |
|-------------|------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|
| match_type  | str  | Selects what kind of serialization method the endpoint responds with. Can be one of: `json`, `xml`.                                                                | `json`        |
| match_scope | str  | Selects how to match the provided matching data in `match_data`. Can be one of: `full`, `partial`. For more info on these, see [Matching system](#Matching-system) | `full`        |
| match_data  | str  | Provides the data to match against. This argument is mandatory if `match_type` or `match_scope` are provided.                                                      | null          |

### HTTP parameters

| Parameter        | Type                | Description                                                                                                                                                                                                                                                                                                                                   | Default value            |
|------------------|---------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------|
| target_url       | str                 | URL of HTTP endpoint.                                                                                                                                                                                                                                                                                                                         | mandatory                |
| headers          | Dictionary[str,str] | Dictionary of custom HTTP headers to be send with the request. These will overwrite existing headers and not alter unmentioned headers.                                                                                                                                                                                                       | {} (no headers)          |
| http_version     | float               | Sets a restriction on the version of HTTP that will be used to make the request. If the endpoint doesn't support such version, an error will occur. Possible values are `1.0`, `1.1`, `2.0`, or `0` for any version. The HTTP/3 (option `3.0`) is currently considered too experimental to be included. See [HTTP/3 support](#http3-support). | 0 (any version)          |
| http_method      | str                 | Sets the HTTP method used in the request. Can be `GET`, `POST`, `PUT` or `OPTIONS`.                                                                                                                                                                                                                                                           | GET                      |
| http_data        | str                 | Sets the HTTP data being sent with the request. Using this option will automatically set the `Content-Type` header to `application/x-www-form-urlencoded`. When using any other form of data, the header can be changed with the `headers` option.                                                                                            | null (no data)           |
| follow_redirects | boolean             | If true, the monitor will query additional redirect URLs if the response contains them. Each call to separate endpoint due to redirections has its own timeout measurements.                                                                                                                                                                  | false                    |
| ip_version       | int                 | Chooses between IPv4, IPv6 or either for communication with endpoint.                                                                                                                                                                                                                                                                         | 0 (either)               |
| response_values  | str                 | Comma separated list of values in output that will be outputted. Value `all` has a special meaning where it ignores all other list values and outputs everything.                                                                                                                                                                             | "all" (every value)      |
| timeout          | float               | Number of seconds before the connection is dropped in case of no response. This timeout includes all transfer operation (name lookup, TLS, TCP, data transfer, etc.).                                                                                                                                                                         | 60.0                     |
| connect_timeout  | float               | Number of seconds before the connection is dropped in case of no response. This timeout measures the time to establish a connection with the endpoint and is disregarded once the connection is made.                                                                                                                                         | 30.0                     |
| auth_method      | str                 | Selects the desired authentication method. Can be `BASIC`, `DIGEST` or `BEARER`. When using `BASIC` or `DIGEST`, the `username` and `password` arguments must be included. When using `DIGEST` method, the `token` argument must be included.                                                                                                 | null (no authentication) |
| username         | str                 | String with username used in authentication. Used with `BASIC` or `DIGEST` authentication method.                                                                                                                                                                                                                                             | null                     |
| password         | str                 | String with password used in authentication. Used with `BASIC` or `DIGEST` authentication method.                                                                                                                                                                                                                                             | null                     |
| token            | str                 | String with token used in authentication. Used with `BEARER` authentication method.                                                                                                                                                                                                                                                           | null                     |
| check_sse        | boolean             | Will check whether the endpoint offers Server-sent Events (SSE). To check for SSE the monitor sends `Accept: text/event-stream` HTTP header and checks for `Content-Type: text/event-stream` in response. This option will set `response_timeout` to 3 seconds so that libcurl has time to get HTTP headers.                                  | false                    |

## OUTPUT

| Name         | Type | Description                                                                                   |
|--------------|------|-----------------------------------------------------------------------------------------------|
| match        | bool | Set to true if the matching arguments are used and the provided data is matched successfully. |
| http_outputs | dict | Outputs from [webapp.http](../webapp.http).                                                   |

### HTTP OUTPUT

| Name            | Type                | Description                                                                                                                                                      |
|-----------------|---------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| target_url      | str                 | Actual URL used in the request.                                                                                                                                  |
| IP_address      | str                 | Destination IP of endpoint.                                                                                                                                      |
| port            | int                 | Destination port of endpoint.                                                                                                                                    |
| status_code     | int                 | HTTP response code.                                                                                                                                              |
| status_string   | str                 | Short string describing the response code.                                                                                                                       |
| http_version    | int                 | HTTP version used in the response.                                                                                                                               |
| ttfb            | int                 | Time in seconds from the start until first byte of HTTP data is received.                                                                                        |
| connection_time | int                 | Time in seconds of the total transfer duration, including TCP/IP stack communication.                                                                            |
| redirect_count  | str                 | Number of redirects followed. Makes sense only with `follow_redirects` enabled.                                                                                  |
| redirect_url    | str                 | Contains URL of the redirect endpoint, but is empty if the response doesn't contain one.                                                                         |
| headers         | Dictionary[str,str] | Dictionary of HTTP headers used in the response.                                                                                                                 |
| bytes_received  | int                 | Number of bytes downloaded with the response.                                                                                                                    |
| download_speed  | int                 | Download speed in bytes per second.                                                                                                                              |
| body            | str                 | Decoded body of HTTP response. Included if `body_flag` is True.                                                                                                  |
| ws_key          | str                 | Base64 encoded `Sec-WebSocket-Key` used in WebSocket request. Only returned when using WebSocket.                                                                |
| ws_valid        | boolean             | True if the header `Sec-WebSocket-Accept` is present and contains valid value. See RFC 6455 Section 1.3 for details. Only returned when using WebSocket.         |
| sse_valid       | boolean             | True if the argument `check_see` is True and the header `Content-Type` is present and contains `text/event-stream`. Only returned when using Server-sent Events. |

## EXAMPLES

### JSON with POST

#### Input

```json
{
  "target_url": "https://httpbin.org/post",
  "http_method": "POST",
  "follow_redirects": true,
  "match_data": "{\"headers\": {\"Accept\": \"*/*\", \"Host\": \"https://httpbin.org\"}}",
  "match_scope": "partial"
}
```

#### Output

```json
{
  "output": {
    "run_id": 1,
    "status": "completed",
    "match": true,
    "http_outputs": {
      "run_id": 1,
      "status": "completed",
      "target_url": "https://httpbin.org/post",
      "IP_address": "52.20.148.183",
      "port": 443,
      "status_code": 200,
      "status_string": "OK",
      "http_version": 2.0,
      "ttfb": 1.9285,
      "connection_time": 1.928623,
      "redirect_count": 0,
      "redirect_url": null,
      "headers": {
        "date": "Fri, 22 Nov 2024 13:17:34 GMT",
        "content-type": "application/json",
        "content-length": "455",
        "server": "gunicorn/19.9.0",
        "access-control-allow-origin": "*",
        "access-control-allow-credentials": "true"
      },
      "download_size": 455.0,
      "download_speed": 235.0,
      "body": "{\n  \"args\": {}, \n  \"data\": \"\", \n  \"files\": {}, \n  \"form\": {}, \n  \"headers\": {\n    \"Accept\": \"*/*\", \n    \"Host\": \"httpbin.org\", \n    \"User-Agent\": \"PycURL/7.45.3 libcurl/8.11.0 OpenSSL/3.4.0 zlib/1.3.1 brotli/1.1.0 zstd/1.5.6 libidn2/2.3.7 libpsl/0.21.5 libssh2/1.11.0 nghttp2/1.64.0 nghttp3/1.6.0\", \n    \"X-Amzn-Trace-Id\": \"Root=1-6740846e-477cf7fe2f5a3f8726c1f2b0\"\n  }, \n  \"json\": null, \n  \"origin\": \"85.193.0.12\", \n  \"url\": \"https://httpbin.org/post\"\n}\n"
    }
  }
}
  ```

### XML with GET

#### INPUT

```json
{
  "target_url": "https://mocktarget.apigee.net/xml",
  "http_method": "GET",
  "follow_redirects": true,
  "match_type": "XML",
  "match_data": "<root><city>San Jose</city></root>",
  "match_scope": "partial"
}
```

#### OUTPUT

```json
{
  "output": {
    "run_id": 1,
    "status": "completed",
    "match": true,
    "http_outputs": {
      "run_id": 1,
      "status": "completed",
      "target_url": "https://mocktarget.apigee.net/xml",
      "IP_address": "35.227.194.212",
      "port": 443,
      "status_code": 200,
      "status_string": "OK",
      "http_version": 2.0,
      "ttfb": 0.175937,
      "connection_time": 0.177186,
      "redirect_count": 0,
      "redirect_url": null,
      "headers": {
        "x-powered-by": "Apigee",
        "access-control-allow-origin": "*",
        "x-frame-options": "ALLOW-FROM RESOURCE-URL",
        "x-xss-protection": "1",
        "x-content-type-options": "nosniff",
        "content-type": "application/xml; charset=utf-8",
        "content-length": "141",
        "etag": "W/\"8d-oqSmr/xiG8D5GJ3RBUhqY00xvcA\"",
        "date": "Fri, 22 Nov 2024 13:20:26 GMT",
        "via": "1.1 google",
        "alt-svc": "h3=\":443\"; ma=2592000,h3-29=\":443\"; ma=2592000"
      },
      "download_size": 141.0,
      "download_speed": 795.0,
      "body": "<?xml version=\"1.0\" encoding=\"UTF-8\"?> <root><city>San Jose</city><firstName>John</firstName><lastName>Doe</lastName><state>CA</state></root>"
    }
  }
}
```