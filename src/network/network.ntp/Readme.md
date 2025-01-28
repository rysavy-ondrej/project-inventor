## NAME

`network.ntp`

## VERSION

1.0.0

## INFO
`NTP` is designed to synchronize the time throughout an entirenetwork infrastructure, including servers, switches, routers, hostmachines, wireless access points, uninterruptible power supply(UPS), and so on.

This test is designed to check the NTP service on a given server by connecting to NTP server and collecting information.
 

## IMPLEMENTATION NOTES
The script connects to the specified `target_host`. The connection timeout is 5 seconds

Script creates client object using `NTPClient()` from `ntplib` and sends request to the NTP server time. All data from the reques are stored in `response`, which is parsed to the `probe` for output.


#### Used modules
- `ntplib==0.4.0` module (https://pypi.org/project/ntplib/): simple interface to query NTP servers from Python.
- `icmplib==3.0.4` module (https://pypi.org/project/icmplib/): used to check if a string is a valid hostname (`is_hostname`).



## INPUT

| Parameter       | Type    | Description                                   |
|-----------------|---------|-----------------------------------------------|
| target_host     | string  | The hostname or IP address |


## OUTPUT
The output is a hostname as key, and dictionary as a value, that contains the results of check. `"someserver": {...}`
| Field            | Type    | Description                                |
|------------------|---------|--------------------------------------------|
| target_host     | string  | The hostname or IP address |
| IP_address           | string | Show `target_host`'s IP address |
| state           | string |  Does the server has open/closed/filtered state on a selected port. |
| connected_time           | string |  Time when the script connected to a specific port.  |
| delay           | string |  Round-trip delay to the NTP server. |
| offset           | string |  The time difference (in seconds) between the server and the client clocks. |
| leap_indicator           | string |  2-bit integer warning of an impending leap second to be inserted or deleted in the last minute of the current month. |
| stratum           | string |  The stratum level of the NTP server. |
| refid           | string |  32-bit code identifying the particular server  or reference clock. |
| root_delay           | string |  Total round-trip delay to the reference clock. |
| root_dispersion           | string |  Total dispersion to the reference clock. |
| precision           | string |  8-bit signed integer representing the precision of the   system clock, in `log2` seconds. For instance, a value of `-18` corresponds to a precision of about **one microsecond**. |
tx_time | string | Time at the server when the response left  for the client.
dest_time | string | Time at the client when the reply arrived from the server.
recv_time | string | Time at the server when the request arrived from the client.



## EXAMPLE
#### Input Example (JSON format):
```json
{
    "target_host": "time.apple.com"
}
```

#### Output Example (JSON format):
```json
{
    "output": {
        "target_host": "tik.cesnet.cz",
        "IP_address": "195.113.144.201",
        "connected_time": "2024-11-22T11:58:02.884535Z",
        "delay": "0.021407127380371094",
        "offset": "-10.703453540802002",
        "leap_indicator": "no warning",
        "stratum": "1",
        "refid": "ATOM",
        "root_delay": "0.0",
        "root_dispersion": "0.0009918212890625",
        "precision": "-23",
        "tx_time": "2024-11-22T11:57:52.169491Z",
        "recv_time": "2024-11-22T11:57:52.169408Z",
        "dest_time": "2024-11-22T11:58:02.883648Z"
    },
    "queue": {
        "target_host": "tik.cesnet.cz",
        "IP_address": "195.113.144.201",
        "connected_time": "2024-11-22T11:58:02.884535Z",
        "delay": "0.021407127380371094",
        "offset": "-10.703453540802002",
        "leap_indicator": "no warning",
        "stratum": "1",
        "refid": "ATOM",
        "root_delay": "0.0",
        "root_dispersion": "0.0009918212890625",
        "precision": "-23",
        "tx_time": "2024-11-22T11:57:52.169491Z",
        "recv_time": "2024-11-22T11:57:52.169408Z",
        "dest_time": "2024-11-22T11:58:02.883648Z"
    }
}
```



## EXAMPLE (Failed operation)
#### Input Example (JSON format):
```json
{
    "target_host": "time.apple.com123"
}
```

#### Output Example (JSON format):
```json
{
    "output": {
        "target_host": "time.apple.com123",
        "retcode": "ERROR: Can not connect to target the target.",
        "errcode": "[Errno -2] Name or service not known"
    },
    "queue": {
        "target_host": "time.apple.com123",
        "retcode": "ERROR: Can not connect to target the target.",
        "errcode": "[Errno -2] Name or service not known"
    }
}
```
