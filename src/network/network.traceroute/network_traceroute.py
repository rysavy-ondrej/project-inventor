#
# Created as a part of the INVENTOR project (TAČR Trend No. FW10010040, 2024-2026).
# Author: Václav Korvas, xkorva03@stud.fit.vutbr.cz
# Institution: Brno University of Technology, Faculty of Information Technology, Czech Republic
# Date: 22/11/2024
#
from icmplib import traceroute, ICMPLibError
from multiprocessing import Queue
import json
import socket
import numpy as np

def load_config(file):
    """
    Load the json configuration file

    Parameters:
    - file (str): The path to the json configuration file

    Returns:
    - dict: The configuration file as a dictionary
    """
    try:
        with open(file, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        err_msg = error_json("INVALID CONFIGURATION", f'Error loading configuration file: {e}')
        return None

def error_json(code, message):
    """
    Create an error json message

    Parameters:
    - message (str): The error message

    Returns:
    - dict: The error message as a dictionary
    """
    data = {'status': 'error',
            'error': {'error_code' : code, 'description': message}}
    return data

def resolve_target(target):
    """
    Resolve the target to an IP address

    Parameters:
    - target (str): The target to resolve
    """
    try:
        addresses = socket.getaddrinfo(target, None)
        ip_addr = addresses[0][4][0]
        return ip_addr, None
    except Exception as e:
        error_msg = error_json("CAN'T RESOLVE", f'Error creating socket: {e}')
        return None, {'run_id': run_id, 'status': 'error', 'error': error_msg}

def process_hops(res):
    """
    Process the hops from the traceroute test

    Parameters:
    - res (list): The list of hops from the traceroute test
    """
    hops = []
    last_distance = 0
    for hop in res:
        if last_distance + 1 != hop.distance:
            hops.append({'hop_number': hop.distance, 'hop_ip': 'Some gateways are not responding'})
        else:
            hops.append({
                'hop_number': hop.distance,
                'hop_ip': hop.address,
                'hop_rtt': round(hop.rtts[0], 3)
            })
        last_distance = hop.distance
    return hops

def calculate_path_stability(paths, target_reached):
    """
    Calculate the path stability of the traceroute test

    Parameters:
    - paths (list): The list of paths
    """
    max_length = max(len(path) for path in paths) if paths else 0
    for path in paths:
        while len(path) < max_length:
            path.append(None)
    variability = np.var([len(set(path)) for path in paths])
    max_variability = max_length - 1 if max_length > 1 else 1
    stability = 1 - (variability / max_variability)
    if not target_reached:
        stability = "Target not reached"
    return stability

def traceroute_test(run_id, target, ttl_max, packet_size, count, interval, timeout, repeats):
    """
    Perform a traceroute test to a target

    Parameters:
    - run_id (int): The id of the test
    - target (str): The target to ping
    - ttl_max (int): The maximum TTL
    - packet_size (int): The size of the sended packet
    - count (int): The number of packets to send to each hop
    - interval (float): The interval between packets
    - timeout (int): The timeout for each packet
    - repeats (int): The number of times to repeat the tracerout test

    Returns:
    - dict: The results of the traceroute test
    """

    # Initialization
    address, error_data = resolve_target(target)
    if not address:
        return error_data

    run_details = []
    packet_sent, packet_received = 0, 0
    min_hops, max_hops = float('inf'), float('-inf')
    paths = []
    target_reached = False
    gateways_issue_detected = False

    for run_cnt in range(1, repeats + 1):
        try:
            res = traceroute(target, count=count, interval=interval, timeout=timeout, max_hops=ttl_max, payload_size=packet_size)
            packet_sent += res[0].packets_sent
            packet_received += res[0].packets_received
            paths.append([hop.address for hop in res])

            # Check if the destination was reached
            if res and res[-1].address == address:
                target_reached = True

            # Update hop details and min/max hops
            hops = process_hops(res)
            # Check if the last hop contains "Some gateways are not responding"
            if hops and hops[-1]['hop_ip'] == 'Some gateways are not responding':
                target_reached = True 

            run_details.append({'run': run_cnt, 'hops': hops})
            if res:
                min_hops = min(min_hops, res[-1].distance)
                max_hops = max(max_hops, res[-1].distance) 
        except ICMPLibError as e:
            run_details.append({'run': run_cnt, 'hops': [str(e)]})

    # Calculate path stability
    path_stability = calculate_path_stability(paths, target_reached or gateways_issue_detected)
    # Final results
    packet_loss = round((1 - packet_received / packet_sent) * 100, 2) if packet_sent > 0 else 0
    data = {
        'run_id': run_id,
        'status': 'completed',
        'summary': {
            'IP_address': address,
            'min_hops': min_hops,
            'max_hops': max_hops,
            'path_stability': path_stability,
            'packet_loss': packet_loss
        },
        'details': run_details
    }

    return data

def run(params : dict, run_id : int ,queue : Queue = None) -> dict:
    """
    Run the traceroute test

    Parameters:
    - params (dict): The configuration parameters
    - run_id (int): The id of the test
    - queue (Queue): The queue to send the results

    Returns:
    - dict: The results of the traceroute test
    """
    result = {}
    if params is not None:
        try:
            result = traceroute_test(run_id, target=params['target_host'],ttl_max=params['ttl_max'],
                                packet_size=params['packet_size'], count=1,
                                interval=0.05, timeout=params['timeout'],
                                repeats=params['repeats'])
            
        except Exception as e:
            result = error_json("ERROR", f'Error running traceroute test: {e}. Please check if you have the necessary permissions.')

    else:
        result = error_json("INVALID CONFIGURATION", "Invalid configuration file")

    if queue is not None:
        queue.put(result)

    return result

if __name__ == "__main__":
    config = load_config("test/input.json")
    res = run(config, 1)
    print(json.dumps(res, indent=4))
