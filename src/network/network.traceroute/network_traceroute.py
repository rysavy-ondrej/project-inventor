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
    try:
        with open(file, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        return None

def error_json(code, message):
    data = {'status': 'error',
            'error': {'error_code': code, 'description': message}}
    return data

def resolve_target(target, run_id):
    # Fix: run_id added as parameter (was referenced but not in scope)
    try:
        addresses = socket.getaddrinfo(target, None)
        ip_addr = addresses[0][4][0]
        return ip_addr, None
    except Exception as e:
        error_msg = error_json("CAN'T RESOLVE", f'Error resolving target: {e}')
        return None, {'run_id': run_id, 'status': 'error', 'error': error_msg}

def process_hops(res):
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

def calculate_path_stability(paths):
    # path_stability is a numeric field (double in [0, 1]). Return None when it
    # cannot be computed (no paths / zero-length paths) rather than a string
    # placeholder, so the JSON type stays numeric-or-null. Whether the target was
    # reached is reported separately via the 'target_reached' field.
    # Fix: guard empty paths to avoid np.var([]) returning NaN (breaks JSON)
    if not paths:
        return None
    max_length = max(len(path) for path in paths)
    if max_length == 0:
        return None
    for path in paths:
        while len(path) < max_length:
            path.append(None)
    variability = np.var([len(set(filter(None, path))) for path in paths])
    max_variability = max_length - 1 if max_length > 1 else 1
    stability = round(float(1 - (variability / max_variability)), 4)
    return stability

def traceroute_test(run_id, target, ttl_max, packet_size, count, interval, timeout, repeats):
    address, error_data = resolve_target(target, run_id)
    if not address:
        return error_data

    run_details = []
    packet_sent, packet_received = 0, 0
    # Fix: use None instead of float('inf')/float('-inf') — those crash json.dumps
    min_hops, max_hops = None, None
    paths = []
    target_reached = False

    for run_cnt in range(1, repeats + 1):
        try:
            res = traceroute(target, count=count, interval=interval, timeout=timeout,
                             max_hops=ttl_max, payload_size=packet_size)
            # Fix: aggregate across all hops, not just first hop
            packet_sent += sum(hop.packets_sent for hop in res)
            packet_received += sum(hop.packets_received for hop in res)
            paths.append([hop.address for hop in res])

            if res and res[-1].address == address:
                target_reached = True

            hops = process_hops(res)
            # Fix: removed false target_reached=True for missing gateways —
            # intermediate hops not responding does NOT mean the target was reached

            run_details.append({'run': run_cnt, 'hops': hops})
            if res:
                distance = res[-1].distance
                min_hops = distance if min_hops is None else min(min_hops, distance)
                max_hops = distance if max_hops is None else max(max_hops, distance)
        except ICMPLibError as e:
            run_details.append({'run': run_cnt, 'hops': [str(e)]})

    path_stability = calculate_path_stability(paths)
    packet_loss = round((1 - packet_received / packet_sent) * 100, 2) if packet_sent > 0 else 0
    data = {
        'run_id': run_id,
        'status': 'completed',
        'summary': {
            'IP_address': address,
            'min_hops': min_hops,
            'max_hops': max_hops,
            'path_stability': path_stability,
            'target_reached': target_reached,
            'packet_loss': packet_loss
        },
        'details': run_details
    }

    return data

def run(params: dict, run_id: int, queue: Queue = None) -> dict:
    result = {}
    if params is not None:
        try:
            result = traceroute_test(
                run_id,
                target=params['target_host'],
                ttl_max=params['ttl_max'],
                packet_size=params['packet_size'],
                count=1,
                interval=0.05,
                timeout=params['timeout'],
                repeats=params['repeats']
            )
        except Exception as e:
            result = error_json("ERROR", f'Error running traceroute test: {e}. '
                                         'Please check if you have the necessary permissions.')
    else:
        result = error_json("INVALID CONFIGURATION", "Invalid configuration file")

    if queue is not None:
        queue.put(result)

    return result

if __name__ == "__main__":
    config = load_config("test/input.json")
    res = run(config, 1)
    print(json.dumps(res, indent=4))
