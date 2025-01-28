#
# Created as a part of the INVENTOR project (TAČR Trend No. FW10010040, 2024-2026).
# Author: Dias Assatulla, xassat00@stud.fit.vutbr.cz
# Institution: Brno University of Technology, Faculty of Information Technology, Czech Republic
# Date: 22/11/2024
#

#!/usr/bin/env python3
from multiprocessing import Queue
from icmplib import  is_hostname
from socket import gethostbyname
import json
import paho.mqtt.client as mqtt
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

def measure_response_time(start_time):
    """
    Function that calculates time between response with service

    Parametrs:
    -   start_time (time.time()): Initial time, with which the final time will be calculated afterwards

    Returns:
    -   time.time(): Final time in seconds
    """
    return round(time.time() - start_time,3)

def create_client(target_host,topic_names,probe) -> mqtt:
    def on_message(client, userdata, msg):
        probe[msg.topic] = str(msg.payload)

    def on_subscribe(client, userdata, mid, reason_code_list, properties):
        probe['reason_code_list'] = str(reason_code_list)
            
    def on_connect(client, userdata, flags, rc, properties):
        probe['is_connected'] = client.is_connected()
        
        if rc == 0: # Which means, it's connected
            probe['connected_time'] = datetime.fromtimestamp((time.time()),timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")    
            for topic in topic_names.split(','):
                client.subscribe(topic)
            
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    response_start = time.time()
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_subscribe = on_subscribe

    client.connect(target_host)

    if is_hostname(target_host):
        probe['IP_address'] = client.socket().getpeername()[0]

    probe['response_time'] = measure_response_time(response_start)
    return client

def collect_info(target_host,topic_names) -> dict:
    """
    Collects the information about the service by connecting to it.

    Parameters:
    -   target_host (string): hostname to connect with.
    -   probe (dict): the final results, where it will be stored.

    Return:
    -   dict: updated results, that will be output.json
    """

    probe = {}
    probe['target_host'] = target_host
    connection_start_time = time.time()
    topic_set = set(topic_names.split(','))


    client = create_client(target_host,topic_names, probe)
    client.loop_start()
    timer = time.time()
    while True:
        if topic_set.issubset(probe.keys()): # If all topics are subscribed, then
            break
        # If it is more than 15 seconds, then break the loop
        if measure_response_time(timer) > 15:
            break
        

    client.loop_stop()
    client.disconnect()

    probe['duration'] = measure_response_time(connection_start_time)

    return probe

def run(params : dict, run_id, queue : Queue = None) -> dict:
    result = {}
    if params is not None:
        try:
            if ',' in params['target_host'] or ' ' in params['target_host']:
                raise Exception("Only one target is allowed!")
            
            result = collect_info(params['target_host'],params['topic_names'])
        except Exception as e:
            result = error_json("CONFIG FILE ERROR", f'{e}')
    else:
        result = error_json("CONFIG FILE ERROR", "Parametrs not specified")

    if queue:
            queue.put(result)

    return result