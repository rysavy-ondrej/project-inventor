#
# Created as a part of the INVENTOR project (TAČR Trend No. FW10010040, 2024-2026).
# Author: Dias Assatulla, xassat00@stud.fit.vutbr.cz
# Institution: Brno University of Technology, Faculty of Information Technology, Czech Republic
# Date: 22/11/2024
#

#!/usr/bin/env python3
from multiprocessing import Queue
from icmplib import is_hostname
import socket
import ldap3
from datetime import datetime, timezone
import time

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


def measure_response_time(start_time):
    """
    Function that calculates time between response with service

    Parametrs:
    -   start_time (time.time()): Initial time, with which the final time will be calculated afterwards

    Returns:
    -   time.time(): Final time in seconds
    """
    return round(time.time() - start_time,3)

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

    try:
        # Initialize server object
        server = ldap3.Server(target_host, get_info=ldap3.ALL)
        if is_hostname(target_host):
            probe['IP_address'] = server.address_info[0][4][0] # Get the IP address
        
        # Try to connect with anonymous bind
        connection = ldap3.Connection(server)
        connection_time = time.time()

        if not connection.bind(): # Try to bind
            raise Exception(connection.result['description']) # Connection failed, end monitoring
        else:
            probe['connected_time'] = datetime.fromtimestamp((time.time()),timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            start_time = time.time()
            
            # Connection successful, collect information by sending simple query
            connection.search(
                search_base='',
                search_filter='(uid=*test*)',
                search_scope=ldap3.SUBTREE,
                attributes=['cn']
            )
            probe['response_time'] = measure_response_time(start_time)
            # This query will show empty list, but the case is to verify the connection
            probe['search_query'] = [str(entry) for entry in connection.entries] 
        
            # In the end unbind the connection
            connection.unbind()

            probe['duration'] = measure_response_time(connection_time)

    except Exception as e: 
        probe = error_json("ERROR: something went wrong during testing", f'{e}')


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
    else:
        result = error_json("CONFIG FILE ERROR", "Parametrs not specified")

    if queue:
        queue.put(result)

    return result
