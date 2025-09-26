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
- **write-to**: The file name where the test output will be stored.
- **targets**: An array of target objects. Each target contains the parameters for an individual test execution. This has form of JSON input expected by the test.
- **repeat-every**: A time interval (e.g., `"30s"`, `"1m"`) that determines how often the test session should be repeated.
- **omit-fields**: Removes the specified fields from the outpu JSON. This is an array of fields.
- **hash-fields**: Compute a new fields as MD5 hash fo the specified field. This is an arrayf of `{"src": SOURCE-FIELD-NAME, "trg": HASH_FIELD-NAME }` objects.
Customize each test session by adjusting the targets and timing parameters to suit your monitoring requirements. Use the `write-to` property to specify distinct output files for different sessions.

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
    command: pwsh -File ./Run-MonitorSession.ps1 -TestSuiteFile schedules/dummy.yaml -OutPath ./results/
    volumes:
      - ./results:/inventor/testbed/results

  testbed-network.ping:
    build: 
      context: ..
      dockerfile: Dockerfile
    working_dir: /inventor/testbed
    command: pwsh -File ./Run-MonitorSession.ps1 -TestSuiteFile schedules/network.ping.yaml -OutPath ./results/
    volumes:
      - ./results:/inventor/testbed/results
```

Both services use the same Docker image (built from the provided Dockerfile) and set the working directory to /inventor/testbed inside the container.
Each container runs the Run-MonitorSession.ps1 PowerShell script with its corresponding YAML configuration file, which defines the specific test session.
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
