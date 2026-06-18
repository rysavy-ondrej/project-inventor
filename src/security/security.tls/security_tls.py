#
# Created as a part of the INVENTOR project (TAČR Trend No. FW10010040, 2024-2026).
# Author: Václav Korvas, xkorva03@stud.fit.vutbr.cz
# Institution: Brno University of Technology, Faculty of Information Technology, Czech Republic
# Date: 22/11/2024
#
import json
from multiprocessing import Queue
import socket
import ipaddress
from OpenSSL import SSL
from OpenSSL import crypto
from OpenSSL._util import lib as _ssl_lib
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


def explain_ssl_error(raw_text):
    """
    Map a raw OpenSSL/pyOpenSSL error string to a human-readable explanation.

    The handshake errors surfaced by OpenSSL (e.g. "sslv3 alert handshake
    failure") are accurate but terse; this adds the most likely cause so the
    result is actionable without having to interpret the raw alert.

    Parameters:
    - raw_text (str): The raw error string (str(exception)).

    Returns:
    - str | None: A plain-language explanation, or None if no specific
      interpretation is known.
    """
    text = raw_text.lower()
    # Most-specific substrings first; the raw OpenSSL text is preserved by the
    # caller, so these only need to add the likely cause.
    hints = [
        ('handshake failure',
         'The server rejected the handshake because no parameters were shared. '
         'Commonly the offered cipher_suites do not match the server certificate '
         'key type (e.g. an ECDHE-RSA cipher against an ECDSA-only server), or '
         'none of the offered cipher_suites/elliptic_curves are accepted.'),
        ('protocol version',
         'The server does not support the requested tls_version. The host may '
         'only offer a different version (e.g. TLS 1.2); try another tls_version.'),
        ('unexpected eof',
         'The server closed the connection during the handshake without sending '
         'a TLS alert. This is often caused by a missing/incorrect SNI (the target '
         'requires Server Name Indication) or an edge/CDN dropping unrecognized '
         'ClientHellos.'),
        ('internal error',
         'The server reported an internal error during the handshake. This is '
         'often caused by a missing/incorrect SNI so the edge/CDN cannot select a '
         'backend or certificate for the requested host.'),
        ('no protocols available',
         'The requested tls_version is disabled in the local OpenSSL build '
         '(e.g. TLS 1.0/1.1 are no longer enabled). Use a newer tls_version.'),
        ('wrong version number',
         'The server did not speak TLS on this port (a non-TLS response was '
         'received). Check target_port.'),
        ('unknown ca',
         'The server presented a certificate chain from an unknown CA.'),
        ('certificate expired',
         'The server certificate has expired.'),
        ('bad certificate',
         'The server rejected the client certificate.'),
        ('decode error',
         'The server could not decode the ClientHello (a malformed extension or '
         'field). Check the configured extensions/elliptic_curves.'),
        ('ciphersuite',
         'One or more of the configured cipher_suites is invalid for this '
         'tls_version. Note TLS 1.3 uses its own cipher suite names '
         '(e.g. TLS_AES_256_GCM_SHA384).'),
    ]
    for needle, hint in hints:
        if needle in text:
            return hint
    return None


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

