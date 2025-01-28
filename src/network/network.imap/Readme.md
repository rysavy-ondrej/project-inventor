## NAME

`network.imap`

## VERSION

1.0.0

## INFO
Internet Message Access Protocol, or IMAP, is an Internet standard protocol used by email clients to retrieve email messages from a mail server over a TCP/IP connection.

This test is designed to check the IMAP service on a given server by sending some operations to IMAP server, if the port state is open.
 

## IMPLEMENTATION NOTES
The script connects to the specified `target_host` through the specified `target_port`. The connection timeout is 5 seconds

If the port number is **not** `993`, it will send firstly operation `starttls()` for security purpose. Then it sends 2 operations in the following order: `noop()` and `capability()`.

`NOOP` -> No Operation, it allows to check if the SMTP service is up and if the server is responding without actually sending an email. It's a lightweight way to verify the service's availability.

`CAPABILITY` -> Operation, that requests for listing the capabilities that the server supports.

It also stores the time when the connection was established and, in the case of a `NOOP` operation, how long it took for the response server to respond.



#### Used modules

- `imaplib==2.58` module (https://docs.python.org/3/library/imaplib.html): IMAP4 protocol client.
- `icmplib==3.0.4` module (https://pypi.org/project/icmplib/): used to check if a string is a valid hostname (`is_hostname`).



## INPUT

| Parameter       | Type    | Description                                   |
|-----------------|---------|-----------------------------------------------|
| target_host     |strings  | The hostname or IPv4/6 address|
| target_port     | string | The port number  |
| login_flag     | string | If it set "True", then it tries to login to the server     |
| login_username     | string | Login credentials for the server     |
| login_server     | string | On which server it will login     |

## OUTPUT
| Field            | Type    | Description                                |
|------------------|---------|--------------------------------------------|
| IP_address           | string | Show `target_host`'s IP address |
|  connected_time           | string |  Time when the script connected to a specific port  |
|  protocol_version           | string |  Which version of IMAP4 server use.  |
|  noop_op           | dictionary |  Collects the result of sending NOOP operation to server |
| name_op -> status_code           | string |  Status code got from server by sending NOOP operation |
| name_op -> status_msg           | string |  Contains messeage result from server of NOOP operations |
|  response_time           | string |  Time taken to send and receive the result from the NOOP operation |
| server_msg           | string |  Contains messeage result from server of CAPABILITY operations |
|  duration           | string |  Total time taken to check port health |




## EXAMPLE
#### Input Example (JSON format):

```json
{
    "target_host": "kazi.fit.vutbr.cz",
    "target_port": "993",
    "login_flag": "False",
    "login_username": "xassat00@vutbr.cz",
    "login_server": "eva.fit.vutbr.cz"
}
```

#### Output Example (JSON format):
```json
{
    "output": {
        "target_host": "kazi.fit.vutbr.cz",
        "target_port": "993",
        "IP_address": "2001:67c:1220:808::93e5:80c",
        "protocol_version": "IMAP4REV1",
        "connected_time": "2024-11-22T11:27:38.236504Z",
        "noop_op": {
            "status_code": "OK",
            "status_msg": "[b'NOOP completed.']"
        },
        "response_time": "0.019s",
        "server_msg": "('OK', [b'IMAP4rev1 SASL-IR LOGIN-REFERRALS ID ENABLE IDLE LITERAL+ AUTH=PLAIN AUTH=LOGIN'])",
        "duration": "1.471s"
    },
    "queue": {
        "target_host": "kazi.fit.vutbr.cz",
        "target_port": "993",
        "IP_address": "2001:67c:1220:808::93e5:80c",
        "protocol_version": "IMAP4REV1",
        "connected_time": "2024-11-22T11:27:38.236504Z",
        "noop_op": {
            "status_code": "OK",
            "status_msg": "[b'NOOP completed.']"
        },
        "response_time": "0.019s",
        "server_msg": "('OK', [b'IMAP4rev1 SASL-IR LOGIN-REFERRALS ID ENABLE IDLE LITERAL+ AUTH=PLAIN AUTH=LOGIN'])",
        "duration": "1.471s"
    }
}
```

## Example (Failed operation)
#### Input Example (JSON Format)
```json
{
    "target_host": "kazi.fit.vutbr.cz123",
    "target_port": "993",
    "login_flag": "False",
    "login_username": "xstudent00@vutbr.cz",
    "login_server": "kazi.fit.vutbr.cz"
}
```
#### Output Example (JSON Format)
```json
{
    "output": {
        "target_host": "kazi.fit.vutbr.cz123",
        "target_port": "993",
        "retcode": "ERROR: can't connect to target.",
        "errcode": "[Errno -2] Name or service not known"
    },
    "queue": {
        "target_host": "kazi.fit.vutbr.cz123",
        "target_port": "993",
        "retcode": "ERROR: can't connect to target.",
        "errcode": "[Errno -2] Name or service not known"
    }
}
```