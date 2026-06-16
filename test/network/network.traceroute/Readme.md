# network.traceroute — tests

Auto-generated tests for the monitor in
[`src/network/network.traceroute`](../../../src/network/network.traceroute), following
[../../Readme.md](../../Readme.md).

## Running

```sh
./run_tests.sh
```

Builds a throwaway venv from `src/network/network.traceroute/requirements.txt`, runs every
case in `inputs/`, writes results to `outputs/`, and reports `[PASS]/[FAIL]/[SKIP]`.

## Targets

`8.8.8.8`

## Caveats

**Live cases need root** (raw sockets). Without root they are skipped; run `sudo ./run_tests.sh`. Also pulls in `numpy` (slower venv build). The negative case runs unprivileged.

## Cases

| Case | Kind | Note |
| --- | --- | --- |
| `traceroute_google_dns` | live (root) | Traceroute to 8.8.8.8 (raw sockets -> root). |
| `traceroute_missing_params` | negative | Negative (unprivileged): missing ttl_max etc -> error. |

Input metadata keys (stripped before the monitor sees them): `_comment`,
`expect_status` (`completed` default, or `error`), `expect_keys` (keys that must
be present on success), `requires_root`, `skip_on_error`.
