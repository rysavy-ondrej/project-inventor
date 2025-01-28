## NAME

`webapp.http`

## VERSION

1.0.0

## INFO

HTTP (Hypertext Transfer Protocol) is an application layer protocol used for transmitting hypermedia documents.
This monitor aims to provide a wide range of useful information from a single HTTP(s) endpoint, such as response code,
headers and transfer times.

### WebSocket support

The monitor will switch to WebSocket mode whenever the input `target` contains a valid WebSocket URI, starting
with `ws://` or `wss://`. The monitor will verify whether the specified endpoint provides a WebSocket connection by
opening a connection and closing it. Successful monitor run is indicated by `valid_ws` being true in output.

### Server-sent Events support

Server-sent events are checked manually by toggling the argument `check_sse`. This will send appropriate headers and
checks if the response contains expected headers. Successful monitor run is indicated by `valid_sse` being true in
output.

When using the SSE monitor the `body` should be considered as unreliable, as it may or may not have received content
from the server.

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

| Parameter        | Type                | Description                                                                                                                                                                                                                                                                                                                                   | Default value            |
|------------------|---------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------|
| target_url       | str                 | URL of HTTP endpoint.                                                                                                                                                                                                                                                                                                                         | mandatory                |
| headers          | Dictionary[str,str] | Dictionary of custom HTTP headers to be send with the request. These will overwrite existing headers and not alter unmentioned headers.                                                                                                                                                                                                       | {} (no headers)          |
| http_version     | float               | Sets a restriction on the version of HTTP that will be used to make the request. If the endpoint doesn't support such version, an error will occur. Possible values are `1.0`, `1.1`, `2.0`, or `0` for any version. The HTTP/3 (option `3.0`) is currently considered too experimental to be included. See [HTTP/3 support](#http3-support). | 0 (any version)          |
| http_method      | str                 | Sets the HTTP method used in the request. Can be `GET`, `POST`, `PUT` or `OPTIONS`.                                                                                                                                                                                                                                                           | GET                      |
| http_data        | str                 | Sets the HTTP data being sent with the request. Using this option will automatically set the `Content-Type` header to `application/x-www-form-urlencoded`. When using any other form of data, the header can be changed with the `headers` option.                                                                                            | null (no data)           |
| body_flag        | boolean             | When true includes the whole body response in the `body` output field.                                                                                                                                                                                                                                                                        | true                     |
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

### Generic HTTP

#### Input

```json
{
  "target_url": "fit.vut.cz",
  "follow_redirects": true
}
```

#### Output

```json
{
  "output": {
    "run_id": 1,
    "status": "completed",
    "target_url": "https://www.fit.vut.cz/",
    "IP_address": "147.229.9.65",
    "port": 443,
    "status_code": 200,
    "status_string": "OK",
    "http_version": 2.0,
    "ttfb": 2.234877,
    "connection_time": 2.25671,
    "redirect_count": 2,
    "redirect_url": null,
    "headers": {
      "Date": "Fri, 22 Nov 2024 13:22:26 GMT",
      "Server": "Apache/2.4.62 (FreeBSD) OpenSSL/1.1.1w-freebsd",
      "Location": "https://fit.vut.cz/",
      "Content-Length": "227",
      "Content-Type": "text/html; charset=iso-8859-1",
      "location": "https://www.fit.vut.cz/",
      "content-length": "231",
      "content-type": "text/html; charset=UTF-8",
      "date": "Fri, 22 Nov 2024 13:22:28 GMT",
      "server": "Apache/2.4.62 (FreeBSD) OpenSSL/1.1.1w-freebsd",
      "vary": "Accept-Language,Accept-Encoding",
      "x-ua-compatible": "IE=edge",
      "cache-control": "private, max-age=0, no-cache",
      "pragma": "no-cache",
      "set-cookie": "logoShown=1; path=/; secure; SameSite=lax",
      "strict-transport-security": "max-age=15768000",
      "x-frame-options": "sameorigin",
      "referrer-policy": "same-origin",
      "x-content-type-options": "nosniff"
    },
    "download_size": 87922.0,
    "download_speed": 38960.0,
    "body": "..."
  }
}
```

### WebSocket

#### INPUT

```json
{
  "target_url": "wss://demo.piesocket.com/v3/channel_123"
}
```

#### OUTPUT

```json
{
  "output": {
    "run_id": 1,
    "status": "completed",
    "target_url": "https://demo.piesocket.com/v3/channel_123",
    "IP_address": "172.105.59.18",
    "port": 443,
    "status_code": 101,
    "status_string": "Switching Protocols",
    "http_version": 1.1,
    "ttfb": 5.394247,
    "connection_time": 5.394343,
    "redirect_count": 0,
    "redirect_url": null,
    "headers": {
      "Server": "nginx/1.25.2",
      "Date": "Fri, 22 Nov 2024 13:24:37 GMT",
      "Connection": "upgrade",
      "Upgrade": "websocket",
      "Sec-WebSocket-Accept": "2kAMAPKFMYzlHctT5EtiX09B8Mw=",
      "X-Powered-By": "Ratchet/0.4.4"
    },
    "download_size": 32.0,
    "download_speed": 5.0,
    "body": "\u0081\u001a{\"error\":\"Missing apiKey\"}\u0088\u0002\u0003\u00e8",
    "ws_key": "Wmh7aT9KVFlaXmJmUyxFZA==",
    "ws_valid": true
  }
}
```

### Server-sent Events

#### INPUT

```json
{
  "target_url": "http://sse.dev/test",
  "check_sse": true
}
```

#### OUTPUT

```json
{
  "output": {
    "run_id": 1,
    "status": "completed",
    "target_url": "http://sse.dev/test",
    "IP_address": "192.248.170.164",
    "port": 80,
    "status_code": 200,
    "status_string": "OK",
    "http_version": 1.1,
    "ttfb": 1.59267,
    "connection_time": 3.00121,
    "redirect_count": 0,
    "redirect_url": null,
    "headers": {
      "Server": "nginx/1.27.2",
      "Date": "Fri, 22 Nov 2024 13:25:09 GMT",
      "Content-Type": "text/event-stream",
      "Transfer-Encoding": "chunked",
      "Connection": "keep-alive",
      "access-control-allow-origin": "*",
      "cache-control": "no-cache"
    },
    "download_size": 83.0,
    "download_speed": 27.0,
    "body": "data: {\"testing\":true,\"sse_dev\":\"is great\",\"msg\":\"It works!\",\"now\":1732281909364}\n\n",
    "sse_valid": true
  }
}
```

### Invalid request

#### INPUT

```json
{
  "target_url": "localhost"
}
```

#### OUTPUT

```json
{
  "output": {
    "status": "error",
    "error": {
      "error_code": "HTTP_MONITOR_ERROR",
      "description": "Error running HTTP monitor: (7, 'Failed to connect to localhost port 80 after 0 ms: Could not connect to server')"
    }
  }
}
```