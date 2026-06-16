# network.ntp — tests

Auto-generated tests for the monitor in
[`src/network/network.ntp`](../../../src/network/network.ntp), following
[../../Readme.md](../../Readme.md).

## Running

```sh
./run_tests.sh
```

Builds a throwaway venv from `src/network/network.ntp/requirements.txt`, runs every
case in `inputs/`, writes results to `outputs/`, and reports `[PASS]/[FAIL]/[SKIP]`.

## Targets

`pool.ntp.org`, `time.google.com`, `tik.cesnet.cz`

## Caveats

None — UDP NTP, no privileges needed.

## Cases

| Case | Kind | Note |
| --- | --- | --- |
| `ntp_pool` | live | NTP query to the public pool. |
| `ntp_google` | live | Google public NTP. |
| `ntp_cesnet` | live | CESNET stratum-1 server. |
| `ntp_missing_host` | negative | Negative: no target_host -> error. |

Input metadata keys (stripped before the monitor sees them): `_comment`,
`expect_status` (`completed` default, or `error`), `expect_keys` (keys that must
be present on success), `requires_root`, `skip_on_error`.
