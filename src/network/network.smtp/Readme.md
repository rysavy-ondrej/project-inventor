## NAME

`network.smtp`

## VERSION

1.0.0

## INFO

SMTP (Simple Mail Transfer Protocol) is a standard communication protocol used for sending and receiving email messages over a network. This test is designed to check if the SMTP service is available on a given `target_host` and attempts to send an email if the service is open. 

FYI: when `send_email_flag` is `True`, you should run test by cmd line `pytest -s`.

However, if this test runs across the Internet, it's recommended to set `send_email_flag` to `False` due to security reasons and not letting sensetive data run in the Internet. `starttls()` ensures that email communication between the client and server, but not what is after the server, if there will be redirect of the email.

## IMPLEMENTATION NOTES
The script connects to the specified `target_host` through the specified `target_port`. The connection timeout is 5 seconds

If the port number is `25` or `587` it will send firstly operation `starttls()` for security purpose. Then it sends 3 operations in the following order: `ehlo`, `noop` and `quit`.


`EHLO` -> Extended Hello, it is process of introducing yourself to the server and requesting extended capabilities. You get a list of features and options supported by the server in response.

`NOOP` -> No Operation, it allows to check if the SMTP service is up and if the server is responding without actually sending an email. It's a lightweight way to verify the service's availability.

`QUIT` -> Operation, that ends session between server and client. It ensures that the connection is closed properly.

It also stores the time when the connection was established and, in the case of a NOOP operation, how long it took for the response server to respond.


#### Used modules

If version is not included - it means it is part of standard Python3 version.

