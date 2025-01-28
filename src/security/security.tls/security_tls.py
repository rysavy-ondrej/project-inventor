#
# Created as a part of the INVENTOR project (TAČR Trend No. FW10010040, 2024-2026).
# Author: Václav Korvas, xkorva03@stud.fit.vutbr.cz
# Institution: Brno University of Technology, Faculty of Information Technology, Czech Republic
# Date: 22/11/2024
#
import json
from multiprocessing import Queue
import socket
from OpenSSL import SSL
from OpenSSL import crypto
import time
from datetime import datetime
import scapy.all as scapy
from scapy.layers.tls.all import TLS, TLSClientHello, TLSServerHello
from scapy.layers.inet import TCP, IP
import threading

handshake_packets = [] # List to store the handshake packets
stop_sniffing = threading.Event() # Event to stop sniffing

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
    - dict: The error dict message
    """
    data = {'status': 'error',
            'error': {'error_code' : code, 'description': message}}
    return data

def handle_exception(e, msg):
    """
    Handle exceptions

    Parameters:
    - e (Exception): The exception object
    - msg (str): The error message

    Returns:
    - dict: The exception data
    """

    return {'error_msg': f'{msg}', 'description': f'{str(e)}'}


def ip_to_hostname(ip):
    """
    Convert an IP address to a hostname

    Parameters:
    - ip (str): The IP address

    Returns:
    - str: The hostname
    """
    try:
        hostname, _, _ = socket.gethostbyaddr(ip)
        return hostname
    except Exception as e:
        return ip

def hostname_to_ip(hostname):
    """
    Convert a hostname to an IP address

    Parameters:
    - hostname (str): The hostname

    Returns:
    - str: The IP address
    """
    try:
        ip = socket.gethostbyname(hostname)
        return ip
    except Exception as e:
        return hostname

def extract_cert_data(cert):
    """
    Extract certificate data

    Parameters:
    - cert (X509): The certificate object

    Returns:
    - dict: The certificate data
    """

    # Extract components of the subject and issuer distinguished names
    subject_components = [(key.decode('utf-8'), value.decode('utf-8')) for key, value in cert.get_subject().get_components()]
    issuer_components = [(key.decode('utf-8'), value.decode('utf-8')) for key, value in cert.get_issuer().get_components()]

    # Convert timestamps to human-readable format
    not_before = cert.get_notBefore().decode('ascii').rstrip('Z')
    not_after = cert.get_notAfter().decode('ascii').rstrip('Z')

    not_before = datetime.strptime(not_before, '%Y%m%d%H%M%S').strftime('%Y-%m-%d %H:%M:%S')
    not_after = datetime.strptime(not_after, '%Y%m%d%H%M%S').strftime('%Y-%m-%d %H:%M:%S')

    # Extract signature algorithm and convert it to a human-readable format
    signature_algorithm = cert.get_signature_algorithm().decode('utf-8')

    # Calculate the number of bits in the public key
    public_key_bits = cert.get_pubkey().bits()

    # Convert the SHA-256 fingerprint to a human-readable string
    fingerprint = cert.digest('sha256').decode('utf-8')

    subject_components = dict(subject_components)
    issuer_components = dict(issuer_components)

    subject_cn = subject_components.get('CN')
    issuer_cn = issuer_components.get('CN')

    if subject_components.get('O') is None:
        subject_on = 'N/A'
    else:
        subject_on = subject_components.get('O').replace('\xa0', ' ')

    if issuer_components.get('O') is None:
        issuer_on = 'N/A'
    else:
        issuer_on = issuer_components.get('O').replace('\xa0', ' ')

    subject_country = subject_components.get('C')
    issuer_country = issuer_components.get('C')

    # Create a dictionary with human-readable data
    data = {
        'subject_cn': subject_cn,
        'subject_on': subject_on,
        'subject_country': subject_country,
        'issuer_cn': issuer_cn,
        'issuer_on': issuer_on,
        'issuer_country': issuer_country,
        'not_before': not_before,
        'not_after': not_after,
        'serial_number': cert.get_serial_number(),
        'version': cert.get_version() + 1,  # Certificates are 0-indexed, but typically presented as 1-indexed
        'signature_algorithm': signature_algorithm,
        'public_key_length': public_key_bits,
        'fingerprint': fingerprint
    }

    return data

def extract_extensions(cert):
    """
    Extract certificate extensions

    Parameters:
    - cert (X509): The certificate object

    Returns:
    - dict: The certificate extensions
    """

    key_usage = 'N/A'
    extended_key_usage = 'N/A'
    autorityInfoAccess = 'N/A'

    for i in range(cert.get_extension_count()):
        ext = cert.get_extension(i)
        ext_name = ext.get_short_name().decode('utf-8')
        ext_data = str(ext)
        if ext_name == 'keyUsage':
            key_usage = ext_data
        elif ext_name == 'extendedKeyUsage':
            extended_key_usage = ext_data
        elif ext_name == 'authorityInfoAccess':
            autorityInfoAccess = [ext_data for ext_data in ext_data.split('\n')]

    data = {
        'key_usage': key_usage,
        'extended_key_usage': extended_key_usage,
        'authority_info_access': autorityInfoAccess,
    }

    return data

def create_ssl_context(tls_version, cipher_suites, elliptic_curves, extensions):
    """
    Create an SSL context

    Parameters:
    - tls_version (str): The TLS version to use
    - cipher_suites (list): The cipher suites to use
    - elliptic_curves (list): The elliptic curves to use
    - extensions (list): The extensions to use

    Returns:
    - SSLContext: The SSL context
    """

    # Maping the TLS version to the OpenSSL constant
    tls_versions = {
        'TLSv1.0': SSL.TLS1_VERSION,
        'TLSv1.1': SSL.TLS1_1_VERSION,
        'TLSv1.2': SSL.TLS1_2_VERSION,
        'TLSv1.3': SSL.TLS1_3_VERSION
    }

    context = SSL.Context(SSL.TLS_CLIENT_METHOD)

    context.set_max_proto_version(tls_versions[tls_version])
    context.set_min_proto_version(tls_versions[tls_version])

    # Set the cipher suites
    if cipher_suites and not tls_version == 'TLSv1.3':
        context.set_cipher_list(b':'.join(cipher.encode('utf-8') for cipher in cipher_suites))

    # Set the elliptic curves
    if elliptic_curves:
        ell_curve = crypto.get_elliptic_curve(elliptic_curves[0])
        context.set_tmp_ecdh(ell_curve)

    # Set the extensions
    if extensions:
        for ext in extensions:
            # Set the alpn extension (where the type is 'alpn' and the data is the protocol name and it's a array)
            if ext['type'] == 'alpn':
                context.set_alpn_protos([proto.encode('utf-8') for proto in ext['data']])

    return context

def perform_tls_handshake(run_id, hostname_or_ip, port, tls_version, cipher_suites, elliptic_curves, extensions, timeout):
    """
    Perform a TLS handshake

    Parameters:
    - hostname (str): The target host
    - port (int): The target port
    - tls_version (str): The TLS version to use
    - cipher_suites (list): The cipher suites to use
    - elliptic_curves (list): The elliptic curves to use
    - extensions (list): The extensions to use
    - timeout (int): The timeout for the connection

    Returns:
    - dict: The TLS handshake data
    """

    res = {
        'run_id': run_id
    }
    try:

        # Create an SSL context
        context = create_ssl_context(tls_version, cipher_suites, elliptic_curves, extensions)

        # Convert the hostname to an IP address
        target = hostname_to_ip(hostname_or_ip)

        # Create a socket and connect to the server
        if ':' in target:
            sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        else:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        sock.connect((target, port))
        sock.settimeout(timeout)

        # Wrap the socket with SSL
        ssl_conn = SSL.Connection(context, sock)
        ssl_conn.setblocking(1)

        if extensions:
            for ext in extensions:
                if ext['type'] == 'sni':
                    ssl_conn.set_tlsext_host_name(ext['data'].encode('utf-8'))

        # Initiate the SSL handshake
        ssl_conn.set_connect_state()
        start_time = time.time()
        ssl_conn.do_handshake()
        end_time = time.time()

        cert = ssl_conn.get_peer_certificate()

        cert_chain = ssl_conn.get_peer_cert_chain()

        duration = (end_time - start_time) * 1000

        res['status'] = 'completed'
        res['handshake_time'] = int(duration)
        res['IP_address'] = target 
        res['target_port'] = port
        res['tls_version'] = ssl_conn.get_protocol_version_name()
        res['cipher_suite'] = ssl_conn.get_cipher_name()
        res['elliptic_curve'] = elliptic_curves[0]
        res['SNIs'] = ssl_conn.get_servername().decode('utf-8') if ssl_conn.get_servername() else 'N/A'
        res['alpn'] = ssl_conn.get_alpn_proto_negotiated().decode('utf-8') if ssl_conn.get_alpn_proto_negotiated() else 'N/A'
        res['client_extension_count'] = 0
        res['server_extension_count'] = 0
        res['client_extension_names'] = "N/A"
        res['server_extension_names'] = "N/A"
        res['addition_server_cert_info'] = extract_extensions(cert)
        res['server_cert_chain'] = [extract_cert_data(cert) for cert in cert_chain]
        res['server_cert'] = extract_cert_data(cert)

        # Clean up
        ssl_conn.shutdown()
        ssl_conn.close()
        sock.close()

    except SSL.Error as e:
        data = handle_exception(e, 'SSL Error')
        res['status'] = 'error'
        res['error'] = data

    except Exception as e:
        data = handle_exception(e, 'Error establishing connection')
        res['status'] = 'error'
        res['error'] = data

    return res

def check_tuple(packet, target):
    """
    Check if the packet is from the target e.g src, dst ip and port match

    Parameters:
    - packet (TLS): The TLS packet
    - target (dict): The target info

    Returns:
    - bool: True if the packet is from the target, False otherwise  
    """

    if packet.haslayer(TCP):
        tcp = packet[TCP]
        if tcp.sport in [target['src_p'], target['dst_p']] and tcp.dport in [target['src_p'], target['dst_p']] \
            and packet[IP].src in [target['src_ip'], target['dst_ip']] and packet[IP].dst in [target['src_ip'], target['dst_ip']]: 
            return True
    return False

def check_destination(packet, target_host, target_port):
    """
    Check if the packet is from the target e.g dst ip and port match

    Parameters:
    - packet (TLS): The TLS packet
    - target_host (str): The target host
    - target_port (int): The target port

    Returns:
    - bool: True if the packet is from the target, False otherwise  
    """

    if packet.haslayer(TCP):
        tcp = packet[TCP]
        if tcp.dport == target_port and packet[IP].dst == target_host:
            return True
    return False


def sniff(target_host, target_port, timeout=5):
    """
    Sniff the network for handshake packets

    Parameters:
    - target_host (str): The target host
    - target_port (int): The target port
    - timeout (int): The timeout for the sniffing
    """

    scapy.sniff(store=False, prn=process_packet, filter=f"tcp port {target_port} and host {target_host}", timeout=timeout)

def process_packet(packet):
    """
    Process a packet and extract the handshake packets

    Parameters:
    - packet (TLS): The TLS packet
    """
    global handshake_packets
    if packet.haslayer(TCP) and packet.haslayer(TLS):
        tls_layers = packet[TLS]
        if tls_layers and tls_layers.msg:
            for msg in tls_layers.msg:
                if tls_layers.type == 22:
                    handshake_packets.append({
                        'msg' : msg,
                        'packet' : packet
                    })

def enhance_tls_info(tls_info, handshake_packets):
    """
    Enhance the TLS info with the info from handshake packets

    Parameters:
    - tls_info (dict): The TLS info
    - handshake_packets (list): The handshake packets

    Returns:
    - dict: The enhanced TLS info
    """
    start_time = 0
    end_time = 0
    client_extensions = []
    server_extensions = []
    target = {
        'dst_ip' : tls_info['IP_address'],
        'dst_p' : tls_info['target_port'],
        'src_ip' : 'N/A',
        'src_p' : 'N/A'
    }
    for packet_dict in handshake_packets:
        msg = packet_dict['msg']
        packet = packet_dict['packet']
        if check_destination(packet, target['dst_ip'], target['dst_p']) and isinstance(msg, TLSClientHello):
            start_time = packet.time
            target['src_ip'] = packet[IP].src
            target['src_p'] = packet[TCP].sport
            for ext in msg.ext:
                client_extensions.append(ext.name)
        elif (msg.msgtype == 20 or msg.msgtype == 4) and check_tuple(packet, target):
            end_time = packet.time
        elif isinstance(msg, TLSServerHello) and check_tuple(packet, target):
            for ext in msg.ext:
                server_extensions.append(ext.name)
            
    duration = (end_time - start_time) * 1000
    tls_info['client_extension_count'] = len(client_extensions)
    tls_info['server_extension_count'] = len(server_extensions)
    tls_info['client_extension_names'] = client_extensions
    tls_info['server_extension_names'] = server_extensions
    tls_info['handshake_time'] = int(duration) if duration > 0 else tls_info['handshake_time']

    return tls_info

def run(params : dict, run_id : int, queue : Queue = None) -> dict:
    if params:
        try:
            target_host = params['target_host']
            target_port = params['target_port']
            tls_version = params['tls_version']
            cipher_suites = params['cipher_suites']
            elliptic_curves = params['elliptic_curves']
            extensions = params['extensions']
            timeout = params['timeout']

            capture_thread = threading.Thread(target=sniff, args=(target_host, target_port, timeout))
            capture_thread.start()

            tls_info = perform_tls_handshake(run_id, target_host, target_port, tls_version,
                                        cipher_suites, elliptic_curves, extensions, timeout)

            capture_thread.join()
            if (tls_info['status'] == 'error'):
                res = tls_info
            else:
                res = enhance_tls_info(tls_info, handshake_packets)

        except Exception as e:
            res = error_json("TLS_TEST_ERROR", f'Error running TLS test: {e}')

    else:
        res = error_json("INVALID_CONFIGURATION", "Invalid configuration file")

    if queue is not None:
        queue.put(res)

    return res

if __name__ == '__main__':
    config = load_config('test/input.json')
    if config is not None:
        res = run(config, 1)
        print(json.dumps(res, indent=4))
    else:
        print('Error loading configuration file')
