# security.tls — handshake tests

Self-contained tests for the TLS monitor in
[`src/security/security.tls`](../../../src/security/security.tls). They exercise
the version/cipher logic against live targets over both **TLSv1.2** and
**TLSv1.3**.

## Layout

```
inputs/    one JSON config per test case (monitor config schema + optional test metadata)
outputs/   generated results, one <case>.json per input (overwritten each run)
run_tls_tests.py   loads inputs/, runs the handshake, writes outputs/, asserts expectations
run_tests.sh       builds a throwaway venv from the monitor's requirements, then runs the above
```

## Running

```sh
./run_tests.sh
```

This creates a temporary virtual environment, installs the pinned dependencies
from `src/security/security.tls/requirements.txt`, runs every case, and removes
the venv on exit. Exit code is non-zero if any case fails.

The harness calls `perform_tls_handshake` directly rather than the monitor's
`run()` entry point, so it does **not** need root — the `run()` path also starts
a scapy packet capture (`sniff`) that requires elevated privileges and is
orthogonal to the cipher/version behaviour under test. Targets are live public
hosts, so a network connection is required.

## Test cases

| Case | Version | Requested cipher | Expectation |
|------|---------|------------------|-------------|
| `tls12_google` | TLSv1.2 | `ECDHE-RSA-AES256-GCM-SHA384` | completes, negotiates that cipher |
| `tls12_cloudflare` | TLSv1.2 | `ECDHE-ECDSA-AES128-GCM-SHA256` | completes, negotiates that cipher |
| `tls13_google` | TLSv1.3 | `TLS_AES_256_GCM_SHA384` | completes, negotiates that ciphersuite |
| `tls13_cloudflare` | TLSv1.3 | `TLS_CHACHA20_POLY1305_SHA256` | completes, negotiates that ciphersuite (overrides server default → proves enforcement) |
| `tls13_invalid_cipher` | TLSv1.3 | `ECDHE-RSA-AES256-GCM-SHA384` (a 1.2 name) | rejected with `status: error` |

## Input metadata keys

Inputs are ordinary monitor configs plus optional test-only keys (stripped
before the config reaches the monitor):

- `_comment` — free-text note.
- `expect_status` — expected `status` (defaults to `completed`).
- `expect_cipher` — expected negotiated cipher (defaults to the single
  requested cipher).
