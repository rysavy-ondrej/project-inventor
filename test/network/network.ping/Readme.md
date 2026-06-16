# network.ping — tests

Auto-generated tests for the monitor in
[`src/network/network.ping`](../../../src/network/network.ping), following
[../../Readme.md](../../Readme.md).

## Running

```sh
./run_tests.sh
```

Builds a throwaway venv from `src/network/network.ping/requirements.txt`, runs every
case in `inputs/`, writes results to `outputs/`, and reports `[PASS]/[FAIL]/[SKIP]`.

## Targets

`8.8.8.8`, `1.1.1.1`

## Caveats

**Live cases need root** (raw ICMP sockets). Without root they are skipped; run `sudo ./run_tests.sh` to execute them. The negative case runs unprivileged.

## Cases

| Case | Kind | Note |
| --- | --- | --- |
| `ping_google_dns` | live (root) | ICMP echo to 8.8.8.8 (raw socket -> root). |
| `ping_cloudflare` | live (root) | ICMP echo to 1.1.1.1 (raw socket -> root). |
| `ping_missing_params` | negative | Negative (unprivileged): missing packet_size/count -> error. |

Input metadata keys (stripped before the monitor sees them): `_comment`,
`expect_status` (`completed` default, or `error`), `expect_keys` (keys that must
be present on success), `requires_root`, `skip_on_error`.
