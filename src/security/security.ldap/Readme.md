## NAME

`security.ldap`

## VERSION

1.0.0

## INFO

LDAP (Lightweight Directory Access Protocol) - is a lightweight protocol for accessing data organised in a hierarchical structure (directory). It allows you to manage and search information about users, devices, and other resources on your network. It is most often used for authentication and account management in corporate networks.


## IMPLEMENTATION NOTES
This script uses `ldap3` library to establish connection to the target host. As an input parametr used only `target_host`. 

It creates server object for LDAP connection, then performs `bind` command to the `target_host`.
If connection is established successfuly - it sends simple `search` query to check if LDAP service working properly.
The result of `search` query can be empty list `[]` or contain some entities. The empty list `[]` does not mean, that something is wrong. The case is to check LDAP service and get response, which `[]` is.


#### Used modules

- `socket` module (https://docs.python.org/3/library/socket.html): provides access to the BSD socket interface.
- `ldap3==2.9.1` module (https://ldap3.readthedocs.io/en/latest/): used to check ldap service.
- `icmplib==3.0.4` module (https://pypi.org/project/icmplib/): used to check hostname address.

## INPUT

| Parameter       | Type    | Description                                   |
|-----------------|---------|-----------------------------------------------|
| target_host     | string  | The hostname or IPv4/6 address|
## OUTPUT

| Field            | Type    | Description                                |
|------------------|---------|--------------------------------------------|
|target_host | string | Target hostname or IPv4/6 address |
|IP_address | string | IPv4/6 address if it is hostname |
|connected_time | string | Established connection time |
|duration | string | Total time taken to operation. |
|response_time | string | Server response time in milliseconds |
|search_query | string | Simple query to check LDAP service. It can be empty list or contain some entries. |




## EXAMPLE
#### Successful operation [without entries]
#### Input Example (JSON format):
```json
{
    "target_host": "db.debian.org"
}
```
#### Output Example (JSON Format)
```json
{
    "output": {
        "target_host": "db.debian.org",
        "IP_address": "2001:41b8:202:deb:1a1a:0:52c3:4b6a",
        "connected_time": "2024-10-24T12:22:46.826487Z",
        "resposne_time_ms": 0.19,
        "search_query": []
    },
    "queue": {
        "target_host": "db.debian.org",
        "IP_address": "2001:41b8:202:deb:1a1a:0:52c3:4b6a",
        "connected_time": "2024-10-24T12:22:46.826487Z",
        "resposne_time_ms": 0.19,
        "search_query": []
    }
}
```

#### Successful operation [with entries]
#### Input Example (JSON format):
```json
{
    "target_host": "ldap.fit.vutbr.cz"
}
```
#### Output Example (JSON Format)
```json
{
    "output": {
        "target_host": "ldap.fit.vutbr.cz",
        "IP_address": "147.229.9.22",
        "connected_time": "2024-10-24T12:21:43.066462Z",
        "resposne_time_ms": 0.01,
        "search_query": [
            "DN: dc=vutbr,dc=cz - STATUS: Read - READ TIME: 2024-10-24T14:21:43.072584\n    dc: vutbr\n    o: VUT v Brne\n       VUT\n    objectClass: organization\n                 dcObject\n                 top\n",
            <omitted>
        ]
    },
    "queue": {
        "target_host": "ldap.fit.vutbr.cz",
        "IP_address": "147.229.9.22",
        "connected_time": "2024-10-24T12:21:43.066462Z",
        "resposne_time_ms": 0.01,
        "search_query": [
            "DN: dc=vutbr,dc=cz - STATUS: Read - READ TIME: 2024-10-24T14:21:43.072584\n    dc: vutbr\n    o: VUT v Brne\n       VUT\n    objectClass: organization\n                 dcObject\n                 top\n",
            <omitted>
        ]
    }
}
```

#### Unsuccessful operation
#### Input Example (JSON format):
```json
{
    "target_host": "kazi.fit.vutbr.cz"
}
```
#### Output Example (JSON Format)
```json
{
    "output": {
        "status": "error",
        "error": {
            "error_code": "ERROR: something went wrong during testing",
            "description": "('unable to open socket', [(LDAPSocketOpenError('socket connection error while opening: [Errno 111] Connection refused'), ('2001:67c:1220:808::93e5:80c', 389, 0, 0)), (LDAPSocketOpenError('socket connection error while opening: [Errno 111] Connection refused'), ('147.229.8.12', 389))])"
        }
    },
    "queue": {
        "status": "error",
        "error": {
            "error_code": "ERROR: something went wrong during testing",
            "description": "('unable to open socket', [(LDAPSocketOpenError('socket connection error while opening: [Errno 111] Connection refused'), ('2001:67c:1220:808::93e5:80c', 389, 0, 0)), (LDAPSocketOpenError('socket connection error while opening: [Errno 111] Connection refused'), ('147.229.8.12', 389))])"
        }
    }
}
```

