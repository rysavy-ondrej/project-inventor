# security.ssh — tests

Auto-generated tests for the monitor in
[`src/security/security.ssh`](../../../src/security/security.ssh), following
[../../Readme.md](../../Readme.md).

## Running

```sh
./run_tests.sh
```

Builds a throwaway venv from `src/security/security.ssh/requirements.txt`, runs every
case in `inputs/`, writes results to `outputs/`, and reports `[PASS]/[FAIL]/[SKIP]`.

## Targets

`github.com`, `gitlab.com`

## Caveats

On success the monitor does not set a `status` field; success is detected by the absence of an error marker.

## Cases

| Case | Kind | Note |
| --- | --- | --- |
| `ssh_github` | live | SSH banner grab from github.com. |
| `ssh_gitlab` | live | SSH banner grab from gitlab.com. |
| `ssh_multi_target` | negative | Negative: comma in target_host is rejected. |

Input metadata keys (stripped before the monitor sees them): `_comment`,
`expect_status` (`completed` default, or `error`), `expect_keys` (keys that must
be present on success), `requires_root`, `skip_on_error`.
