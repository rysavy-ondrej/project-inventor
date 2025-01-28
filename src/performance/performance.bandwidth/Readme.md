## NAME

`performance.bandwidth`

## VERSION

1.0.0

## INFO

Network performance is used as an indicator to assess key metrics like throughput, latency, jitter, and packet loss between two endpoints or network agents. Iperf3 is a tool for network performance measurement. It is a cross-platform tool that can produce standardized performance measurements for any network. Iperf3 has client and server functionality, and can create data streams to measure the throughput between the two ends in one or both directions. The data streams can be either Transmission Control Protocol (TCP) or User Datagram Protocol (UDP). IPerf3 provides insights into network quality and capacity, making it invaluable for diagnosing network issues, evaluating network upgrades, and optimizing network performance.

Test are implimented as a Python script using [Iperf3](https://iperf.fr/iperf-download.php): to measure network performance.

## REQUIREMENTS
To install iperf3 on Rocky Linux, run: `yum install iperf3`.

## IMPLIMENTATION NOTES
The `peformance.bandwidth.clint.py` script connects to the `peformance.bandwidth.server.py` through a specific `target_host` and `target_port`. 

To establish a connection using `iperf3`, the client sends test data to a listening server. Here's a step-by-step process:

`1. Start the Iperf3 Server` - On the server machine run `peformance.bandwidth.server.py`.
This script starts the iperf3 server in listening mode on `port 5201` by default (you can specify a different port when needed).

Tests can also be done using [public iperf3 serverlists](https://github.com/R0GGER/public-iperf3-servers)

`2. Start the Iperf3 Client` - On the client machine run `peformance.bandwidth.clint.py`. By default, it connects on port 5201 unless a different port is specified in the Input configuration file.

`3. Connection Established` - The client sends a connection request to the server using TCP or UDP (depending on the test mode). Once connected, the client transmits data to the server, measuring network bandwidth, latency, and other performance metrics.

`4. Default Test Duration` - The test runs for 10 seconds by default, which can be adjusted in the input configuration file.


## INPUT  
| Parameter | Type   | Description |
|-----------|--------|-------------|
|`host`     |String  |Specifies the server IP address or hostname to connect to for the test.|
|`port`     |Integer |Sets the port number on the server to connect to (default is 5201).|
|`flag`     |Flag    |Specifies that the test should use UDP instead of TCP.|
|`duration`	|Integer |Defines the duration of the test in seconds (default is 10 seconds).|
|`reverse`  |Flag    | Runs the test in reverse mode, measuring the bandwidth from the server to the client.|


## OUTPUT

|Field              |Description|
|-------------------|-----------|
|`host`             |IP address or hostname of the server to which the client is connected.|
|`port`             |Port number used for the connection.|
|`interval`         |Time interval (in seconds) for reporting the metrics, shown for each reported result.|
|`bytes`            |Total number of bytes transferred during the test.|
|`bitrate`          |Calculated throughput in bits per second (bps), indicating the rate of data transfer.|
|`jitter`           |The variation in packet arrival time, measured in milliseconds, relevant for UDP tests.|
|`loss`             |Percentage of packets lost during the test (relevant in UDP mode).|
|`test_duration`    |Duration of the test as specified by the user, or the actual duration if it varied.|
|`mode`             |Indicates whether the test is running in TCP or UDP mode.|
|`tcp_window_size`  |The TCP window size used for the connection, relevant for TCP performance evaluation.|
|`udp_buffer_size`  |The size of the UDP buffer used for sending packets, relevant in UDP mode.|


## Iperf3 KEY OPTIONS

- **Client Options**
    - -c: - Run in client mode, connecting to the specified server.
    -  --bidir: - Perform a bidirectional test (both client and server send data).
    - -R, --reverse: - Run a reverse test (server sends data to client).
    - -p, --port: - Specify the server port (default is 5201).
    - -f, --format <format>: - Format for output (k, m, g, K, M, G for kilo, mega, or giga bits/bytes).
    - -i, --interval <interval>: - Report results at regular intervals (default: 1 second).
    - -t, --time <time>:  - Test duration in seconds (default: 10 seconds).
    - --bind <host>: - Bind to a specific local IP address.
    - --cport <port>: - Specify the local port for the client.
    - -V, --verbose: - Provide more detailed output.
    - -J: - Output results in JSON format.
    - --logfile <file>: - Write output to a specified log file.
    - -V, --verbose: - Display the iperf3 version and exit.
    - -u, --udp: - Use UDP instead of TCP.
    - --length, -l <bytes>: - Set length of the buffer to read/write (default: 128 KB for TCP, 8 KB for UDP).
    - --bandwidth <n>[KMG]: - Target bandwidth for UDP tests (default: 1 Mbps).
    - --pacing-timer <n>[KMG]: - Set the interval for UDP packet pacing.

- **Server Options**
    - -s, --server: - Run in server mode.
    - -D, --daemon: - Run the server as a daemon.
    - --logfile <file>: - Write server output to a specified file.
    - --pidfile <file>: - Write the process ID to a specified file.


## EXAMPLE

TCP Input Example (JSON Format)

```json
{
    "host": "105.235.237.2",
    "port": "5201",
    "protocol": "tcp",
    "duration": "5",
    "reverse": "false",
}
```

TCP Output Example (JSON Format)

```json
{
    "start": {
        "connected": [
            {
                "socket": 7,
                "local_host": "192.168.0.132",
                "local_port": 50863,
                "remote_host": "173.214.175.122",
                "remote_port": 5202
            }
        ],
        "version": "iperf 3.17.1",
        "system_info": "Darwin Captain.local 24.0.0 Darwin Kernel Version 24.0.0: Tue Sep 24 23:36:26 PDT 2024; root:xnu-11215.1.12~1/RELEASE_ARM64_T8103 x86_64",
        "timestamp": {
            "time": "Tue, 19 Nov 2024 20:05:32 UTC",
            "timesecs": 1732046732
        },
        "connecting_to": {
            "host": "nyc.speedtest.is.cc",
            "port": 5202
        },
        "cookie": "zj4d34zzn475dapt3q2sxnxzfcbisryw2nrl",
        "tcp_mss_default": 1348,
        "target_bitrate": 0,
        "fq_rate": 0,
        "sock_bufsize": 0,
        "sndbuf_actual": 131072,
        "rcvbuf_actual": 131072,
        "test_start": {
            "protocol": "TCP",
            "num_streams": 1,
            "blksize": 131072,
            "omit": 0,
            "duration": 1,
            "bytes": 0,
            "blocks": 0,
            "reverse": 0,
            "tos": 0,
            "target_bitrate": 0,
            "bidir": 0,
            "fqrate": 0,
            "interval": 1
        }
    },
    "intervals": [
        {
            "streams": [
                {
                    "socket": 7,
                    "start": 0,
                    "end": 1.003706,
                    "seconds": 1.0037059783935547,
                    "bytes": 1179648,
                    "bits_per_second": 9402339.13431934,
                    "omitted": false,
                    "sender": true
                }
            ],
            "sum": {
                "start": 0,
                "end": 1.003706,
                "seconds": 1.0037059783935547,
                "bytes": 1179648,
                "bits_per_second": 9402339.13431934,
                "omitted": false,
                "sender": true
            }
        }
    ],
    "end": {
        "streams": [
            {
                "sender": {
                    "socket": 7,
                    "start": 0,
                    "end": 1.003706,
                    "seconds": 1.003706,
                    "bytes": 1179648,
                    "bits_per_second": 9402338.93191831,
                    "sender": true
                },
                "receiver": {
                    "socket": 7,
                    "start": 0,
                    "end": 1.121017,
                    "seconds": 1.003706,
                    "bytes": 830368,
                    "bits_per_second": 5925819.144580323,
                    "sender": true
                }
            }
        ],
        "sum_sent": {
            "start": 0,
            "end": 1.003706,
            "seconds": 1.003706,
            "bytes": 1179648,
            "bits_per_second": 9402338.93191831,
            "sender": true
        },
        "sum_received": {
            "start": 0,
            "end": 1.121017,
            "seconds": 1.121017,
            "bytes": 830368,
            "bits_per_second": 5925819.144580323,
            "sender": true
        },
        "cpu_utilization_percent": {
            "host_total": 0.825434431194818,
            "host_user": 0.20585323977960565,
            "host_system": 0.6195811914152124,
            "remote_total": 0.0015251656362020422,
            "remote_user": 0,
            "remote_system": 0.0015251656362020422
        },
        "receiver_tcp_congestion": "cubic"
    },
    "host": "nyc.speedtest.is.cc",
    "port": "5202",
    "protocol": "tcp",
    "duration": 1,
    "reverse": false,
    "ttfb": 5.086
}
```

## EXAMPLE

UDP Input Example (JSON Format)

```json
{
    "host": "105.235.237.2",
    "port": "5201",
    "protocol": "udp",
    "duration": "5",
    "reverse": "false",
}
```

UDP Output Example (JSON Format)

```json
{
    "start": {
        "connected": [
            {
                "socket": 7,
                "local_host": "nyc.speedtest.is.cc",
                "local_port": 52755,
                "remote_host": "173.214.175.122",
                "remote_port": 5202
            }
        ],
        "version": "iperf 3.17.1",
        "system_info": "Darwin Captain.local 24.0.0 Darwin Kernel Version 24.0.0: Tue Sep 24 23:36:26 PDT 2024; root:xnu-11215.1.12~1/RELEASE_ARM64_T8103 x86_64",
        "timestamp": {
            "time": "Tue, 19 Nov 2024 20:09:03 UTC",
            "timesecs": 1732046943
        },
        "connecting_to": {
            "host": "nyc.speedtest.is.cc",
            "port": 5202
        },
        "cookie": "u7ih5v4slh7mmrfjemrzkssha32cpiftk3gq",
        "target_bitrate": 1048576,
        "fq_rate": 0,
        "sock_bufsize": 0,
        "sndbuf_actual": 9216,
        "rcvbuf_actual": 786896,
        "test_start": {
            "protocol": "UDP",
            "num_streams": 1,
            "blksize": 1348,
            "omit": 0,
            "duration": 1,
            "bytes": 0,
            "blocks": 0,
            "reverse": 0,
            "tos": 0,
            "target_bitrate": 1048576,
            "bidir": 0,
            "fqrate": 0,
            "interval": 1
        }
    },
    "intervals": [
        {
            "streams": [
                {
                    "socket": 7,
                    "start": 0,
                    "end": 1.000251,
                    "seconds": 1.000251054763794,
                    "bytes": 132104,
                    "bits_per_second": 1056566.7438856813,
                    "packets": 98,
                    "omitted": false,
                    "sender": true
                }
            ],
            "sum": {
                "start": 0,
                "end": 1.000251,
                "seconds": 1.000251054763794,
                "bytes": 132104,
                "bits_per_second": 1056566.7438856813,
                "packets": 98,
                "omitted": false,
                "sender": true
            }
        }
    ],
    "end": {
        "streams": [
            {
                "udp": {
                    "socket": 7,
                    "start": 0,
                    "end": 1.000251,
                    "seconds": 1.000251,
                    "bytes": 132104,
                    "bits_per_second": 1056566.801732765,
                    "jitter_ms": 0.26374305619287425,
                    "lost_packets": 0,
                    "packets": 98,
                    "lost_percent": 0,
                    "out_of_order": 0,
                    "sender": true
                }
            }
        ],
        "sum": {
            "start": 0,
            "end": 1.117025,
            "seconds": 1.117025,
            "bytes": 132104,
            "bits_per_second": 1056566.801732765,
            "jitter_ms": 0.26374305619287425,
            "lost_packets": 0,
            "packets": 98,
            "lost_percent": 0,
            "sender": true
        },
        "sum_sent": {
            "start": 0,
            "end": 1.000251,
            "seconds": 1.000251,
            "bytes": 132104,
            "bits_per_second": 1056566.801732765,
            "jitter_ms": 0,
            "lost_packets": 0,
            "packets": 98,
            "lost_percent": 0,
            "sender": true
        },
        "sum_received": {
            "start": 0,
            "end": 1.117025,
            "seconds": 1.117025,
            "bytes": 132104,
            "bits_per_second": 946113.1129562902,
            "jitter_ms": 0.26374305619287425,
            "lost_packets": 0,
            "packets": 98,
            "lost_percent": 0,
            "sender": false
        },
        "cpu_utilization_percent": {
            "host_total": 73.90588779348393,
            "host_user": 70.31721742921187,
            "host_system": 3.5884494505138456,
            "remote_total": 0.002036423329442827,
            "remote_user": 0,
            "remote_system": 0.002036910046299768
        }
    },
    "host": "nyc.speedtest.is.cc",
    "port": "5202",
    "protocol": "udp",
    "duration": 1,
    "reverse": false,
    "ttfb": 1.859
}
```


## EXAMPLE

Input Example (Failed Operation):

```json
{
    "host": "192.168.0.132",
    "port": "5201",
    "protocol": "udp",
    "duration": "5",
    "reverse": "false",
}
```

Output Example (JSON Format):

```json
{
    "start": {
        "connected": [],
        "version": "iperf 3.17.1",
        "system_info": "Darwin Captain.local 24.0.0 Darwin Kernel Version 24.0.0: Tue Sep 24 23:36:26 PDT 2024; root:xnu-11215.1.12~1/RELEASE_ARM64_T8103 x86_64"
    },
    "intervals": [],
    "end": {},
    "error": "control socket has closed unexpectedly",
    "host": "192.168.0.132",
    "port": "5201",
    "protocol": "tcp",
    "duration": 1,
    "reverse": false,
    "ttfb": 0.034
}
```