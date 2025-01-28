## NAME

`network.ftp`

## VERSION

1.0.0

## INFO

FTP (File Transfer Protocol) - is an application layer protocol responsible for transferring data between two systems. An FTP connection is created between a client and a server, after which they communicate with each other using the network. To do this, the user can obtain permission by providing credentials to the FTP server or use anonymous FTP.

This script uses an anonymous login method and also tries to connect FTP server over TLS/SSL for security reasons. (FTP server also needs to support TLS/SSL, otherwise it return error code and the connection is shutdown)

## IMPLEMENTATION NOTES
Script tries connect to the server in the defined `target_host`. After that, anonymous logging is performed, then the `data connection` is secured using `prot_p()` functions from the same `ftplib` library. Then the script issues `retrlines("LIST")` operation, which is in Linux operation same command `ls -l`. It also calculates time taken to respond from the server. And in the end it sends `quit` operation to ensure correct disconnect from the service.



#### Used modules

- `ftplib==(no info)` module (https://docs.python.org/3/library/ftplib.html): Provides client side of the FTP protocol. Version 
- `icmplib==3.0.4` module (https://pypi.org/project/icmplib/): used to check if target host is hostname by function `is_hostname()`.


## Status code's and it's semantic
List of all FTP service return codes you can see in [RFC959](https://datatracker.ietf.org/doc/html/rfc959).

This is list of common return codes, that you will see: 
- `120 ` →    Service ready in nnn minutes
- `125 ` →   Data connection already open; transfer starting
- `150 ` →    File status okay; about to open data connection
- `230` →  User logged in, proceed
- `200` →  Command okay
- `226` → Closing data connection / Requested file action successful
- `221` →  Service closing control connection
- `332` →  Need account for login
- `421` →  Service not available, closing control connection
- `425 ` →  Can't open data connection
- `426 ` →   Connection closed; transfer aborted
- `500 ` →   Syntax error or command unrecognized. 
- `501 ` →   Syntax error in parameters or arguments
- `502 ` →   Command not implemented
- `530 ` →   Not logged in




## INPUT

| Parameter       | Type    | Description                                   |
|-----------------|---------|-----------------------------------------------|
| target_host     | string  | The hostname or IP address|

## OUTPUT

| Field            | Type    | Description                                |
|------------------|---------|--------------------------------------------|
| target_host           | string | Target host IPv4/IPv6 address or hostname |
|   connected_time           | string |  Time when the script connected to a specific port  |
|   login_op           | string |  Anonymously login to the FTP server |
|   welcome_op           | string |  FTP server **WELCOME** string, that **indicates succesfully connection** |
|   protect_op           | string |  Turn security on data connection to `private` |
|   retrlines_op           | string |  Operation to check FTP server functionality |
|   quit_op           | string |  Disconnect from FTP server |
|   response_time           | string |  Time taken to send and receive the result from the NOOP operation |
|   duration           | string |  Total time taken to check port health |


In case of error connection. You will see also:
| Field            | Type    | Description                                |
|------------------|---------|--------------------------------------------|
|   retcode           | string |  Error messeage code |
|   errmsg           | string |  Error messeage detail |


## EXAMPLE
#### Input Example (JSON format):

```json
{
    "target_host": "ftp1.at.proftpd.org"
}
```
#### Output Example (JSON Format)
```json
{
    "output": {
        "target_host": "ftp.gnu.org",
        "IP_address": "2001:470:142:3::b",
        "connected_time": "2024-11-22T11:26:14.220344Z",
        "welcome_op": "220 GNU FTP server ready.",
        "login_op": "Failed: 530 Please login with USER and PASS.",
        "response_time": "0.118s",
        "quit_op": "221 Goodbye.",
        "duration": "0.536s"
    },
    "queue": {
        "target_host": "ftp.gnu.org",
        "IP_address": "2001:470:142:3::b",
        "connected_time": "2024-11-22T11:26:14.220344Z",
        "welcome_op": "220 GNU FTP server ready.",
        "login_op": "Failed: 530 Please login with USER and PASS.",
        "response_time": "0.118s",
        "quit_op": "221 Goodbye.",
        "duration": "0.536s"
    }
}
```

## EXAMPLE (Failed operation)
#### Input Example (JSON format):

```json
{
    "target_host": "192.168.1.11"
}
```
#### Output Example (JSON Format)
```json
{
    "output": {
        "target_host": "192.168.1.11",
        "retcode": "ERROR:",
        "errcode": "timed out"
    },
    "queue": {
        "target_host": "192.168.1.11",
        "retcode": "ERROR:",
        "errcode": "timed out"
    }
}
```
