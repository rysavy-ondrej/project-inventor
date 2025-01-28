# Created as a part of the INVENTOR project (TAČR Trend No. FW10010040, 2024-2026).
# Author: Nelson Makau Mutua, imutua@fit.vutbr.cz
# Institution: Brno University of Technology, Faculty of Information Technology, Czech Republic
# Date: 01/12/2024
import subprocess
import json

def start_iperf_server(config):
    """
    Starts an iperf3 server listening on a specified IP and port.

    Parameters:
    config (dict): Configuration with the following keys:
        - "host" (str): IP address to bind the server to (default: '0.0.0.0')
        - "port" (int): Port number to listen on (default: 5201)
        - "log_file" (str): File to save the server log output (optional)
    """
    host = config.get("host", "0.0.0.0")
    port = str(config.get("port", 5201))
    log_file = config.get("log_file", "iperf_server_log.json")

    iperf_command = ["iperf3", "-s", "-B", host, "-p", port, "-J"]  # -J for JSON output

    print(f"Starting iperf3 server on {host}:{port}")
    
    try:
        with subprocess.Popen(iperf_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as proc:
            print(f"iperf3 server is running. Listening for connections on {host}:{port}")
            try:
                for line in proc.stdout:
                    print(line, end='')  # Print server output in real-time
                    
                    # Optionally, save each line of JSON data to log file
                    with open(log_file, "a") as logfile:
                        logfile.write(line)
                        
            except KeyboardInterrupt:
                print("\nShutting down iperf3 server...")
                proc.terminate()
                proc.wait()
                
    except Exception as e:
        print(f"Error starting iperf3 server: {e}")

if __name__ == "__main__":
    # Load configuration from a JSON file or prompt user input
    config = {
        "host": input("Enter the IP address to bind the server (or default 0.0.0.0):") or "0.0.0.0",
        "port": int(input("Enter the Port to bind the server:") or "5201"),
        "log_file": "iperf_server_log.json"
    }

    start_iperf_server(config)
