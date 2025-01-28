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
import time
import easysnmp

SNMP_PORT = 161

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


def collect_info(target_host, com_string, oid) -> dict:
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
        if is_hostname(target_host):
            target_host_ip = socket.getaddrinfo(target_host, SNMP_PORT)[0][4][0]
            probe['IP_address'] = target_host_ip

        session = easysnmp.Session(hostname=target_host,version=2,community=com_string)
        start_time = time.time()
        cleaned_oid = ",".join([item.strip() for item in oid.split(",")]) # To get rid off "oid1,oid2, oid3     "
        
        for object in cleaned_oid.split(','):
            response = session.get(object)
            probe[object] = {
                'get_value':str(response.value),
                'snmp_data_type':str(response.snmp_type)
            }
            
        probe['response_time'] = measure_response_time(start_time)
    except Exception as e: 
        probe = error_json("ERROR: something went wrong during testing", f'{e}')


    return probe

def run(params : dict, run_id : int, queue : Queue = None) -> dict:
    result = {}
    if params is not None:
        try:
            if ',' in params['target_host'] or ' ' in params['target_host']:
                raise Exception("Only one target is allowed!")

            if ',' in params['community_string'] or ' ' in params['community_string']:
                raise Exception("Only one community string is allowed!")
            
            if not params['oids'] or params['oids'] == ',':
                raise Exception("At least one OID must be defined!")
            
            if ' ' in params['oids']: 
                raise Exception("No whitespaces allowed in `oids` parametrs!")

            result = collect_info(params['target_host'],params['community_string'],params['oids'])
        except Exception as e:
            result = error_json("CONFIG FILE ERROR", f'{e}')
    else:
        result = error_json("CONFIG FILE ERROR", "Parametrs not specified")

    if queue:
        queue.put(result)

    return result
