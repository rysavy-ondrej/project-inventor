# network.ftp — tests

Auto-generated tests for the monitor in
[`src/network/network.ftp`](../../../src/network/network.ftp), following
[../../Readme.md](../../Readme.md).

## Running

```sh
./run_tests.sh
```

Builds a throwaway venv from `src/network/network.ftp/requirements.txt`, runs every
case in `inputs/`, writes results to `outputs/`, and reports `[PASS]/[FAIL]/[SKIP]`.

## Targets

`ftp.gnu.org`, `test.rebex.net`

## Caveats

None.

## Cases

| Case | Kind | Note |
| --- | --- | --- |
| `ftp_gnu` | live | Anonymous FTP welcome banner from ftp.gnu.org. |
| `ftp_rebex` | live | Rebex public FTP test server (anonymous login may be refused; banner still returned). |
| `ftp_multi_target` | negative | Negative: comma in target_host is rejected. |

Input metadata keys (stripped before the monitor sees them): `_comment`,
`expect_status` (`completed` default, or `error`), `expect_keys` (keys that must
be present on success), `requires_root`, `skip_on_error`.
