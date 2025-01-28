#
# Created as a part of the INVENTOR project (TAČR Trend No. FW10010040, 2024-2026).
# Author: Václav Korvas, xkorva03@stud.fit.vutbr.cz
# Institution: Brno University of Technology, Faculty of Information Technology, Czech Republic
# Date: 22/11/2024
#
import json
import time
import dns.resolver
import dns.dnssec
import dns.rdatatype
import dns.reversename
import dns.rcode as rcode
from multiprocessing import Queue
from datetime import datetime, timezone

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

def handle_exception(domain, response_code, resolution_time, e):
    """
    Handle exceptions

    Parameters:
    - domain (str): The domain that caused the exception
    - response_code (str): The response code to use
    - resolution_time (int): The time it took to resolve the domain

    Returns:
    - dict: The exception data
    """
    exception_data = {
        'target_host': str(domain),
        'IP_address': [],
        'expiration_time': 'N/A',
        'response_time': convert_to_mili_seconds(resolution_time),
        'status': 'failed',
        'status_code': response_code,
        'error_message' : str(e),
    }

    return exception_data

def get_cname(answer):
    """
    Get the CNAME from the answer

    Parameters:
    - answer (dns.resolver.Answer): The answer to get the CNAME from

    Returns:
    - str: The CNAME
    """
    cname = []
    for data in answer:
        if data.rdtype == dns.rdatatype.CNAME:
            cname.append(data.to_text())

    return cname

def get_ns(answer):
    """
    Get the NS from the answer

    Parameters:
    - answer (dns.resolver.Answer): The answer to get the NS from

    Returns:
    - str: The NS
    """
    ns = []
    for data in answer:
        if data.rdtype == dns.rdatatype.NS:
            ns.append(data.to_text())

    return ns

def get_soa(answer):
    """
    Get the SOA (Start of Authority) record from the answer.

    Parameters:
    - answer (dns.resolver.Answer): The answer to get the SOA from

    Returns:
    - dict: The SOA information, containing:
        - 'mname': The primary name server for the domain.
        - 'rname': The responsible authority's mailbox (email address).
        - 'serial': The serial number for the zone.
        - 'refresh': The time interval (in seconds) before the zone should be refreshed.
        - 'retry': The time interval (in seconds) before a failed refresh should be retried.
        - 'expire': The upper limit (in seconds) before the zone is considered no longer authoritative.
        - 'minimum': The minimum TTL (in seconds) for records in the zone.
    """
    soa_record = answer.rrset[0]
    soa_info = {
        'mname': soa_record.mname.to_text(),    # Primary name server
        'rname': soa_record.rname.to_text(),    # Responsible authority's mailbox
        'serial': str(soa_record.serial),       # Serial number
        'refresh': str(soa_record.refresh),     # Refresh interval
        'retry': str(soa_record.retry),         # Retry interval
        'expire': str(soa_record.expire),       # Expiration limit
        'minimum': str(soa_record.minimum),     # Minimum TTL
    }

    return soa_info

def check_ds(answer):
    """
    Check if the answer has a DS (Delegation Signer) record.

    Parameters:
    - answer (dns.resolver.Answer): The answer to check

    Returns:
    - list of dicts: The DS information, each containing:
        - 'key_tag': The key tag value identifying the DNSKEY record.
        - 'algorithm': The algorithm used by the DS record, in human-readable form.
        - 'digest_type': The digest type used by the DS record.
        - 'digest': The digest value, in hexadecimal form.
    """
    ds_info = []
    if answer.rrset is None:
        return ds_info
    for data in answer.rrset:
        if data.rdtype == dns.rdatatype.DS:
            ds_info.append({
                'key_tag': str(data.key_tag),
                'algorithm': dns.dnssec.algorithm_to_text(data.algorithm),
                'digest_type': str(data.digest_type),
                'digest': data.digest.hex(),
            })

    return ds_info 

def get_caa(answer):
    """
    Get the CAA (Certification Authority Authorization) records from the answer.

    Parameters:
    - answer (dns.resolver.Answer): The answer to get the CAA records from.

    Returns:
    - list of dicts: The CAA information, each containing:
        - 'flags': The flags byte of the CAA record as a string.
        - 'tag': The property tag of the CAA record as a string.
        - 'value': The property value of the CAA record as a string.
    """
    caa_info = []
    if answer.rrset is None:
        return caa_info
    for record in answer:
        if record.rdtype == dns.rdatatype.CAA:
            caa_info.append({
                'flags': str(record.flags),
                'tag': record.tag.decode('utf-8') if isinstance(record.tag, bytes) else record.tag,
                'value': record.value.decode('utf-8') if isinstance(record.value, bytes) else record.value
            })

    return caa_info

