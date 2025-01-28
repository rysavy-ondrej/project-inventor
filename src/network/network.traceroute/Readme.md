# Network Traceroute Test

Trace the path packets take from the source to a specified destination across a computer network, identifying each hop along the way.

- Send packets with incrementally increasing TTL values to trace the network path.
- Identify nodes (routers/switches) based on ICMP "Time Exceeded" messages.
- Determine the path and measure round-trip time to each node.


## Requirements

| Library | Version   |
| ------- | --------- |
| icmplib | 3.0.4     |

## Input

```proto
message TracerouteTestConfig {
  string target_host = 1; 
  int32 ttl_max = 2; 
  int32 packet_size = 3; 
  string timeout = 4; 
  int32 repeats = 5; 
}
```

## Output

The schema of the output is defined as follows:

```proto
message TracerouteTestResult {
  int32 run_id = 1; // Unique identifier for the test run
  TestStatus status = 2; // Status of the test run
  Summary summary = 3;  // Nested message containing summary information
  repeated Detail details = 4;  // Repeated nested message containing detailed information
}

message Summary {
  string IP_address = 1;   // Target host IP address
  int32 min_hops = 2;   // Minimum number of hops
  int32 max_hops = 3;  // Maximum number of hops
  double path_stability = 4;  // Path stability, a value between 0 and 1 (0: unstable, 1: stable)
  double packet_loss = 5;   // Packet loss percentage
}

message Detail {
  int32 run = 1;    // Run number  
  repeated Hop hops = 2; // Repeated nested message containing hop information
}

message Hop {
  int32 hop_number = 1;    // Hop number 
  string hop_ip = 2;  // IP address of the hop (can be not available)
  double hop_rtt = 3; // Round-trip time to the hop 
}
```

## How to run simple test

```bash
sudo pytest monitor_traceroute.py
```

The result will be in the `test` directory in file `output.json`
For running the test you need `sudo` permissions just as you would need them for running the script itself.

## Examples

INPUT:

```json
{
  "target_host": "8.8.8.8",
  "ttl_max" : 50,
  "packet_size": 200,
  "timeout": 3,
  "repeats" : 2
}
```

OUTPUT:

```json
{
    "run_id": 1,
    "status": "completed",
    "summary": {
        "IP_address": "8.8.8.8",
        "min_hops": 9,
        "max_hops": 9,
        "path_stability": 1.0,
        "packet_loss": 0.0
    },
    "details": [
        {
            "run": 1,
            "hops": [
                {
                    "hop_number": 1,
                    "hop_ip": "147.229.220.1",
                    "hop_rtt": 4.612
                },
                {
                    "hop_number": 2,
                    "hop_ip": "147.229.254.69",
                    "hop_rtt": 0.462
                },
                {
                    "hop_number": 3,
                    "hop_ip": "147.229.253.233",
                    "hop_rtt": 0.377
                },
                {
                    "hop_number": 4,
                    "hop_ip": "147.229.252.17",
                    "hop_rtt": 1.976
                },
                {
                    "hop_number": 5,
                    "hop_ip": "10.5.0.46",
                    "hop_rtt": 4.756
                },
                {
                    "hop_number": 6,
                    "hop_ip": "195.113.157.70",
                    "hop_rtt": 4.401
                },
                {
                    "hop_number": 7,
                    "hop_ip": "192.178.99.19",
                    "hop_rtt": 4.229
                },
                {
                    "hop_number": 8,
                    "hop_ip": "216.239.51.183",
                    "hop_rtt": 4.158
                },
                {
                    "hop_number": 9,
                    "hop_ip": "8.8.8.8",
                    "hop_rtt": 4.027
                }
            ]
        },
        {
            "run": 2,
            "hops": [
                {
                    "hop_number": 1,
                    "hop_ip": "147.229.220.1",
                    "hop_rtt": 1.634
                },
                {
                    "hop_number": 2,
                    "hop_ip": "147.229.254.69",
                    "hop_rtt": 0.371
                },
                {
                    "hop_number": 3,
                    "hop_ip": "147.229.253.233",
                    "hop_rtt": 0.57
                },
                {
                    "hop_number": 4,
                    "hop_ip": "147.229.252.17",
                    "hop_rtt": 1.584
                },
                {
                    "hop_number": 5,
                    "hop_ip": "10.5.0.46",
                    "hop_rtt": 4.58
                },
                {
                    "hop_number": 6,
                    "hop_ip": "195.113.157.70",
                    "hop_rtt": 4.592
                },
                {
                    "hop_number": 7,
                    "hop_ip": "192.178.99.19",
                    "hop_rtt": 4.19
                },
                {
                    "hop_number": 8,
                    "hop_ip": "216.239.51.183",
                    "hop_rtt": 4.092
                },
                {
                    "hop_number": 9,
                    "hop_ip": "8.8.8.8",
                    "hop_rtt": 4.03
                }
            ]
        }
    ]
}
```

## Example (failed test due to unreachable target)

INPUT
    
```json
{
    "target_host": "192.168.1.11",
    "ttl_max": 10,
    "packet_size": 200,
    "timeout": 3,
    "repeats": 1
}
   
```

OUTPUT

```json
{
    "run_id": 1,
    "status": "completed",
    "summary": {
        "IP_address": "192.168.1.11",
        "min_hops": 3,
        "max_hops": 3,
        "path_stability": "Target not reached",
        "packet_loss": 0.0
    },
    "details": [
        {
            "run": 1,
            "hops": [
                {
                    "hop_number": 1,
                    "hop_ip": "147.229.220.1",
                    "hop_rtt": 3.301
                },
                {
                    "hop_number": 2,
                    "hop_ip": "147.229.254.69",
                    "hop_rtt": 0.534
                },
                {
                    "hop_number": 3,
                    "hop_ip": "147.229.253.233",
                    "hop_rtt": 0.707
                }
            ]
        }
    ]
}
```
