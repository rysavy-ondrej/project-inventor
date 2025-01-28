## NAME

`webapp.security`

## VERSION

1.0.0

## INFO

This monitor aims to provide a summarized security monitoring of a given HTTP endpoint. It utilizes that with the use of [testssl.sh](https://testssl.sh/) bash script.
The script contains a list of known vulnerabilities, as well as generally known security best practices, which it then uses to discover if the endpoint adheres to them.
The result of this monitor is a summarization in a form of grade/score, as well as list of detected findings, which may be used to strengthen any discovered security issues.

The runtime of this monitor is usually around a minute. The time required to monitor every possible vulnerability can be quite lengthy.

## License notes

The script `testssl.sh` on which this monitor is built on is licensed under the GPLv2 license. Copy of this license can be found in the [LICENSE](script/LICENSE) file.
The license allows for copy, distribution and modification of the code. Modifications done to the code have to be released back under GPLv2 license. 
As the script included is not modified in any way, this shouldn't necessitate public re-release.

## Requirements

| Library        | Usage                                                                                                                   |
|----------------|-------------------------------------------------------------------------------------------------------------------------|
| openssl >= 1.0 | Provides the various cryptographic functionality needed for the monitor. This isn't a Python library but an OS library. |

No Python libraries are necessary.

## INPUT

| Parameter       | Type  | Description                                    | Default value           |
|-----------------|-------|------------------------------------------------|-------------------------|
| target_url      | str   | URL of HTTP endpoint.                          | mandatory               |
| connect_timeout | int   | Max seconds to wait for TCP socket connection. | None                    |
| openssl_timeout | int   | Max seconds to wait for openssl connection.    | None                    |
| script_path     | str   | Path to the `testssl.sh` script file.          | "./script/testssl.sh"   |

## OUTPUT

| Name          | Type                    | Description                                                                                                                                                                                                                                                                                                                                                       |
|---------------|-------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| grade         | str                     | Grade summarizing the quality of the endpoint security. `A` being the best and `F` the worst. A special grading of `T` will be given when the certificate is found to be invalid, and `M` when domain name doesn't match the DNS record.                                                                                                                          |
| grade_reasons | list[str]               | List of reasons given for the provided grading.                                                                                                                                                                                                                                                                                                                   |
| final_score   | int                     | Percentile scoring of the quality, with 100 being the best and 0 the worst.                                                                                                                                                                                                                                                                                       |
| findings      | dict[str,list[Finding]] | Dictionary providing lists of testssl findings, categorized into severity levels of `INFO`, `OK`, `LOW`, `MEDIUM`, `HIGH` and `CRITICAL`. Each finding provides an identifier and explanation of the finding. If the finding contains a known vulnerability, a [CVE](https://www.cve.org/) and [CWE](https://cwe.mitre.org/) identifiers may be included as well. |

## EXAMPLES

### Valid usage

#### Input

```json
{
  "target_url": "https://example.com"
}
```

#### Output

```json
{
  "output": {
    "run_id": 1,
    "status": "completed",
    "grade": "B",
    "grade_reasons": [
      "Grade capped to B. TLS 1.1 offered",
      "Grade capped to B. TLS 1.0 offered",
      "Grade capped to A. HSTS is not offered"
    ],
    "final_score": 91,
    "findings": {
      "INFO": [
        ...
      ],
      "OK": [
        ...
      ],
      "LOW": [
        ...
      ],
      "MEDIUM": [
        {
          "id": "BREACH",
          "severity": "MEDIUM",
          "cve": "CVE-2023-3587",
          "cwe": "CWE-310",
          "finding": "potentially VULNERABLE, gzip deflate HTTP compression detected  - only supplied '/' tested"
        },
        ...
      ]
    }
  }
}
```

### Error handling

#### Input

```json
{
  "target_url": "localhost"
}
```

#### Output

```json
{
    "output": {
        "status": "error",
        "error": {
            "error_code": "HTTP_SECURITY_MONITOR_ERROR",
            "description": "Error running HTTP security monitor: testssl.sh returned non-zero code: 246, and error string: \"Can't connect to '127.0.0.1:443' Make sure a firewall is not between you and your scanning target!\""
        }
    }
}
```