- `smtplib` module (https://docs.python.org/3/library/smtplib.html): Provides SMTP client session object that can be used to send mail to any internet machine with an SMTP or ESMTP listener daemon.
- `email` module (https://docs.python.org/3/library/email.html): is a library for managing email messages.
- `getpass` module (https://docs.python.org/3/library/getpass.html): is a Portable password input. It does not echo the password, when user is prompting.
- `re` module (https://docs.python.org/3/library/re.html): is module that lets using regular expressions.
- `icmplib==3.0.4` module (https://pypi.org/project/icmplib/): used to check if a string is a valid hostname (`is_hostname`).


## Status code's and it's semantic

I added the most common status code, that you will probably get. 

More you can find in - [SMTP return codes](https://en.wikipedia.org/wiki/List_of_SMTP_server_return_codes)

- **2yz Positive completion**
    - 211 System status, or system help reply
    - 214 Help message (A response to the HELP command)
    - 220 `domain` Service ready
    - 221 `domain` Service closing transmission channel
    - 221 2.0.0 Goodbye
    - 235 2.7.0 Authentication succeeded
    - 240 QUIT
    - 250 Requested mail action okay, completed
- **5yz Permanent negative completion**
    - 500 Syntax error, command unrecognized
    - 500 5.5.6 Authentication Exchange line is too long
    - 501 Syntax error in parameters or arguments
    - 502 Command not implemented
    - 503 Bad sequence of commands
    - 504 Command parameter is not implemented
    - 504 5.5.4 Unrecognized authentication type
    - 521 Server does not accept mail
    - 523 Encryption Needed
    - 530 5.7.0 Authentication required
    - 534 5.7.9 Authentication mechanism is too weak
    - 535 5.7.8 Authentication credentials invalid
    - 538 5.7.11 Encryption required for requested authentication mechanism
    - 554 5.3.4 Message too big for system
    - 556 Domain does not accept mail


## INPUT

| Parameter       | Type    | Description                                   |
|-----------------|---------|-----------------------------------------------|
| target_host     | string  | The hostname or IPv4/6 address|
| target_port     | string | The port number  |
| send_email_flag     | string | `True` - send email /// `False` - do not send email      |

## OUTPUT

| Field            | Type    | Description                                |
|------------------|---------|--------------------------------------------|
| target_host     | string  | The hostname or IPv4/6 address|
| target_port     | string | The port number  |
| IP_address           | string | Show `target_host`'s IP address |
| sendmail_op           | string |  Contains the result of attemting sending email if it set `True`
| connected_time           | string |  Time when the script connected to a specific port  |
| server_msg           | string |  Time when the script connected to a specific port  |
| ehlo_op           | dictionary |  Collects the result of sending EHLO operation to server |
| noop_op           | dictionary |  Collects the result of sending NOOP operation to server |
| quit_op           | dictionary |  Collects the result of sending QUIT operation to server |
| name_op -> status_code           | string |  Status code got from server by sending NOOP/QUIT/EHLO operations |
| name_op -> status_msg           | string |  Contains messeage result from NOOP/QUIT/EHLO operations |
| ehlo_op -> SIZE           | string |  Maximum size of message, that server can handle in MB |
| response_time           | string |  Time taken to send and receive the result from the NOOP operation |
| duration           | string |  Total time taken to check port health |





## EXAMPLE
#### Input Example (JSON format):
```json
{
    "target_host": "kazi.fit.vutbr.cz",
    "target_port": "25",
    "send_email_flag": "False"
}

```
#### Output Example (JSON Format)
```json
{
    "output": {
        "target_host": "kazi.fit.vutbr.cz",
        "target_port": "25",
        "IP_address": "147.229.8.12",
        "connected_time": "2024-11-22T11:58:56.596428Z",
        "server_msg": "250-kazi.fit.vutbr.cz Hello static-84-42-180-82.bb.vodafone.cz [84.42.180.82], pleased to meet you",
        "ehlo_op": {
            "status_code": "250",
            "status_msg": "['ENHANCEDSTATUSCODES', 'PIPELINING', 'EXPN', 'VERB', '8BITMIME', 'SIZE 33554432', 'DSN', 'ETRN', 'AUTH PLAIN LOGIN', 'DELIVERBY', 'HELP']",
            "SIZE": "32.0 MB"
        },
        "noop_op": {
            "status_code": "250",
            "status_msg": "b'2.0.0 OK'"
        },
        "response_time": "0.019s",
        "quit_op": {
            "status_code": "221",
            "status_msg": "b'2.0.0 kazi.fit.vutbr.cz closing connection'"
        },
        "duration": "0.246s"
    },
    "queue": {
        "target_host": "kazi.fit.vutbr.cz",
        "target_port": "25",
        "IP_address": "147.229.8.12",
        "connected_time": "2024-11-22T11:58:56.596428Z",
        "server_msg": "250-kazi.fit.vutbr.cz Hello static-84-42-180-82.bb.vodafone.cz [84.42.180.82], pleased to meet you",
        "ehlo_op": {
            "status_code": "250",
            "status_msg": "['ENHANCEDSTATUSCODES', 'PIPELINING', 'EXPN', 'VERB', '8BITMIME', 'SIZE 33554432', 'DSN', 'ETRN', 'AUTH PLAIN LOGIN', 'DELIVERBY', 'HELP']",
            "SIZE": "32.0 MB"
        },
        "noop_op": {
            "status_code": "250",
            "status_msg": "b'2.0.0 OK'"
        },
        "response_time": "0.019s",
        "quit_op": {
            "status_code": "221",
            "status_msg": "b'2.0.0 kazi.fit.vutbr.cz closing connection'"
        },
        "duration": "0.246s"
    }
}
```

## EXAMPLE (Failed operation)
#### Input Example (JSON format):
```json
{
    "target_host": "kazi.fit.vutbr.cz123",
    "target_port": "25",
    "send_email_flag": "False"
}

```
#### Output Example (JSON Format)
```json
{
    "output": {
        "target_host": "kazi.fit.vutbr.cz123",
        "target_port": "25",
        "retcode": "ERROR: on port 25 can't connect.",
        "errcode": "[Errno -2] Name or service not known"
    },
    "queue": {
        "target_host": "kazi.fit.vutbr.cz123",
        "target_port": "25",
        "retcode": "ERROR: on port 25 can't connect.",
        "errcode": "[Errno -2] Name or service not known"
    }
}
```