def get_dnskey(answer):
    """
    Get the DNSKEY (DNS Key) records from the answer.

    Parameters:
    - answer (dns.resolver.Answer): The answer to get the DNSKEY records from.

    Returns:
    - list of dicts: The DNSKEY information, each containing:
        - 'flags': The flags field of the DNSKEY record as a string.
        - 'protocol': The protocol field of the DNSKEY record as a string.
        - 'algorithm': The algorithm used by the DNSKEY record, in human-readable form.
        - 'key': The public key associated with the DNSKEY record, as a string.
    """
    dnskey_info = []
    if answer.rrset is None:
        return dnskey_info
    for record in answer.rrset:
        if record.rdtype == dns.rdatatype.DNSKEY:
            dnskey_info.append({
                'flags': str(record.flags),
                'protocol': str(record.protocol),
                'algorithm': dns.dnssec.algorithm_to_text(record.algorithm),
                'key': record.key.to_text() if isinstance(record.key, dns.rdata.Rdata) else record.key.hex(),
            })

    return dnskey_info

def get_rrsig(answer):
    """
    Get the RRSIG (Resource Record Signature) records from the answer.

    Parameters:
    - answer (dns.resolver.Answer): The answer to get the RRSIG records from.

    Returns:
    - list of dicts: The RRSIG information, each containing:
        - 'type_covered': The type of resource record covered by the signature, as a string.
        - 'algorithm': The algorithm used by the RRSIG record, in human-readable form.
        - 'labels': The number of labels in the original RRSIG owner name, as a string.
        - 'original_ttl': The original TTL of the covered resource record, as a string.
        - 'signature_expiration': The expiration time of the signature, as a string.
        - 'signature_inception': The inception time of the signature, as a string.
        - 'key_tag': The key tag of the DNSKEY record that generated the signature, as a string.
        - 'signer_name': The domain name of the signer of the RRSIG record, as a string.
        - 'signature': The signature value, represented in hexadecimal format.
    """
    rrsig_info = []
    if answer.rrset is None:
        return rrsig_info

    for record in answer.rrset:
        if record.rdtype == dns.rdatatype.RRSIG:
            rrsig_info.append({
                'type_covered': dns.rdatatype.to_text(record.type_covered),
                'algorithm': dns.dnssec.algorithm_to_text(record.algorithm),
                'labels': str(record.labels),
                'original_ttl': str(record.original_ttl),
                'signature_expiration': str(record.signature_expiration),
                'signature_inception': str(record.signature_inception),
                'key_tag': str(record.key_tag),
                'signer_name': record.signer_name.to_text() if isinstance(record.signer_name, dns.name.Name) else record.signer_name,
                'signature': record.signature.hex(),
            })

    return rrsig_info

def convert_time(expiration_time):
    """
    Convert the expiration time to a human readable format

    Parameters:
    - expiration_time (int): The expiration time

    Returns:
    - str: The human readable expiration time in seconds
    """
    return int(expiration_time - datetime.now(timezone.utc).timestamp())

def convert_to_mili_seconds(time):
    """
    Convert the time to miliseconds

    Parameters:
    - time (int): The time to convert

    Returns:
    - int: The time in miliseconds
    """
    return round(time * 1000, 4) 

