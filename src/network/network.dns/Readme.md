# Network DNS Test

This test is designed to verify the functionality of DNS services by resolving specific DNS names or a list of predefined DNS entries. It performs DNS resolution using standard methods and collects its results. The test aims to provide an overview of the state of the DNS system and detailed results for the individual resolutions, helping in identifying potential issues or verifying the correct operation of DNS services.

## Requirements

| Library | Version   |
| ------- | --------- |
| dnspython | 2.5.0     |


## INPUT

```proto
message DnsResolveTestConfig {
  repeated string query_domains = 1; // List of domains to query
  string query_type = 2; // Type of DNS query (e.g., "A" for address records)
}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| query_domains | List[str] | A list of DNS names to be resolved during the test. |
| query_type | str | A query type, commonly, "A", "AAAA". |
| nameservers| List[str] | The list of nameservers to use, if None use the default configuration of the resolver |

## Output

The output of the test is divided into two main sections: summary information and detailed information.

```proto
// Message representing the overall test results
message DnsResolveTestResult {
  ID run_id = 1; // The unique identifier of the test run
  TestStatus status = 2; // The overall status of the tests 
  Summary summary = 3; // A nested message for the summary of the test results
  repeated Detail details = 4; // An array of detailed results for individual tests
}



// Summary information of all tests
message Summary {
  int32 total_tests = 1; // The total number of tests conducted
  int32 success_count = 2; // The number of tests that were successful
  int32 failure_count = 3; // The number of tests that failed
  int32 response_time_avg = 4; // The average resolution(response) time across all tests
  int32 response_time_min = 5; // The minimum resolution(response) time observed
  int32 response_time_max = 6; // The maximum resolution(response) time observed
  string resolution_type = 7; // The type of DNS query performed (e.g., "A", "AAAA")
}



// Detailed information about each test  if the status is "success"
message Detail {
  string target_host = 1; // The DNS name queried
  repeated string IP_address = 2; // A list of resolved IP addresses
  int32 expiration_time = 3;  // The number of seconds for which the DNS answer can be cached and is considered valid 
  int32 response_time = 4; // The time taken to resolve the DNS name
  string status = 5; // The status of the DNS resolution ("success")
  string status_code = 6; // The response code of the DNS query (e.g., "NOERROR", "NXDOMAIN")
  string nameservers_used = 7; // The nameservers used for the resolution
  DS_detail ds = 8; // The delegation signer of the DNS query (only has a value if the query type is "DS")
  string cname = 9; // The canonical name of the DNS query (only has a value if the query type is "CNAME")
  string ns = 10; // The name server of the DNS query (only has a value if the query type is "NS")
  SOA_detail soa = 11; // The start of authority of the DNS query (only has a value if the query type is "SOA")
  repeated CAA_detail caa = 12; // The certification authority authorization of the DNS query (only has a value if the query type is "CAA")
  repeated DNSKEY_detail dnskey = 13; // The DNS key of the DNS query (only has a value if the query type is "DNSKEY")
  repeated RRSING_detail rrsig = 14; // The resource record signature of the DNS query (only has a value if the query type is "RRSIG")

}

// Detailed information about each test if the status is "failure"
message Detail {
  string target_host = 1; // The DNS name queried
  repeated string IP_address = 2; // A list of resolved IP addresses
  int32 expiration_time = 3;  // The number of seconds for which the DNS answer can be cached and is considered valid 
  int32 response_time = 4; // The time taken to resolve the DNS name
  string status = 5; // The status of the DNS resolution ("failed")
  string status_code = 6; // The response code of the DNS query (e.g., "NOERROR", "NXDOMAIN")
  string error_message = 7; // The error message describing the failure

}

// Detailed information about the delegation signer (DS) of the DNS query
message DS_detail {
  string key_tag = 1; // The key tag value identifying the DNSKEY record
  string algorithm = 2; // The algorithm used for the key in human-readable form
  string digest_type = 3; // The digest type used by the DS record
  string digest = 4; // The digest value in hexadecimal format
}

// Detailed information about the start of authority (SOA) of the DNS query
message SOA_detail {
  string mname = 1; // The primary name server for the zone
  string rname = 2; // The email address of the responsible person for the zone
  int32 serial = 3; // The serial number of the zone
  int32 refresh = 4; // The time interval before the zone should be refreshed in seconds
  int32 retry = 5; // The time interval before a failed refresh should be retried in seconds
  int32 expire = 6; // The time interval that the zone is valid without refresh in seconds
  int32 minimum = 7; // The minimum TTL value for the zone in seconds
}

// Detailed information about the certification authority authorization (CAA) of the DNS query
message CAA_detail {
  string flags = 1; // The flags byte of the CAA record as a string
  string tag = 2; // The property tag of the CAA record as a string
  string value = 3; // The property value of the CAA record as a string
}

// Detailed information about the DNS key (DNSKEY) of the DNS query
message DNSKEY_detail {
  string flags = 1; // The flags field of the DNSKEY record as a string
  string protocol = 2; // The protocol field of the DNSKEY record as a string
  string algorithm = 3; // The algorithm used by the DNSKEY record, in human-readable form
  string public_key = 4; // The public key associated with the DNSKEY record as a string
}

