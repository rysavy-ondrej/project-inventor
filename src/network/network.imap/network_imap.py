#
# Created as a part of the INVENTOR project (TAČR Trend No. FW10010040, 2024-2026).
# Author: Dias Assatulla, xassat00@stud.fit.vutbr.cz
# Institution: Brno University of Technology, Faculty of Information Technology, Czech Republic
# Date: 22/11/2024
#

#!/usr/bin/env python3

from icmplib import is_hostname, resolve
import nmap 
import time
import imaplib 
from socket import gethostbyname
from datetime import datetime, timezone
from multiprocessing import Queue

IMAP_SSL_PORT = 993

def error_json(code, message):
    """
    Create an error json message

    Parameters:
    -   message (str): The error message

    Returns:
    -   str: The error message as a json
    """
    data = {'status': 'error', 
            'error': {'error_code' : code, 'description': message}}
    return data

def collect_info(target_host, port) -> dict:
    """
    Collects the information about the service by connecting to it.

    Parameters:
    -   target_host (string): hostname to connect with.
    -   port (int): which port use to connect.

    Return:
    -   probe (dict): the final results, where it will be stored.
    """
    probe = {}
    probe['target_host'] = target_host
    probe['target_port'] = port
    start_time = time.time()
    try:
        if int(port) == IMAP_SSL_PORT:
            server = imaplib.IMAP4_SSL(target_host,timeout=5)
        else:
            server = imaplib.IMAP4(target_host, port=port,timeout=5)
            server.starttls()

        if is_hostname(target_host):
            probe['IP_address'] = server.sock.getpeername()[0]
            
        probe['protocol_version'] = server.PROTOCOL_VERSION
        probe['connected_time'] = datetime.fromtimestamp((time.time()),timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        
        response_time_start = time.time()
        result = server.noop()
        probe['noop_op'] = {'status_code':str(result[0]), 'status_msg':str(result[1])}
        probe['response_time'] = str(f"{measure_response_time(response_time_start)}s")    
        result = server.capability()
        probe['server_msg'] = str(result)
        
        probe['duration'] = str(f"{measure_response_time(start_time)}s")
    except Exception as e:
        probe['retcode'] = f"ERROR: can't connect to target."
        probe['errcode'] = f"{e}"

    return probe

def measure_response_time(start_time):
    """
    Function that calculates time between response with service

    Parametrs:
    -   start_time (time.time()): Initial time, with which the final time will be calculated afterwards

    Returns:
    -   time.time(): Final time in seconds
    """
    return round(time.time() - start_time,3)
    
def login_check(target_server, login_username, probe) -> dict:
    """
    Tries to login to the server

    Parameters:
    -   target_server (string): hostname to connect with.
    -   login_username (string): username credential.
    -   probe (dict): the final results, where it will be stored.

    Return:
    -   dict: updated results, that will be output.json
    """
    import getpass
    try:
        server = imaplib.IMAP4_SSL(target_server)
        result = server.login(login_username,getpass.getpass(f"Enter password for {login_username}: "))
        
        probe['login_server'] = {
            'target':str(target_server),
            'login_op':str(result)
        }
        result = server.logout()
        probe['login_server']['logout_op'] = str(result)
    except Exception as e:
       probe['login_server'] = {
           'target':str(target_server),
            'login_op':f"ERROR! {e}"
        }

    return probe

def run(params : dict, run_id : int, queue : Queue = None) -> dict:

    result = {}
    
    if params is not None:
        try:
            if ',' in params['target_host'] or ' ' in params['target_host']:
                raise Exception("Only one target is allowed!")
            if ',' in params['target_port'] or ' ' in params['target_port']:
                raise Exception("Only one port is allowed!")
            
            result = collect_info(params['target_host'],params['target_port'])
            
            if params['login_flag'] == "True":
                login_check(params['login_server'], params['login_username'], result)

        except Exception as e:
            result = error_json("CONFIG FILE ERROR", f'{e}')

        if queue:
            queue.put(result)
    else:
        result = error_json("CONFIG FILE ERROR", "Parametrs not specified")

    return result