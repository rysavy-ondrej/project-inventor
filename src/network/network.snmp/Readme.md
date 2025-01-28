## NAME

`network.snmp`

## VERSION

1.0.0

## INFO
SNMP (Simple Network Management Protocol) – is a lightweight protocol used for managing and monitoring network devices. It is widely utilized for collecting information from devices like routers, switches, servers, and IoT systems. SNMP operates over IP networks, making it ideal for monitoring network performance and detecting issues in real-time. Devices using SNMP can communicate status updates and metrics, such as CPU usage or network traffic, to a central management system. SNMP supports both the querying of data and sending of unsolicited alerts (traps) from devices to management consoles.

## IMPLEMENTATION NOTES
This script uses `easysnmp` library to perform SNMP GET test on the target host. It uses input parametrs such as `oids` and `community_string`. It creates prepared session at the beginning, then performs an SNMP GET operation to retrieve a particular piece of information.

**This test works with SNMP version 2**

#### Used modules
- `easysnmp==0.2.6` module (https://easysnmp.readthedocs.io/en/latest/#): to work with SNMP service.
- `icmplib==3.0.4` module (https://pypi.org/project/icmplib/): used to check if a string is a valid hostname (`is_hostname`).



## INPUT

| Parameter       | Type    | Description                                   |
|-----------------|---------|-----------------------------------------------|
| target_host     | string  | The hostname or IP address |
| oids     | string  | List of OID for SNMP GET divided by `,` |
| community_string     | string  | Community string to get access |


## OUTPUT
| Field            | Type    | Description                                |
|------------------|---------|--------------------------------------------|
| IP_address           | string | Show `target_host`'s IP address if it is hostname|
| oids           | dict |  Contains `get_value` and `snmp_data_type`. |
| get_value           | string |  Contains result of GET operation. |
| response_time           | string |  Time taken to send and receive response from the server. |
| snmp_data_type           | string |  Contains what data type has the result. |
| pushed_oid           | string |  Contains what OID was pushed to the target. Only appears, if there is one OID in `input.json`|




## EXAMPLE
#### Input Example (JSON format):
```json
{
    "target_host": "localhost",
    "oids": "1.3.6.1.2.1.1.1.0,1.3.6.1.2.1.1.5.0",
    "community_string": "public"
}
```

#### Output Example (JSON format):
```json
{
    "output": {
        "target_host": "isa.fit.vutbr.cz",
        "IP_address": "2001:67c:1220:8b0::93e5:b012",
        "1.3.6.1.2.1.1.5.0": {
            "get_value": "isa.fit.vutbr.cz",
            "snmp_data_type": "OCTETSTR"
        },
        "1.3.6.1.2.1.1.5.1": {
            "get_value": "NOSUCHINSTANCE",
            "snmp_data_type": "NOSUCHINSTANCE"
        },
        "response_time": 0.045
    },
    "queue": {
        "target_host": "isa.fit.vutbr.cz",
        "IP_address": "2001:67c:1220:8b0::93e5:b012",
        "1.3.6.1.2.1.1.5.0": {
            "get_value": "isa.fit.vutbr.cz",
            "snmp_data_type": "OCTETSTR"
        },
        "1.3.6.1.2.1.1.5.1": {
            "get_value": "NOSUCHINSTANCE",
            "snmp_data_type": "NOSUCHINSTANCE"
        },
        "response_time": 0.045
    }
}
```

## EXAMPLE (Failed operation)
#### Input Example (JSON format):
```json
{
    "target_host": "localhost",
    "oids": "1.3.6.1.2.1.1.1.0,1.3.6.1.2.1.1.5.0",
    "community_string": "wrong_community_string"
}
```

#### Output Example (JSON format):
```json
{
    "output": {
        "status": "error",
        "error": {
            "error_code": "ERROR: something went wrong during testing",
            "description": "timed out while connecting to remote host"
        }
    },
    "queue": {
        "status": "error",
        "error": {
            "error_code": "ERROR: something went wrong during testing",
            "description": "timed out while connecting to remote host"
        }
    }
}
```
