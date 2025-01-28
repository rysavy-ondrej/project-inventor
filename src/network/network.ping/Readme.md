# Network Ping Test

A PING test is a basic network diagnostic tool used to verify the reachability of a host on an IP network, measuring the round-trip time (RTT) for messages sent from the originating host to a destination computer. The test operates by sending Internet Control Message Protocol (ICMP) echo request packets to the target host and waiting for it to send back an echo reply. This test is commonly used to check network connectivity and performance.

## Requirements

| Library | Version   |
| ------- | --------- |
| icmplib | 3.0.4     |

The test needs to be run with root privileges (e.g., using `sudo`) or with elevated privileges, because it needs to be able to send ICMP messages and have access to raw sockets.
The ping utility on linux doesn't require `sudo` because it has necessary setuid permission, allowing regular users to send ICMP packets without elevated privileges.

## Input

```proto
message PingTestConfig {
  string target_host = 1; // The IP address or hostname of the target.
  int32 packet_size = 2; // The size of the ICMP payload in bytes.
  int32 packet_count = 3; // The number of ICMP packets to send.
  float interpacket_delay = 4; // The delay between probes in seconds.
  float timeout = 5; // The maximum time to wait for a response in seconds.
}
```

## Output

```proto
// Top-level message representing the entire test result
message PingTestResult {
  int32 run_id = 1;             // The identification of the test instance.
  TestStatus status = 2; // The status of the test (e.g., "completed")
  PingTestSummary summary = 2; // Nested message for summary details
  repeated PingTestDetails details = 3; // Array of Detail messages for each probe
}

// Summary of the test results
message PingTestSummary {
  int32 pkts_sent = 1; // Total packets sent
  int32 pkts_received = 2; // Total packets received
  float pkts_lost = 3; // Percentage of packets lost
  float rtt_min = 4; // Minimum round trip time in milliseconds
  float rtt_max = 5; // Maximum round trip time in milliseconds
  float rtt_avg = 6; // Average round trip time in milliseconds
  float rtt_stdev = 7; // Standard deviation of round trip times in milliseconds
  float jitter = 8; // Jitter in milliseconds
}

// Details of each individual probe
message PingTestDetails {
  string IP_address = 1; // The IP address of the target host
  int32 connected_time = 2; // Timestamp of the connection
  int32 response_time = 3; // Timestamp of the response
  float rtt = 4; // Round Trip Time in milliseconds
  float bytes_received = 5; // Number of bytes received 
  string status_msg = 6; // Response code or message (e.g., "echo_reply")
  int32 status_code = 7; // ICMP code
}
```

Response code to string mapping:

| Code | Message                  |
|------|--------------------------|
| 0    | Echo Reply               |
| 3    | Destination Unreachable  |
| 4    | Source Quench            |
| 5    | Redirect Message         |
| 8    | Echo Request             |
| 9    | Router Advertisement     |
| 10   | Router Solicitation      |
| 11   | Time Exceeded            |
| 12   | Parameter Problem        |
| 13   | Timestamp Request        |
| 14   | Timestamp Reply          |
| 15   | Information Request      |
| 16   | Information Reply        |
| 17   | Address Mask Request     |
| 18   | Address Mask Reply       |
| 30   | Traceroute               |
| 31   | Datagram Conversion Error|
| 32   | Mobile Host Redirect     |
| 42   | Extended Echo Request    |
| 43   | Extended Echo Reply      |


## How to run simple test

```bash
sudo pytest monitor_ping.py
```

The result will be in the `test` directory in file `output.json`
For running the test you need `sudo` permissions just as you would need them for running the script itself.

## Examples

INPUT:

```json
{
    "target_host": "8.8.8.8",
    "packet_size": 200,
    "packet_count": 2,
    "interpacket_delay": 3,
    "timeout": 5
}
```

OUTPUT:

```json
{
    "run_id": 1,
    "status": "completed",
    "summary": {
        "IP_address": "8.8.8.8",
        "pkts_send": 2,
        "pkts_received": 2,
        "pkts_lost": 0.0,
        "rtt_min": 38.753,
        "rtt_max": 577.212,
        "rtt_avg": 307.983,
        "rtt_stddev": 380.748,
        "jitter": 538.459
    },
    "details": [
        {
            "connected_time": "2024-12-01T13:52:23.104092Z",
            "response_time": "2024-12-01T13:52:23.681303Z",
            "rtt": 577.212,
            "bytes_received": 208,
            "status_msg": "Echo Reply",
            "status_code": 0
        },
        {
            "connected_time": "2024-12-01T13:52:23.681686Z",
            "response_time": "2024-12-01T13:52:23.720438Z",
            "rtt": 38.753,
            "bytes_received": 208,
            "status_msg": "Echo Reply",
            "status_code": 0
        }
    ]
}
```

## Example (failed test due to host unreachable)

INPUT:

```json
{
    "target_host": "192.168.1.11",
    "packet_size": 200,
    "packet_count": 2,
    "interpacket_delay": 3,
    "timeout": 5
}
```

OUTPUT:

```json
{
    "run_id": 1,
    "status": "completed",
    "summary": {
        "IP_address": "192.168.1.11",
        "pkts_send": 2,
        "pkts_received": 0,
        "pkts_lost": 100.0,
        "rtt_min": 0,
        "rtt_max": 0,
        "rtt_avg": 0.0,
        "rtt_stddev": 0.0,
        "jitter": 0.0
    },
    "details": [
        {
            "connected_time": "2024-12-01T14:15:11.302364Z",
            "response_time": "2024-12-01T14:15:14.352015Z",
            "rtt": 0,
            "bytes_received": 236,
            "status_msg": "Destination host unreachable",
            "status_code": 3
        },
        {
            "connected_time": "2024-12-01T14:15:14.352273Z",
            "response_time": "2024-12-01T14:15:17.388644Z",
            "rtt": 0,
            "bytes_received": 236,
            "status_msg": "Destination host unreachable",
            "status_code": 3
        }
    ]
}
```