def is_ip_address(value):
    """
    Check whether a string is a literal IPv4 or IPv6 address.

    Used to decide whether a target can be sent as SNI: SNI must be a hostname,
    never an IP literal.

    Parameters:
    - value (str): The host string to test.

    Returns:
    - bool: True if value is an IP address literal, False otherwise.
    """
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False

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

    # Absent string fields are null (consistent with subject_cn/issuer_cn above,
    # which are None when the component is missing), not an "N/A" placeholder.
    if subject_components.get('O') is None:
        subject_on = None
    else:
        subject_on = subject_components.get('O').replace('\xa0', ' ')

    if issuer_components.get('O') is None:
        issuer_on = None
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
        # X.509 serial numbers are identifiers (up to 160 bits), not quantities,
        # and routinely exceed UINT64. Emit as a decimal string so downstream
        # consumers with 64-bit integer columns cannot overflow.
        'serial_number': str(cert.get_serial_number()),
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

    # Scalar string fields are null when the extension is absent (not "N/A").
    key_usage = None
    extended_key_usage = None
    # authority_info_access is a repeated (array) field; default to an empty list
    # so the type stays an array even when the cert has no such extension.
    autorityInfoAccess = []

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

    # Set the cipher suites. TLS 1.3 ciphersuites use a separate OpenSSL API
    # (SSL_CTX_set_ciphersuites); set_cipher_list only affects TLS 1.2 and
    # below. pyOpenSSL does not wrap the TLS 1.3 setter, so call it via FFI.
    if cipher_suites:
        joined = b':'.join(cipher.encode('utf-8') for cipher in cipher_suites)
        if tls_version == 'TLSv1.3':
            if _ssl_lib.SSL_CTX_set_ciphersuites(context._context, joined) != 1:
                raise SSL.Error(f'Invalid TLS 1.3 ciphersuite(s): {cipher_suites}')
        else:
            context.set_cipher_list(joined)

    # Set the elliptic curves
    if elliptic_curves is not None and len(elliptic_curves) > 0:
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

        # Determine the SNI to send. An explicit 'sni' extension always wins;
        # otherwise default to the target hostname, which is what ordinary TLS
        # clients do and what most CDN/virtual-hosted servers require to route
        # the handshake and select a certificate. SNI must be a hostname, so it
        # is skipped when the target is a literal IP address.
        sni_host = None
        if extensions:
            for ext in extensions:
                if ext['type'] == 'sni':
                    sni_host = ext['data']
        if sni_host is None and not is_ip_address(hostname_or_ip):
            sni_host = hostname_or_ip
        if sni_host:
            ssl_conn.set_tlsext_host_name(sni_host.encode('utf-8'))

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
        # Null (not "N/A") when no value applies: no curve requested, or the
        # server returned no SNI / negotiated no ALPN protocol.
        res['elliptic_curve'] = elliptic_curves[0] if elliptic_curves else None
        res['SNIs'] = ssl_conn.get_servername().decode('utf-8') if ssl_conn.get_servername() else None
        res['alpn'] = ssl_conn.get_alpn_proto_negotiated().decode('utf-8') if ssl_conn.get_alpn_proto_negotiated() else None
        res['client_extension_count'] = 0
        res['server_extension_count'] = 0
        # These are repeated (array) fields; initialize to empty lists, not a
        # string placeholder, so the type stays an array if enhance_tls_info
        # (the packet-capture pass) does not run or finds no handshake packets.
        res['client_extension_names'] = []
        res['server_extension_names'] = []
        res['addition_server_cert_info'] = extract_extensions(cert)
        res['server_cert_chain'] = [extract_cert_data(cert) for cert in cert_chain]
        res['server_cert'] = extract_cert_data(cert)

        # Clean up
        ssl_conn.shutdown()
        ssl_conn.close()
        sock.close()

    except SSL.Error as e:
        # Enrich the terse OpenSSL message with a likely cause when one can be
        # inferred, while preserving the original text for diagnosis.
        raw = str(e)
        hint = explain_ssl_error(raw)
        description = f'{hint} (raw error: {raw})' if hint else raw
        res['status'] = 'error'
        res['error'] = {'error_msg': 'SSL Error', 'description': description}

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
        # Guard the msgtype access with hasattr: encrypted TLS 1.2 Finished
        # records (content type 22) cannot be dissected by scapy, so they arrive
        # as raw content with no 'msgtype' field. Reading it unguarded raised
        # AttributeError('msgtype'), which aborted otherwise-successful handshakes.
        elif hasattr(msg, 'msgtype') and (msg.msgtype == 20 or msg.msgtype == 4) and check_tuple(packet, target):
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
            # Reset the shared capture buffer so this run only analyzes its own
            # handshake packets. The list is a module global appended to by the
            # sniffer thread; without this reset a long-lived session would carry
            # packets (and encrypted messages) from earlier runs into this one,
            # corrupting extension counts/timings and re-triggering parse errors.
            global handshake_packets
            handshake_packets = []

            target_host = params.get('target_host', None)
            if target_host is None:
                raise ValueError("Target host is not specified in the configuration file")
            target_port = params.get('target_port', None)
            if target_port is None:
                raise ValueError("Target port is not specified in the configuration file")
            tls_version = params.get('tls_version', None)
            if tls_version is None:
                raise ValueError("TLS version is not specified in the configuration file")
            cipher_suites = params.get('cipher_suites', None)
            if cipher_suites is None:
                raise ValueError("Cipher suites are not specified in the configuration file")
            elliptic_curves = params.get('elliptic_curves', [])
            extensions = params.get('extensions', [])
            timeout = params.get('timeout', None)
            if timeout is None:
                raise ValueError("Timeout is not specified in the configuration file")

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