def dns_resolve(query_domains, query_type, run_id, nameservers=None):
    """
    Test the DNS resolution of the given domains

    Parameters:
    - query_domains (list): The list of domains to query
    - query_type (str): The query type to use
    - run_id (int): The run id
    - nameservers (list): The list of nameservers to use, if None use the default configuration of the resolver

    Returns:
    - dict: The results of the DNS resolution
    """

    res = {}
    details_list = []
    test_cnt = 0
    failed_cnt = 0
    avg_resolution_time = 0
    max_resolution_time = 0
    min_resolution_time = 0

    # Initialize the resolver
    resolver = dns.resolver.Resolver()
    if nameservers is not None:
        resolver.nameservers = nameservers
    else:
        nameservers = resolver.nameservers

    for domain in query_domains:
        detail = {}
        try:
            start_time = time.time()

            qname = dns.reversename.from_address(domain) if query_type == 'PTR' else domain

            answers = resolver.resolve(qname, query_type)

            if query_type != 'PTR':
                detail['target_host'] = answers.qname.to_text()

            if query_type == 'A' or query_type == 'AAAA':
                detail['IP_address'] = [answer.to_text() for answer in answers]
            elif query_type == 'PTR':
                detail['domain_names'] = [ans.to_text() for ans in answers]
            else:
                detail['IP_address'] = []
                
            detail['expiration_time'] = convert_time(answers.expiration) 
            detail['response_time'] = convert_to_mili_seconds(answers.response.time) 
            detail['status'] = 'success'
            detail['status_code'] = rcode.to_text(answers.response.rcode())
            detail['nameservers_used'] = nameservers
            detail['ds'] = check_ds(answers) if query_type == 'DS' else 'N/A'
            detail['cname'] = get_cname(answers) if query_type == 'CNAME' else 'N/A'
            detail['ns'] = get_ns(answers) if query_type == 'NS' else 'N/A'
            detail['soa'] = get_soa(answers) if query_type == 'SOA' else 'N/A'
            detail['caa'] = get_caa(answers) if query_type == 'CAA' else 'N/A'
            detail['dnskey'] = get_dnskey(answers) if query_type == 'DNSKEY' else 'N/A'
            detail['rrsig'] = get_rrsig(answers) if query_type == 'RRSIG' else 'N/A'

        except dns.resolver.NXDOMAIN as e:
            detail = handle_exception(domain, 'NXDOMAIN', time.time() - start_time, e)
            failed_cnt += 1

        except dns.resolver.NoAnswer as e:
            detail = handle_exception(domain, 'NOANSWER', time.time() - start_time, e)
            failed_cnt += 1

        except dns.resolver.NoNameservers as e:
            detail = handle_exception(domain, 'NONAMESERVERS', time.time() - start_time, e)
            failed_cnt += 1

        except dns.resolver.NoRootSOA as e:
            detail = handle_exception(domain, 'NOROOTSOA', time.time() - start_time, e)
            failed_cnt += 1

        except dns.resolver.NotAbsolute as e:
            detail = handle_exception(domain, 'NOTABSOLUTE', time.time() - start_time, e)
            failed_cnt += 1

        except dns.exception.Timeout as e:
            detail = handle_exception(domain, "TIMEOUT", time.time() - start_time, e)
            failed_cnt += 1

        except dns.exception.DNSException as e:
            detail = handle_exception(domain, 'DNSException', time.time() - start_time, e)
            failed_cnt += 1

        except Exception as e:
            detail = handle_exception(domain, 'UNKNOWN', time.time() - start_time, e)
            failed_cnt += 1

        details_list.append(detail)
        test_cnt += 1

    # Filter out details without a valid 'response_time'
    valid_response_times = [detail['response_time'] for detail in details_list if 'response_time' in detail and detail['response_time'] is not None]

    # Check if there are valid response times before calculating
    if valid_response_times:
        avg_resolution_time = round(sum(valid_response_times) / len(valid_response_times), 4)
        max_resolution_time = round(max(valid_response_times), 4)
        min_resolution_time = round(min(valid_response_times), 4)
    else:
        avg_resolution_time = max_resolution_time = min_resolution_time = 0 

    res['run_id'] = run_id 
    res['status'] = 'completed'
    res['summary'] = {
        'total_tests': test_cnt,
        'successful_tests': test_cnt - failed_cnt,
        'failed_tests': failed_cnt,
        'response_time_avg': avg_resolution_time, 
        'response_time_min': min_resolution_time,
        'response_time_max': max_resolution_time,
        'resolution_type': query_type,
    }
    res['details'] = details_list 

    return res

def run(params : dict, run_id : int ,queue : Queue = None) -> dict:

    if params is not None:
        #try:
        domains = params['target_hosts']
        query_type = params['query_type'].upper()
        nameservers = params.get('nameservers', None)

        if query_type not in ['A', 'AAAA', 'CNAME', 'NS', 'SOA', 'DS', 'CAA', 'DNSKEY', 'RRSIG', 'PTR']:
            res = error_json("INVALID_QUERY_TYPE", "Invalid query type")
        else:
            res = dns_resolve(domains, query_type, run_id, nameservers)

        #except Exception as e:
            #res = error_json("DNS_TEST_ERROR", f'Error running DNS test: {e}') 

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
