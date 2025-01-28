#
# Created as a part of the INVENTOR project (TAČR Trend No. FW10010040, 2024-2026).
# Author: Dias Assatulla, xassat00@stud.fit.vutbr.cz
# Institution: Brno University of Technology, Faculty of Information Technology, Czech Republic
# Date: 22/11/2024
#

#!/usr/bin/env python3
from multiprocessing import Queue
from icmplib import is_hostname
import json
import time
import ftplib
from socket import gethostbyname
from datetime import datetime, timezone

FTP_port = 21

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
    start_time = time.time()
    
    try:      
        server = ftplib.FTP_TLS(target_host, timeout=5)
        response_time_start = time.time()
        if is_hostname(target_host):
            probe['IP_address'] = server.sock.getpeername()[0]

        probe['connected_time'] = datetime.fromtimestamp((time.time()),timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        probe['welcome_op'] = server.getwelcome()

        try:
            probe['login_op'] = server.login() # Login anonymously
            probe['protect_op'] = server.prot_p() # Data protection to private
            probe['retrlines_op'] = server.retrlines('LIST')
        except Exception as e:
            probe['login_op'] = f"Failed: {e}"

        probe['response_time'] = str(f"{measure_response_time(response_time_start)}s")
        probe['quit_op'] = server.quit()
        probe['duration'] = str(f"{measure_response_time(start_time)}s")
    except Exception as e:
        probe['retcode'] = f"ERROR:"
        probe['errmsg'] = f"{e}"

    return probe

def run(params : dict, run_id, queue : Queue = None) -> dict:
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
