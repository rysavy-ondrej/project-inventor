#
# Created as a part of the INVENTOR project (TAČR Trend No. FW10010040, 2024-2026).
# Author: Dias Assatulla, xassat00@stud.fit.vutbr.cz
# Institution: Brno University of Technology, Faculty of Information Technology, Czech Republic
# Date: 22/11/2024
#

#!/usr/bin/env python3
from multiprocessing import Queue
from icmplib import is_ipv6_address, is_hostname
import socket
import ntplib
import time
from datetime import datetime, timezone

def error_json(code, message):
    """
    Create an error json message

    Parameters:
    - message (str): The error message

    Returns:
    - str: The error message as a json
    """
    data = {'status': 'error', 
            'error': {'error_code' : code, 'description': message}}
    return data

# This is exact same class like in ntplib. The only diff is that in function request it also return destination address
class NTPClient:
    """NTP client session."""

    def __init__(self):
        """Constructor."""
        pass

    def request(self, host, version=2, port='ntp', timeout=5):
        """Query a NTP server.

        Parameters:
        host    -- server name/address
        version -- NTP version to use
        port    -- server port
        timeout -- timeout on socket operations

        Returns:
        NTPStats object
        """
        # lookup server address
        addrinfo = socket.getaddrinfo(host, port)[0]
        family, sockaddr = addrinfo[0], addrinfo[4]

        # create the socket
        s = socket.socket(family, socket.SOCK_DGRAM)

        try:
            s.settimeout(timeout)

            # create the request packet - mode 3 is client
            query_packet = ntplib.NTPPacket(mode=3, version=version,
                                tx_timestamp=ntplib.system_to_ntp_time(time.time()))

            # send the request
            s.sendto(query_packet.to_data(), sockaddr)

            # wait for the response - check the source address
            src_addr = None,
            while src_addr[0] != sockaddr[0]:
                response_packet, src_addr = s.recvfrom(256)

            # build the destination timestamp
            dest_timestamp = ntplib.system_to_ntp_time(time.time())
        except socket.timeout:
            raise ntplib.NTPException("No response received from %s." % host)
        finally:
            s.close()

        # construct corresponding statistics
        stats = ntplib.NTPStats()
        stats.from_data(response_packet)
        stats.dest_timestamp = dest_timestamp

        return stats, sockaddr[0]

def collect_info(target_host) -> dict:
    """
    Collects the information about the service by connecting to it.

    Parameters:
    -   target_host (string): hostname to connect with.

    Return:
    -   probe (dict): the final results, where it will be stored.
    """
    probe = {}
    probe['target_host'] = target_host
    client = NTPClient() # Create client
    try:
        response, addr = client.request(target_host, version=3) # Creates ntplib.NTPStats object by connecting to the server
        if is_hostname(target_host):
            probe['IP_address'] = addr
        probe['connected_time'] = datetime.fromtimestamp((time.time()),timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        probe['delay'] = str(response.delay)  
        probe['offset'] = str(response.offset) 
        probe['leap_indicator'] = ntplib.leap_to_text(response.leap)
        probe['stratum'] = str(response.stratum) 
        # check if stratum is 1
        if response.stratum == 1:
            # Convert ref id to hex string
            hex_id = hex(response.ref_id)

            # decode hex to string
            probe['refid'] = ''.join(chr(int(hex_id[i:i+2], 16)) for i in range(2, len(hex_id), 2))
        else:
            probe['refid'] = str(ntplib.ref_id_to_text(response.ref_id))
        
        probe['root_delay'] = str(response.root_delay) 
        probe['root_dispersion'] = str(response.root_dispersion) 
        probe['precision'] = str(response.precision)  
        probe['tx_time'] = datetime.fromtimestamp((response.tx_time),timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ") 
        probe['recv_time'] = datetime.fromtimestamp((response.recv_time),timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ") 
        probe['dest_time'] = datetime.fromtimestamp((response.dest_time),timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ") 
    
    except Exception as e:
        probe['retcode'] = f"ERROR: Can not connect to target the target."
        probe['errcode'] = f"{e}"

    return probe

def run(params : dict, run_id : int, queue : Queue = None) -> dict:
    result = {}
    if params is not None:
        try:
            if ',' in params['target_host'] or ' ' in params['target_host']:
                raise Exception("Only one target is allowed!")
            
            result = collect_info(params['target_host'])
        except Exception as e:
            result = error_json("CONFIG FILE ERROR", f'{e}')

        if queue:
            queue.put(result)
    else:
        result = error_json("CONFIG FILE ERROR", "Parametrs not specified")

    return result
