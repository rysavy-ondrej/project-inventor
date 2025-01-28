#
# Created as a part of the INVENTOR project (TAČR Trend No. FW10010040, 2024-2026).
# Author: Dias Assatulla, xassat00@stud.fit.vutbr.cz
# Institution: Brno University of Technology, Faculty of Information Technology, Czech Republic
# Date: 22/11/2024
#

#!/usr/bin/env python3

import smtplib 
import time
import json
from icmplib import is_hostname
from socket import gethostbyname
from datetime import datetime, timezone
from multiprocessing import Queue
# For sending email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import getpass

SMTP_TLS_PORT = 465
SMTP_PORT = 587

def load_config(file):
    """
    Load the json configuration file

    Parameters:
    -   file (str):  The path to the json configuration file

    Returns:
    -   dict: The configuration file as a dictionary
    """
    try: 
        with open(file, 'r') as f:
            config = json.load(f)
            return config
    except Exception as e:
        err_msg = error_json("INVALID CONFIGURATION", f'Error loading configuration file: {e}')
        print(err_msg)
        return None

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

def run(params : dict, run_id : int, queue : Queue = None) -> dict:
    result = {}
    if params is not None:
        try:
            if ',' in params['target_host'] or ' ' in params['target_host']:
                raise Exception("Only one target is allowed!")
            if ',' in params['target_port'] or ' ' in params['target_port']:
                raise Exception("Only one port is allowed!")
            
            result = collect_info(params['target_host'],params['target_port'])
            
            if params['send_email_flag'] == "True":
                send_email(result, params['target_host'])

        except Exception as e:
            result = error_json("CONFIG FILE ERROR", f'{e}')

        if queue:
            queue.put(result)
    else:
        result = error_json("CONFIG FILE ERROR", "Parametrs not specified")

    return result

def get_size_from_list(list_features):
    """
    From the list of features in get_features() function gets SIZE field.

    Parametrs:
    -   list_features (list of array): list of features that support server

    Returns:
    -   str: returns SIZE that can handle server in MB.
    """
    import re

    for item in list_features:
        match = re.match(r'^SIZE (\d+)$', item)
        if match:
            size_number = match.group(1)
            return f"{(int(size_number) / (1024 * 1024))} MB"
    return "UNKNOWN"

def get_features(server, probe):
    """
    Sends EHLO (Extended Hello) command to SMTP server, 
    to get the list of features that supports

    Parametrs:
    -   target_host (str): Target host that will be port scanned
    -   port (str): port on which will be checked connection
    -   probe (dict): to get the result of the operation

    Returns:
    -   dict: probe for data dictionary
    """
    # Get supported features
    responce_code, server_msg = server.ehlo()

    # Get the greeting message
    probe['server_msg'] = str(str(responce_code) + "-" + server_msg.decode('utf-8').split('\n')[0])

    server_msg_lines = server_msg.decode('utf-8').split('\n')

    # To skip the part, where it shows your IP or smth, I used [1:]
    probe['ehlo_op'] = {'status_code':str(responce_code),
                              'status_msg':str(server_msg_lines[1:]),
                              'SIZE':get_size_from_list(server_msg_lines[1:])}
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

def collect_info(target_host, port) -> dict:
    """
    Sends NOOP (No Operation) command to SMTP server, 
    to check if the connection to the SMTP server is still active

    Parametrs:
    -   target_host (str): Target host that will be port scanned
    -   port (str): port on which will be checked connection
    

    Returns:
    -   probe (dict): the result of function
    """
    probe = {}
    probe['target_host'] = target_host
    probe['target_port'] = port
    start_time = time.time()

    try:
        if int(port) == SMTP_TLS_PORT:
            server = smtplib.SMTP_SSL(target_host,timeout=5)    
        else:
            server = smtplib.SMTP(target_host,port=port,timeout=5)
            # Start TLS session for security reasons
            server.starttls()

        if is_hostname(target_host):
            probe['IP_address'] = server.sock.getpeername()[0]

        probe['connected_time'] = datetime.fromtimestamp((time.time()),timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        get_features(server, probe)
        response_time_start = time.time()
        result = server.noop()
        probe['noop_op'] = {'status_code':str(result[0]), 'status_msg':str(result[1])}
        probe['response_time'] = str(f"{measure_response_time(response_time_start)}s")
        
        result = server.quit()
        probe['quit_op'] = {'status_code':str(result[0]), 'status_msg':str(result[1])}
                
        probe['duration'] = str(f"{measure_response_time(start_time)}s")

    except Exception as e:
        probe['retcode'] = f"ERROR: on port {port} can't connect."
        probe['errcode'] = f"{e}"

    return probe

def send_email(probe, target_server):

    # Get user input
    sender_email = input("Enter your email: ")
    receiver_email = input("Enter receiver of your email: ")

    # Create dummy data
    subject = 'Test Email'
    body = 'This is a test email sent using Python.'

    # Set up the email message
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    # Connect to SMTP server. 
    with smtplib.SMTP(target_server,SMTP_PORT) as server:
        try:   
            # TLS connection
            server.starttls()
            # Log in to the SMTP server 
            server.login(input("Enter username: "), getpass.getpass(prompt="Enter your email password: "))
            
            # Send email
            server.sendmail(sender_email, receiver_email, message.as_string())
            probe['sendmail_op'] = f"Succesfully sent email from {target_server} to {receiver_email}"
        except Exception as e:
            print("Failed to send email:", e)
            probe['sendmail_op'] = f"Failed to send email from {target_server}. Error: {e}"
