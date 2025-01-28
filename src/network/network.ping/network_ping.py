#
# Created as a part of the INVENTOR project (TAČR Trend No. FW10010040, 2024-2026).
# Author: Václav Korvas, xkorva03@stud.fit.vutbr.cz
# Institution: Brno University of Technology, Faculty of Information Technology, Czech Republic
# Date: 22/11/2024
#
from icmplib import *
import time
import json
from statistics import stdev
from datetime import datetime, timezone
from multiprocessing import Queue
import socket

# Global variables
code_map = {
    0: "Echo Reply",
    3: "Destination Unreachable",
    4: "Source Quench",
    5: "Redirect Message",
    8: "Echo Request",
    9: "Router Advertisement",
    10: "Router Solicitation",
    11: "Time Exceeded",
    12: "Parameter Problem",
    13: "Timestamp Request",
    14: "Timestamp Reply",
    15: "Information Request",
    16: "Information Reply",
    17: "Address Mask Request",
    18: "Address Mask Reply",
    30: "Traceroute",
    31: "Datagram Conversion Error",
    32: "Mobile Host Redirect",
    42: "Extended Echo Request",
    43: "Extended Echo Reply"
}

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

def jitter(rtts):
    """
    Calculate the jitter of a list of RTTs

    Parameters:
    - rtts (list): The list of RTTs

    Returns:
    - float: The jitter
    """
    sum_deltas = 0.0
    num_deltas = len(rtts) - 1

    if num_deltas < 1:
        return 0.0

    for i in range(num_deltas):
        sum_deltas += abs(rtts[i] - rtts[i + 1])

    return round(sum_deltas / num_deltas, 3)

def error_json(code, message):
    """
    Create an error json message

    Parameters:
    - message (str): The error message

    Returns:
    - str: The error message as a json
    """
    data = {'status': 'error', 'error': {'code': code, 'message': message}} 
    return data

def simple_ping(target_host, packet_size, packet_count, timeout, interpacket_delay, run_id):
    """
    Ping a host based on the configuration and return the results

    Parameters:
    - target_host (str): The target IP address
    - packet_size (int): The size of the packet
    - packet_count (int): The number of packets to send
    - timeout (int): The maximum waiting time for receiving a reply in seconds
    - interpacket_delay (int): The time to wait between sending each packet in seconds
    - run_id (int): Id of the run

    Returns:
    - dict: The result from ping
    """
    try:
        # Resolve the address family dynamically
        info = socket.getaddrinfo(target_host, None)
        
        # Check for IPv4 or IPv6 address family
        if any(i[0] == socket.AF_INET for i in info):
            sock = ICMPv4Socket()
        elif any(i[0] == socket.AF_INET6 for i in info):
            sock = ICMPv6Socket()
        else:
            raise Exception("No valid address family found for the target host")
    except Exception as e:
        err_msg = error_json("CAN'T CREATE SOCKET", f'Error creating socket: {e}')
        data = {'run_id': run_id, 'status': 'error', 'error': err_msg}
        return data    
        
    sent = 0
    received = 0
    data = {}
    probes = []

    for seq in range(packet_count):
        if seq < packet_count - 1:
            time.sleep(interpacket_delay)
        probe = {}

        # Create ICMP request
        request = ICMPRequest(destination=target_host, id=PID, sequence=seq, payload_size=packet_size)

        try:
            # Send the request
            sock.send(request=request)
            sent += 1
            reply = sock.receive(request, timeout)
            
            # Throw an exception if it is an ICMP error message
            if ((reply._type == 0 and isinstance(sock, ICMPv4Socket)) or 
                (reply._type == 129 and isinstance(sock, ICMPv6Socket))):
                received += 1 
            reply.raise_for_status() 
            
            # Fill the probe data
            probe['connected_time'] = datetime.fromtimestamp(request.time, timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            probe['response_time'] = datetime.fromtimestamp(reply.time, timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            probe['rtt'] = round(((reply.time - request.time) * 1000), 3)
            probe['bytes_received'] = reply.bytes_received
            probe['status_msg'] = code_map[reply.type] if reply.type in code_map else 'Unknown'
            probe['status_code'] = reply.type

        except DestinationUnreachable as e:
            probe['connected_time'] = datetime.fromtimestamp(request.time, timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            probe['response_time'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            probe['rtt'] = 0
            probe['bytes_received'] = reply._bytes_received
            probe['status_msg'] = str(e)
            probe['status_code'] = reply._type
        
        except TimeExceeded as e:
            probe['connected_time'] = datetime.fromtimestamp(request.time, timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            probe['response_time'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            probe['rtt'] = 0
            probe['bytes_received'] = 0
            probe['status_msg'] = str(e)
            probe['status_code'] = reply._type

        except ICMPLibError as e:
            probe['connected_time'] = datetime.fromtimestamp(request.time, timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            probe['response_time'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            probe['rtt'] = 0
            probe['bytes_received'] = 0
            probe['status_msg'] = str(e)
            probe['status_code'] = reply._type

        probes.append(probe)

    data['run_id'] = run_id
    data['status'] = 'completed'
    data['summary'] = {'IP_address': target_host,
                       'pkts_send': sent, 
                       'pkts_received': received, 
                       'pkts_lost': round((sent - received) / sent * 100, 2) if sent > 0 else 0,
                       'rtt_min': round(min(p['rtt'] if 'rtt' in p else 0 for p in probes), 3),
                       'rtt_max': round(max(p['rtt'] if 'rtt' in p else 0 for p in probes), 3),
                       'rtt_avg': round(sum(p['rtt'] if 'rtt' in p else 0 for p in probes) / len(probes), 3),
                       'rtt_stddev': round(stdev(p['rtt'] if 'rtt' in p else 0 for p in probes), 3) if len(probes) > 1 else 0,
                       'jitter': jitter([p['rtt'] if 'rtt' in p else 0 for p in probes])}
    data['details'] = probes

    return data

def run(params : dict, run_id : int, queue : Queue = None) -> dict:
    res = {}
    if params:
        try:
            target_host = params['target_host']
            packet_size = params['packet_size']
            packet_count = params['packet_count']
            timeout = params['timeout']
            interpacket_delay = params['interpacket_delay']
            res = simple_ping(target_host, packet_size, packet_count, timeout, interpacket_delay, run_id)

        except Exception as e:
            res = error_json("CONFIG FILE ERROR", f'Missing configuration parametr: {e}')

        if queue:
            queue.put(res)
    else:
        res = error_json("CONFIG FILE ERROR", "Parametrs not specified")

    return res

if __name__ == '__main__':
    config = load_config('test/input.json')
    if config:
        res = run(config, 1)
        print(json.dumps(res, indent=4))
    else:
        print("Error loading configuration file")
