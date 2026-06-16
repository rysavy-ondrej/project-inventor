# network.dns — resolution tests

Self-contained tests for the DNS monitor in
[`src/network/network.dns`](../../../src/network/network.dns). They exercise
several query types and both failure modes against live DNS using public
resolvers.

## Layout

```
inputs/    one JSON config per test case (monitor config schema + optional test metadata)
outputs/   generated results, one <case>.json per input (overwritten each run)
run_dns_tests.py   loads inputs/, runs the monitor, writes outputs/, asserts expectations
run_tests.sh       builds a throwaway venv from the monitor's requirements, then runs the above
```

## Running

```sh
./run_tests.sh
```

Creates a temporary virtual environment, installs the pinned dependencies from
`src/network/network.dns/requirements.txt` (dnspython), runs every case, and
removes the venv on exit. Exit code is non-zero if any case fails.

The harness calls the monitor's public `run()` entry point directly — DNS
resolution is pure dnspython with no packet capture, so **no root is required**.
Tests query live public resolvers, so a network connection is required.

## Test cases

| Case | Query | Targets | Expectation |
|------|-------|---------|-------------|
| `dns_a_record` | A | example.com, www.vutbr.cz | completes, 0 failed |
| `dns_aaaa_record` | AAAA | www.google.com, cloudflare.com | completes, 0 failed |
| `dns_ns_record` | NS | vutbr.cz, example.com | completes, 0 failed |
| `dns_ptr_record` | PTR | 8.8.8.8, 1.1.1.1 | completes, 0 failed (reverse lookup) |
| `dns_nxdomain` | A | nonexistent domain | **completes** but `failed_tests == 1` (per-domain failure surfaced, not swallowed) |
| `dns_invalid_query_type` | BOGUS | example.com | rejected with top-level `status: error` |

Note the two distinct negative styles: an unsupported `query_type` fails the
whole run (`status: error`), whereas an unresolvable domain still yields
`status: completed` and is only reflected in `summary.failed_tests` and that
domain's per-detail `status`.

## Input metadata keys

Inputs are ordinary monitor configs plus optional test-only keys (stripped
before the config reaches the monitor):

- `_comment` — free-text note.
- `expect_status` — expected top-level `status` (defaults to `completed`).
- `expect_failed_tests` — expected `summary.failed_tests`.
- `expect_successful_tests` — expected `summary.successful_tests`.
