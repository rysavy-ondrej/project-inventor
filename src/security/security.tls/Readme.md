# Security TLS/SSL Test 

This test is designed to test the initial handshake of TLS (Transport Layer Security) communication. It attempts to create a secured connection to the target host using configurable parameters (TLS version, cipher suites, etc.), collects server parameters, and measures performance metrics such as handshake duration and success rate. The purpose is to ensure that the target host supports desired TLS configurations and performs adequately under various conditions.

## Requirements

| Library | Version   |
| ------- | --------- |
| pyOpenSS| 24.1.0    |
| scapy   | 2.5.0     |
| cryptography | 41.0.5  |

The test needs to be run with elevated privileges to capture packets and perform the handshake.

## Input

For TLS version 1.3, the specified cipher suites are ignored, because the library does not support the configuration of cipher suites for TLS 1.3. The library uses the default cipher suites for TLS 1.3.

```proto
message TLSHandshakeTestConfig {
    string target_host = 1; // The target host to connect to
    int32 target_port = 2; // The target port to connect to
    string tls_version = 3; // The TLS version to use for the connection
    repeated string cipher_suites = 4; // The list of cipher suites to use for the connection
    repeated string elliptic_curves = 5; // The list of elliptic curves to use for the connection
    repeated Extension extensions = 6; // The list of extensions to use for the connection
    int32 timeout = 7; // The timeout for the connection in seconds
}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| target_host | str | The target host to connect to. |
| target_port | int | The target port to connect to. |
| tls_version | str | The TLS version to use for the connection. |
| cipher_suites | List[str] | The list of cipher suites to use for the connection. |
| elliptic_curves | List[str] | The list of elliptic curves to use for the connection. |
| extensions | List[Extension] | The list of extensions to use for the connection. |
| timeout | int | The timeout for the connection in seconds. |

## Output

The output of the test is divided into two main sections: summary information and detailed information.

```proto
// Message representing the overall test results
message TLSHandshakeTestResult {
    ID run_id = 1; // The unique identifier of the test run
    TestStatus status = 2; // The overall status of the tests 
    int32 handshake_time = 3; // The time taken to complete the handshake in milliseconds without TCP handshake
    string IP_address = 4; // The target IP that was connected to
    int32 target_port = 5; // The target port that was connected to
    string tls_version = 6; // The TLS version used for the connection
    string cipher_suite = 7; // The cipher suite used for the connection
    string elliptic_curve = 8; // The elliptic curve used for the connection
    string SNIs = 9; // The server name indication used for the connection
    string alpn = 10; // The application layer protocol negotiation used for the connection
    int32 client_extension_count = 11; // The number of client extensions used for the connection
    int32 server_extension_count = 12; // The number of server extensions used for the connection
    repeated string client_extension_names = 13; // The names of the client extensions used for the connection
    repeated string server_extension_names = 14; // The names of the server extensions used for the connection
    Extensions extensions = 15; // The extensions used for the connection
    repeated ServerCertificate server_cert_chain = 16; // The server certificate chain information
    ServerCertificate server_cert = 17; // The server certificate information
}

// Message representing the server certificate information
ServerCertificate {
    string subject_cn = 1; // The common name of the subject
    string subject_on = 2; // The organization name of the subject
    string subject_country = 3; // The country of the subject
    string issuer_cn = 4; // The common name of the issuer
    string issuer_on = 5; // The organization name of the issuer
    string issuer_country = 6; // The country of the issuer
    string not_before = 7; // The not before date of the certificate
    string not_after = 8; // The not after date of the certificate
    int64 serial_number = 9; // The serial number of the certificate
    int32 version = 10; // The version of the certificate
    string signature_algorithm = 11; // The signature algorithm of the certificate
    int32 public_key_length = 12; // The public key size of the certificate
    string fingerprint = 13; // The fingerprint of the certificate
}

