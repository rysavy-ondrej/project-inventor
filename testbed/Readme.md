# CHANGES 
- New docker file created for dynamic analysis. It is necessary to install chromium, node.js and puppeteer library for dynamic analysis. For that reason when starting webapp.http.dynamic tests you need set dockerfile to [Dockerfile.node](..%2FDockerfile.node)  instead of [Dockerfile](..%2FDockerfile) in [docker-compose.yaml](docker-compose.yaml)
# INVENTOR Testbed

This is a lightweight, containerized environment for continuous monitoring and testing using Docker Compose and PowerShell scripting. The system is designed to manage test execution, log collection, and data storage efficiently while keeping configuration simple and flexible.

Note: To run outside the container, use the [system service](service/Readme.md) to ensure continuous operation of the testbed.


## Overview

The testbed uses a YAML configuration file to define monitoring sessions. Each session describes:

- **Monitors**: The available test modules and their execution details.
- **Schedule**: The test sessions that are executed periodically, including target parameters and output settings.

Using Docker Compose, different monitoring sessions can be deployed in isolated containers. This enables parallel test execution and easy scaling while maintaining separation of concerns.

## Configuration File Structure

The configuration file is divided into two main sections: **Monitors** and **Schedule**.

### Monitors Section

This section defines the set of available monitoring modules. Each monitor is defined as an object with the following key properties:

- **name**: A unique identifier for the monitor (for example, a test type like `network.ping`).
- **module**: The name of the module or library that implements the monitor’s functionality.
- **exec**: The relative path to the executable or script that runs the monitor.

Define each monitor so that the scheduling logic can later reference it by name. This abstraction decouples the configuration of test sessions from the specific implementation details.

### Schedule Section

This section specifies how and when the tests should be executed. Each scheduled test entry includes:

