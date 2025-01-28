## NAME

`security.ssh`

## VERSION

1.0.0

## INFO

SSH (Secure SHell) - is an application layer network protocol designed for secure remote access to `UNIX` systems. This protocol is effective in that it encrypts all information transmitted over the network. By default, `port 22` is used. It is mainly used for remote management of user data on the server, running service commands, working in console mode with databases.


## IMPLEMENTATION NOTES
The script connects to the specified `target_host` through the specified `target_port`. The connection timeout is 5 seconds

Using `socket` library, script creates connection to `target_host` and receives data from the connected socket. Here is usefull data is `SSH Version/Banner` which represents, that service is working and users can connect to it. After that, script closes connection by `socket.close()`.

#### Used modules

- `socket` module (https://docs.python.org/3/library/socket.html): A Python implementation of SSHv2.
- `icmplib==3.0.4` module (https://pypi.org/project/icmplib/): used to ping servers before testing service.

## INPUT

| Parameter       | Type    | Description                                   |
|-----------------|---------|-----------------------------------------------|
| target_host     | string  | The hostname or IPv4/6 address|

## OUTPUT

| Field            | Type    | Description                                |
|------------------|---------|--------------------------------------------|
| IP_address           | string | Show `target_host`'s IP address |
| connected_time           | string |  Time connected to the service  |
| response_time           | string |  Time taken to get response from server  |
| ssh_banner           | string |  SSH Version, which indicates postive connection  |
| duration           | string |  Total time taken for procedure  |





## EXAMPLE
#### Input Example (JSON format):
```json
{
    "target_host": "eva.fit.vutbr.cz"
}
```
#### Output Example (JSON Format)
```json
{
    "output": {
        "target_host": "eva.fit.vutbr.cz",
        "IP_address": "147.229.176.14",
        "connected_time": "2024-06-29T16:45:19.157495Z",
        "ssh_banner": "SSH-2.0-OpenSSH_9.7\r\n",
        "response_duration": "0.064s",
        "connection_duration": "0.111s"
    },
    "queue": {
        "target_host": "eva.fit.vutbr.cz",
        "IP_address": "147.229.176.14",
        "connected_time": "2024-06-29T16:45:19.157495Z",
        "ssh_banner": "SSH-2.0-OpenSSH_9.7\r\n",
        "response_duration": "0.064s",
        "connection_duration": "0.111s"
    }
}
```


## EXAMPLE (Unsuccessful  operation)
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
        "status": "error",
        "error": {
            "error_code": "CONFIG FILE ERROR",
            "description": "local variable 'sock' referenced before assignment"
        }
    },
    "queue": {
        "status": "error",
        "error": {
            "error_code": "CONFIG FILE ERROR",
            "description": "local variable 'sock' referenced before assignment"
        }
    }
}
```