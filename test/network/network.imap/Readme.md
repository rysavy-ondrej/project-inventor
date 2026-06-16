# network.imap — tests

Auto-generated tests for the monitor in
[`src/network/network.imap`](../../../src/network/network.imap), following
[../../Readme.md](../../Readme.md).

## Running

```sh
./run_tests.sh
```

Builds a throwaway venv from `src/network/network.imap/requirements.txt`, runs every
case in `inputs/`, writes results to `outputs/`, and reports `[PASS]/[FAIL]/[SKIP]`.

## Targets

`imap.gmail.com:993` (banner/NOOP, no login)

## Caveats

`login_flag` is kept `"False"` so no credentials are needed.

## Cases

| Case | Kind | Note |
| --- | --- | --- |
| `imap_gmail` | live | IMAPS connect + NOOP against Gmail (no login). |
| `imap_multi_port` | negative | Negative: comma in target_port is rejected before any I/O. |

Input metadata keys (stripped before the monitor sees them): `_comment`,
`expect_status` (`completed` default, or `error`), `expect_keys` (keys that must
be present on success), `requires_root`, `skip_on_error`.
