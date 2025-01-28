## NAME

`network.mqtt`

## VERSION

1.0.0

## INFO

MQTT (Message Queuing Telemetry Transport) - is a lightweight network protocol designed to exchange messages between devices with low bandwidth or high latency. It is ideal for IoT (Internet of Things) and M2M (machine-to-machine) communications. These IoT devices use MQTT for data transmission as it is easy to implement and can efficiently transmit IoT data. MQTT supports the transmission of messages from devices to the cloud and vice versa.


## How to test?
**Do it using root privileges (su or sudo)**
```
1. pip3 install -r requirements.txt 
2. pytest test_mqtt.py /// pytest
```

## IMPLEMENTATION NOTES
Using `paho-mqtt` library, script creates connection to `target_host`. After that it starts `loop` for **0.3 seconds**, so `client` has time to `subscribe` on some topic and get response from `broker`. After receiving topic `payload` and getting `SUBACK` it ends connection by stopping `loop` and client disconnecting.

For test purpose, I subscribe on some **reserved** topics in `input.json`.


#### Used modules

- `paho-mqtt==2.1.0` module (https://docs.python.org/3/library/socket.html): A Python implementation of SSHv2..
- `icmplib==3.0.4` module (https://pypi.org/project/icmplib/): used to ping servers before testing service.

## INPUT

| Parameter       | Type    | Description                                   |
|-----------------|---------|-----------------------------------------------|
| target_host     | string  | The hostname or IP address |
| topic_names     | string_list  | The list of topics to obtain information divided by `,` |

## OUTPUT

| Field            | Type    | Description                                |
|------------------|---------|--------------------------------------------|
| IP_address           | string | Show `target_host`'s IP address |
|  connected_time           | string |  Time connected to the service  |
|  duration           | string |  Total time taken to the monitoring  |
|  response_time           | string |  Time taken to send and receive the result  |
|  is_connected           | bool |  Is agent succesfully connected to the service  |
|  reason_code_list           | string |  Result, after sending SUBSCRIBE  |
|  $SYS/broker/version           | string | Topic name, to subscribe for test purpose  |
|  $SYS/broker/uptime           | string |  Topic name, to subscribe for test purpose  |





## EXAMPLE
#### Input Example (JSON format):
```json
{
    "target_host": "test.mosquitto.org",
    "topic_names": "python/mqtt,$SYS/broker/version,$SYS/broker/uptime"
}
```
#### Output Example (JSON Format)
```json
{
    "output": {
        "target_host": "test.mosquitto.org",
        "IP_address": "91.121.93.94",
        "is_connected": true,
        "connected_time": "2024-06-29T16:42:43.155399Z",
        "reason_code_list": "[ReasonCode(Suback, 'Granted QoS 0')]",
        "$SYS/broker/version": "b'mosquitto version 2.0.99'",
        "$SYS/broker/uptime": "b'1140410 seconds'"
    },
    "queue": {
        "target_host": "test.mosquitto.org",
        "IP_address": "91.121.93.94",
        "is_connected": true,
        "connected_time": "2024-06-29T16:42:43.155399Z",
        "reason_code_list": "[ReasonCode(Suback, 'Granted QoS 0')]",
        "$SYS/broker/version": "b'mosquitto version 2.0.99'",
        "$SYS/broker/uptime": "b'1140410 seconds'"
    }
}
```

## Example (Failed operation)
#### Input Example (JSON Format)
```json
{
    "target_host": "2001:41d0:a:6f1c::12",
    "topic_names": "python/mqtt,$SYS/broker/version,$SYS/broker/uptime"
}
```
#### Output Example (JSON Format)
```json
{
    "output": {
        "status": "error",
        "error": {
            "error_code": "CONFIG FILE ERROR",
            "description": "timed out"
        }
    },
    "queue": {
        "status": "error",
        "error": {
            "error_code": "CONFIG FILE ERROR",
            "description": "timed out"
        }
    }
}
```