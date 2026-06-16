# network.smtp — tests

Auto-generated tests for the monitor in
[`src/network/network.smtp`](../../../src/network/network.smtp), following
[../../Readme.md](../../Readme.md).

## Running

```sh
./run_tests.sh
```

Builds a throwaway venv from `src/network/network.smtp/requirements.txt`, runs every
case in `inputs/`, writes results to `outputs/`, and reports `[PASS]/[FAIL]/[SKIP]`.

## Targets

`gmail-smtp-in.l.google.com:25` (EHLO only, no email)

## Caveats

The live case needs outbound **port 25**, which many networks block; it is treated as an environment **SKIP** (not a failure) when the port is unreachable. `send_email_flag` is kept `"False"`.

## Cases

| Case | Kind | Note |
| --- | --- | --- |
| `smtp_public_mx` | live (skippable) | EHLO probe to a public MX (no email sent). SKIPPED where outbound port 25 is blocked. |
| `smtp_multi_port` | negative | Negative: comma in target_port is rejected before any I/O. |

Input metadata keys (stripped before the monitor sees them): `_comment`,
`expect_status` (`completed` default, or `error`), `expect_keys` (keys that must
be present on success), `requires_root`, `skip_on_error`.