// Detailed information about the resource record signature (RRSIG) of the DNS query
message RRSIG_detail {
  string type_covered = 1; // The type of resource record covered by the signature, such as 'A', 'AAAA', 'MX', etc., presented as a string. 
  string algorithm = 2; // The algorithm used by the RRSIG record, expressed in human-readable form (e.g., "RSA-SHA256"), as a string. 
  string labels = 3; // The number of labels in the original RRSIG owner name, presented as a string. 
  string original_ttl = 4; // The original TTL (Time to Live) value of the covered resource record, presented as a string. 
  string signature_expiration = 5; // The expiration time of the signature, presented as a string. 
  string signature_inception = 6; // The inception time of the signature, presented as a string. 
  string key_tag = 7; //  The key tag of the DNSKEY record that generated the signature, presented as a string. 
  string signer_name = 8; // The domain name of the signer of the RRSIG record, presented as a string. 
  string signature = 9; // The signature value itself, represented in hexadecimal format, as a string. 
}


```

### Summary Information

| Field | Type | Description |
|-------|------|-------------|
| total_tests | int | The total number of DNS resolutions attempted. |
| success_count | int | The number of successful DNS resolutions. |
| failure_count | int | The number of failed DNS resolutions. |
| response_time_avg | float | The average time taken for DNS resolutions, in milliseconds. |
| response_time_min | float | The minimum time taken for DNS resolutions, in milliseconds. |
| response_time_max | float | The maximum time taken for DNS resolutions, in milliseconds. |
| resolution_type     | string | The type of DNS query performed (e.g., "A", "AAAA") |

### Detailed Information

Each entry in the detailed information section will correspond to an individual DNS resolution attempt and include the following fields:

| Field | Type | Description |
|-------|------|-------------|
| target_host | str | The DNS name that was resolved. |
| IP_address | List[str] | The IP addresses returned, if any. |
| expiration_time | float | The number of seconds for which the DNS answer can be cached and is considered valid  |
| response_time | float | The time taken for the DNS resolution, in milliseconds. |
| status | str | The status of the DNS resolution. It can be either "success" or "failed". |
| status_code | str | A DNS response code string. It can be NOERROR, NXDOMAIN, SERVFAIL, ... |

For successful resolutions, the following additional fields are included:

| Field | Type | Description |
|-------|------|-------------|
| ds | DS_detail | The delegation signer of the DNS query. |
| cname | str | The canonical name of the DNS query. |
| ns | str | The name server of the DNS query. |
| soa | SOA_detail | The start of authority of the DNS query. |
| caa | List[CAA_detail] | The certification authority authorization of the DNS query. |
| dnskey | List[DNSKEY_detail] | The DNS key of the DNS query. |
| rrsig | List[RRSIG_detail] | The resource record signature of the DNS query. |

For failed resolutions, the following additional field is included:

| Field | Type | Description |
|-------|------|-------------|
| error_message | str | The error message describing the failure. |

## Run simple test

```bash
pytest monitor_dns.py
```

The result will be in the `test` directory in file `output.json`

## Examples

INPUT:

```json
{
  "target_hosts": ["example.com", "vutbr.cz"],
  "query_type" : "A",
  "nameservers": ["188.116.92.133"]
}
```

OUTPUT:

```json
{
    "run_id": 1,
    "status": "completed",
    "summary": {
        "total_tests": 2,
        "successful_tests": 2,
        "failed_tests": 0,
        "response_time_avg": 80.2747,
        "response_time_min": 74.0213,
        "response_time_max": 86.5281,
        "resolution_type": "A"
    },
    "details": [
        {
            "target_host": "example.com.",
            "IP_address": [
                "93.184.215.14"
            ],
            "expiration_time": 2999,
            "response_time": 74.0213,
            "status": "success",
            "status_code": "NOERROR",
            "nameservers_used": [
                "188.116.92.133"
            ],
            "ds": "N/A",
            "cname": "N/A",
            "ns": "N/A",
            "soa": "N/A",
            "caa": "N/A",
            "dnskey": "N/A",
            "rrsig": "N/A"
        },
        {
            "target_host": "vutbr.cz.",
            "IP_address": [
                "147.229.2.90"
            ],
            "expiration_time": 226,
            "response_time": 86.5281,
            "status": "success",
            "status_code": "NOERROR",
            "nameservers_used": [
                "188.116.92.133"
            ],
            "ds": "N/A",
            "cname": "N/A",
            "ns": "N/A",
            "soa": "N/A",
            "caa": "N/A",
            "dnskey": "N/A",
            "rrsig": "N/A"
        }
    ]
}
```

## Example (failed test domain does not exist)

INPUT:

```json
{
  "query_domains": ["nexistujicidomena.cz"],
  "query_type" : "A",
  "nameservers" : ["188.166.92.133"]
}
```

OUTPUT:

```json
{
    "run_id": 1,
    "status": "completed",
    "summary": {
        "total_tests": 1,
        "successful_tests": 0,
        "failed_tests": 1,
        "response_time_avg": 5401.9175,
        "response_time_min": 5401.9175,
        "response_time_max": 5401.9175,
        "resolution_type": "A"
    },
    "details": [
        {
            "target_host": "nexistujicidomena.cz",
            "IP_address": [],
            "expiration_time": "N/A",
            "response_time": 5401.9175,
            "status": "failed",
            "status_code": "TIMEOUT",
            "error_message": "The resolution lifetime expired after 5.402 seconds: Server Do53:188.166.92.133@53 answered The DNS operation timed out.; Server Do53:188.166.92.133@53 answered The DNS operation timed out.; Server Do53:188.166.92.133@53 answered The DNS operation timed out."
        }
    ]
}
```