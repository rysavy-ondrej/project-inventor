# Created as a part of the INVENTOR project (TAČR Trend No. FW10010040, 2024-2026).
# Author: Nelson Makau Mutua, imutua@fit.vutbr.cz
# Institution: Brno University of Technology, Faculty of Information Technology, Czech Republic
# Date: 01/12/2024

import subprocess
import time
import json
import os

def run_iperf(config):
    """Runs iperf3 with given parameters from JSON config and saves output to JSON file."""
    host = config.get("host")
    port = str(config.get("port", 5201))
    protocol = config.get("protocol", "tcp").lower()
    duration = config.get("duration", 10)
    reverse = config.get("reverse", False)
    output_file = config.get("output_file", "iperf_results.json")

    iperf_command = ["iperf3", "-c", host, "-p", port, "-t", str(duration), "-J"]  # Enable JSON output

    if protocol == "udp":
        iperf_command.append("-u")
    if reverse:
        iperf_command.append("-R")

    print(f"Running iperf3 to {host}:{port} using {protocol.upper()} protocol for {duration} seconds")

    # Record the time for TTFB calculation
    start_time = time.time()

    try:
        # Execute iperf3 and capture output
        result = subprocess.run(iperf_command, capture_output=True, text=True, timeout=duration + 5)

        # Calculate the TTFB
        ttfb = time.time() - start_time
        print(f"Time to First Byte (approx): {ttfb:.3f} seconds")

        # Parse the JSON output
        iperf_data = json.loads(result.stdout)

        # Add additional data to JSON
        iperf_data.update({
            "host": host,
            "port": port,
            "protocol": protocol,
            "duration": duration,
            "reverse": reverse,
            "ttfb": round(ttfb, 3),
        })

        # Save results to JSON file
        with open(output_file, "w") as outfile:
            json.dump(iperf_data, outfile, indent=4)

        print(f"Results saved to {output_file}")

    except subprocess.TimeoutExpired:
        print("Error: iperf3 timed out")
    except json.JSONDecodeError:
        print("Error: Failed to parse iperf3 JSON output.")
        print("Raw Output:\n", result.stdout)
    except Exception as e:
        print(f"Error running iperf3: {e}")

if __name__ == "__main__":
    # Load configuration from JSON file
    config_file = input("Enter the path to the configuration JSON file: ")

    try:
        with open(config_file, "r") as file:
            config = json.load(file)

        # Run the iperf test with the loaded config
        run_iperf(config)

    except FileNotFoundError:
        print("Error: Configuration file not found.")
    except json.JSONDecodeError:
        print("Error: Failed to parse JSON configuration.")