- **test**: The name of the monitor (from the Monitors section) that should be used for this session.
- **write-to**: A logical name for the session output. *Note:* `Run-MonitorSession.ps1` no longer writes files itself — it emits every result to standard output. The destination (file name, Kafka topic, …) is now decided by the output **sink** the result stream is piped into (see [Output sinks](#output-sinks)). This field is retained for documentation/back-compat and is not consumed by the runner.
- **targets**: An array of target objects. Each target contains the parameters for an individual test execution. This has form of JSON input expected by the test.
- **repeat-every**: A time interval (e.g., `"30s"`, `"1m"`) that determines how often the test session should be repeated.
- **omit-fields**: Removes the specified fields from the outpu JSON. This is an array of fields.
- **hash-fields**: Compute a new fields as MD5 hash fo the specified field. This is an arrayf of `{"src": SOURCE-FIELD-NAME, "trg": HASH_FIELD-NAME }` objects.
Customize each test session by adjusting the targets and timing parameters to suit your monitoring requirements.

## Example Configuration

Below is an example YAML configuration file illustrating two monitoring sessions using the `network.ping` monitor:

```yaml
monitors:
  - name: network.ping
    module: network_ping
    exec: src/network/network.ping

schedule:
  - test: network.ping
    write-to: network.ping.vutbr 
    targets:  
        - { "target_host": "www.vut.cz", "packet_size": 200, "packet_count": 5, "interpacket_delay": 1, "timeout": 5 }
        - { "target_host": "www.fce.vutbr.cz", "packet_size": 200, "packet_count": 5, "interpacket_delay": 1, "timeout": 5 }
        - { "target_host": "www.fsi.vutbr.cz", "packet_size": 200, "packet_count": 5, "interpacket_delay": 1, "timeout": 5 }
        - { "target_host": "www.fekt.vutbr.cz", "packet_size": 200, "packet_count": 5, "interpacket_delay": 1, "timeout": 5 }
    repeat-every: 30s

  - test: network.ping
    write-to: network.ping.internet
    omit-fields: [ "rtt_stddev" ]  
    hash-fields: [ { src: "IP_address", trg: "IP_address-hash" } ]  
    targets:  
        - { "target_host": "google.com", "packet_size": 100, "packet_count": 3, "interpacket_delay": 1, "timeout": 5 }
        - { "target_host": "youtube.com", "packet_size": 100, "packet_count": 3, "interpacket_delay": 1, "timeout": 5 }
        - { "target_host": "facebook.com", "packet_size": 100, "packet_count": 3, "interpacket_delay": 1, "timeout": 5 }
        - { "target_host": "amazon.com", "packet_size": 100, "packet_count": 3, "interpacket_delay": 1, "timeout": 5 }
    repeat-every: 1m
```

Monitors Section defines a single monitor (network.ping) that is implemented by the network_ping module and executed from the src/network/network.ping path.

Two test sessions are defined:

* The first session targets several local or institutional websites and outputs results to network.ping.vutbr.json. It is set to run every 30 seconds.
* The second session targets popular internet domains (e.g., google.com, youtube.com) and outputs to network.ping.internet.json. This session is configured to run every minute.

## Output sinks

`Run-MonitorSession.ps1` does not store results itself. It runs the schedule and
writes each measurement as a single compact JSON document to **standard output**
(via `Write-Output`). What happens to that stream is decided by the **sink** the
output is piped into. Three sinks are provided:

| Sink script | Destination | Key parameters |
| --- | --- | --- |
| [`Out-Console.ps1`](Out-Console.ps1) | The host console (stdout) | — |
| [`Out-FileByDay.ps1`](Out-FileByDay.ps1) | A per-day file `<BaseName>.<yyyy-MM-dd>.json` | `-BaseName`, `-OutPath` |
| [`Out-Kafka.ps1`](Out-Kafka.ps1) | A Kafka topic (via the `kcat`/`kafkacat` CLI) | `-KafkaBroker`, `-KafkaTopic` |

Basic usage — pick one sink and pipe the session into it:

```bash
# Print results to the console:
pwsh ./Run-MonitorSession.ps1 -TestSuiteFile schedules/network.ping.yaml | pwsh ./Out-Console.ps1

# Append results to ./results/network.ping.<date>.json (a new file each day):
pwsh ./Run-MonitorSession.ps1 -TestSuiteFile schedules/network.ping.yaml | pwsh ./Out-FileByDay.ps1 -BaseName network.ping -OutPath ./results

# Publish results to a Kafka topic:
pwsh ./Run-MonitorSession.ps1 -TestSuiteFile schedules/network.ping.yaml | pwsh ./Out-Kafka.ps1 -KafkaBroker localhost:9092 -KafkaTopic inventor.results
```

`Out-FileByDay.ps1` re-evaluates the date for every record, so the output file
rolls over automatically at midnight even for a long-running session.
`Out-Kafka.ps1` uses each result's `Meta.TestId` as the Kafka message key.

### Using multiple sinks at once

The previous version of the runner could write to files, Kafka and stdout
simultaneously. With the sink approach the same is achieved by **fanning the
stream out** to several sinks. The simplest way is `Tee-Object`, which forwards
the pipeline while also branching a copy to another sink:

```bash
# Store to a per-day file AND echo to the console at the same time:
pwsh -Command "& ./Run-MonitorSession.ps1 -TestSuiteFile schedules/network.ping.yaml |
    Tee-Object -Variable line | & ./Out-Console.ps1; <# 'line' holds the last record #>"
```

For more than two destinations, or to combine file + Kafka + console, wrap the
sinks in a small fan-out script that forwards each line to every sink in its
`process` block, e.g.:

```powershell
# Out-Multi.ps1 — forward each result to several sinks.
param([Parameter(ValueFromPipeline)] [string]$InputObject)
process {
    $InputObject | ./Out-Console.ps1
    $InputObject | ./Out-FileByDay.ps1 -BaseName network.ping -OutPath ./results
    $InputObject | ./Out-Kafka.ps1 -KafkaBroker localhost:9092 -KafkaTopic inventor.results
}
```

```bash
pwsh ./Run-MonitorSession.ps1 -TestSuiteFile schedules/network.ping.yaml | pwsh ./Out-Multi.ps1
```

This keeps each sink small and single-purpose while still allowing any
combination of outputs.

## Deployment and Usage
The testbed is deployed using Docker Compose. Each monitoring session is run in a separate container, providing isolation and better scalability.

Below is an example docker-compose.yml file that deploys two containers, each executing a different monitoring session:

```yaml
version: "3.8"

services:
  testbed-dummy:
    build: 
      context: ..
      dockerfile: Dockerfile
    working_dir: /inventor/testbed
    command: pwsh -Command "& ./Run-MonitorSession.ps1 -TestSuiteFile schedules/dummy.yaml | & ./Out-FileByDay.ps1 -BaseName dummy -OutPath ./results/"
    volumes:
      - ./results:/inventor/testbed/results

  testbed-network.ping:
    build: 
      context: ..
      dockerfile: Dockerfile
    working_dir: /inventor/testbed
    command: pwsh -Command "& ./Run-MonitorSession.ps1 -TestSuiteFile schedules/network.ping.yaml | & ./Out-FileByDay.ps1 -BaseName network.ping -OutPath ./results/"
    volumes:
      - ./results:/inventor/testbed/results
```

Both services use the same Docker image (built from the provided Dockerfile) and set the working directory to /inventor/testbed inside the container.
Each container runs the `Run-MonitorSession.ps1` PowerShell script with its corresponding YAML configuration file, then pipes the result stream into an output **sink** script (here `Out-FileByDay.ps1`). Because `pwsh -Command` is used to run a pipeline, both stages run inside the same container.
Results from the tests are stored in the container’s ./results directory and are shared with the host machine via a mounted volume.

Add more sessions by introducing new services in `docker-compose.yaml` or write your own docker compose specification if you need an independent environment.

## Running the Testbed
To launch all the monitoring sessions, simply run:

```bash
docker-compose -f docker-compose.yaml up
```

Docker Compose will build the image (if necessary) and start all defined services concurrently. Each container will execute its configured monitoring session independently, periodically running tests and writing outputs to the shared results directory.

### Running only selected service

In Docker Compose, each section defines a service. It is possible to run only a selected service as follows:

```bash
docker compose up testbed-webapp.http.dynamic
```