// Message representing the extensions used for the connection
Extensions {
    string key_usage = 1; // The key usage extension
    string extended_key_usage = 2; // The extended key usage extension
    repeated string authority_info_access = 3; // The authority information access extension
}
```
In case of successful handshake, the following fields are included:

| Field | Type | Description |
|-------|------|-------------|
| run_id | int | The unique identifier of the test run. |
| status | TestStatus | The overall status of the tests. |
| handshake_time | int | The time taken to complete the handshake in milliseconds. |
| IP_address | str | The target IP that was connected to|
| target_port | int | The target port to connect to. |
| tls_version | str | The TLS version used for the connection. |
| cipher_suite | str | The cipher suite used for the connection. |
| elliptic_curve | str | The elliptic curve used for the connection. |
| SNIs | str | The server name indication used for the connection. |
| alpn | str | The application layer protocol negotiation used for the connection. |
| client_extension_count | int | The number of client extensions used for the connection. |
| server_extension_count | int | The number of server extensions used for the connection. |
| client_extension_names | List[str] | The names of the client extensions used for the connection. |
| server_extension_names | List[str] | The names of the server extensions used for the connection. |
| extensions | Extensions | The extensions used for the connection. |
| server_cert_chain | List[ServerCertificate] | The server certificate chain information. |
| server_cert | ServerCertificate | The server certificate information. |

For failed handshake, the following fields are included:

| Field | Type | Description |
|-------|------|-------------|
| run_id | int | The unique identifier of the test run. |
| status | TestStatus | The overall status of the tests. |
| error_message | str | The error message describing the failure. |
| error_description | str | The description of the error. |

## How to run simple test

```bash
sudo pytest monitor_tls.py
```

The result will be in the `test` directory in file `output.json`
For running the test you need `sudo` permissions just as you would need them for running the script itself.

## Examples

INPUT:

```json
{
    "target_host": "www.example.com",
    "target_port": 443,
    "tls_version": "TLSv1.2",
    "cipher_suites": [
        "ECDHE-ECDSA-AES256-GCM-SHA384",
        "ECDHE-RSA-AES256-GCM-SHA384"
    ],
    "elliptic_curves": [
        "prime256v1"
    ],
    "extensions": [
        {
            "type": "sni",
            "data": "example.com"
        },
        {
            "type": "alpn",
            "data": ["spdy/2", "http/1.1"]
        }
    ],
    "timeout": 10
}
```

OUTPUT:

```json
{
    "run_id": 1,
    "status": "completed",
    "handshake_time": 459,
    "IP_address": "93.184.215.14",
    "target_port": 443,
    "tls_version": "TLSv1.2",
    "cipher_suite": "ECDHE-RSA-AES256-GCM-SHA384",
    "elliptic_curve": "prime256v1",
    "SNIs": "example.com",
    "alpn": "http/1.1",
    "client_extension_count": 8,
    "server_extension_count": 5,
    "client_extension_names": [
        "TLS Extension - Server Name",
        "TLS Extension - Supported Point Format",
        "TLS Extension - Supported Groups",
        "TLS Extension - Session Ticket",
        "TLS Extension - Application Layer Protocol Negotiation",
        "TLS Extension - Encrypt-then-MAC",
        "TLS Extension - Extended Master Secret",
        "TLS Extension - Signature Algorithms"
    ],
    "server_extension_names": [
        "TLS Extension - Renegotiation Indication",
        "TLS Extension - Supported Point Format",
        "TLS Extension - Session Ticket",
        "TLS Extension - Application Layer Protocol Negotiation",
        "TLS Extension - Extended Master Secret"
    ],
    "addition_server_cert_info": {
        "key_usage": "Digital Signature, Key Encipherment",
        "extended_key_usage": "TLS Web Server Authentication, TLS Web Client Authentication",
        "authority_info_access": [
            "OCSP - URI:http://ocsp.digicert.com",
            "CA Issuers - URI:http://cacerts.digicert.com/DigiCertGlobalG2TLSRSASHA2562020CA1-1.crt"
        ]
    },
    "server_cert_chain": [
        {
            "subject_cn": "www.example.org",
            "subject_on": "Internet Corporation for Assigned Names and Numbers",
            "subject_country": "US",
            "issuer_cn": "DigiCert Global G2 TLS RSA SHA256 2020 CA1",
            "issuer_on": "DigiCert Inc",
            "issuer_country": "US",
            "not_before": "2024-01-30 00:00:00",
            "not_after": "2025-03-01 23:59:59",
            "serial_number": 9781292415466404211737309641897402759,
            "version": 3,
            "signature_algorithm": "sha256WithRSAEncryption",
            "public_key_length": 2048,
            "fingerprint": "EF:BA:26:D8:C1:CE:37:79:AC:77:63:0A:90:F8:21:63:A3:D6:89:2E:D6:AF:EE:40:86:72:CF:19:EB:A7:A3:62"
        },
        {
            "subject_cn": "DigiCert Global G2 TLS RSA SHA256 2020 CA1",
            "subject_on": "DigiCert Inc",
            "subject_country": "US",
            "issuer_cn": "DigiCert Global Root G2",
            "issuer_on": "DigiCert Inc",
            "issuer_country": "US",
            "not_before": "2021-03-30 00:00:00",
            "not_after": "2031-03-29 23:59:59",
            "serial_number": 17226682543955925492517929723242541158,
            "version": 3,
            "signature_algorithm": "sha256WithRSAEncryption",
            "public_key_length": 2048,
            "fingerprint": "C8:02:5F:9F:C6:5F:DF:C9:5B:3C:A8:CC:78:67:B9:A5:87:B5:27:79:73:95:79:17:46:3F:C8:13:D0:B6:25:A9"
        }
    ],
    "server_cert": {
        "subject_cn": "www.example.org",
        "subject_on": "Internet Corporation for Assigned Names and Numbers",
        "subject_country": "US",
        "issuer_cn": "DigiCert Global G2 TLS RSA SHA256 2020 CA1",
        "issuer_on": "DigiCert Inc",
        "issuer_country": "US",
        "not_before": "2024-01-30 00:00:00",
        "not_after": "2025-03-01 23:59:59",
        "serial_number": 9781292415466404211737309641897402759,
        "version": 3,
        "signature_algorithm": "sha256WithRSAEncryption",
        "public_key_length": 2048,
        "fingerprint": "EF:BA:26:D8:C1:CE:37:79:AC:77:63:0A:90:F8:21:63:A3:D6:89:2E:D6:AF:EE:40:86:72:CF:19:EB:A7:A3:62"
    }
}
```

## Example (failed test because of not existing domain)

INPUT

```json
{
    "target_host": "neexistujicidomena.cz",
    "target_port": 443,
    "tls_version": "TLSv1.2",
    "cipher_suites": [
        "ECDHE-ECDSA-AES256-GCM-SHA384",
        "ECDHE-RSA-AES256-GCM-SHA384"
    ],
    "elliptic_curves": [
        "prime256v1"
    ],
    "extensions": [
        {
            "type": "sni",
            "data": "example.com"
        },
        {
            "type": "alpn",
            "data": ["spdy/2", "http/1.1"]
        }
    ],
    "timeout": 6 
}
```

OUTPUT

```json
{
    "status": "error",
    "error": {
        "error_code": "TLS_TEST_ERROR",
        "description": "Error running TLS test: 'target_host'"
    }
}
```

## Example (failed test because of unsupported TLS version)

INPUT

```json
{
    "target_host": "www.example.com",
    "target_port": 443,
    "tls_version": "TLSv1.0",
    "cipher_suites": [
        "ECDHE-ECDSA-AES256-GCM-SHA384",
        "ECDHE-RSA-AES256-GCM-SHA384"
    ],
    "elliptic_curves": [
        "prime256v1"
    ],
    "extensions": [
        {
            "type": "sni",
            "data": "example.com"
        },
        {
            "type": "alpn",
            "data": ["spdy/2", "http/1.1"]
        }
    ],
    "timeout": 6 
}
```

OUTPUT

```json
{
    "run_id": 1,
    "status": "error",
    "error": {
        "error_msg": "SSL Error",
        "description": "[('SSL routines', '', 'no protocols available')]"
    }
}
```
