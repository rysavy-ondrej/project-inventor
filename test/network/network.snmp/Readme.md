# network.snmp — tests

Auto-generated tests for the monitor in
[`src/network/network.snmp`](../../../src/network/network.snmp), following
[../../Readme.md](../../Readme.md).

## Running

```sh
./run_tests.sh
```

Builds a throwaway venv from `src/network/network.snmp/requirements.txt`, runs every
case in `inputs/`, writes results to `outputs/`, and reports `[PASS]/[FAIL]/[SKIP]`.

## Targets

none — **negative testing only** (no live SNMP agent)

## Caveats

**Negative-only.** All cases hit `run()`'s validation branches before any network I/O. Requires the `easysnmp` C-extension to import, which needs system net-snmp headers (`sudo apt-get install libsnmp-dev`); the suite skips cleanly if it cannot be installed/imported.

## Cases

| Case | Kind | Note |
| --- | --- | --- |
| `snmp_empty_oids` | negative | Negative: empty oids rejected. |
| `snmp_space_in_oids` | negative | Negative: whitespace in oids rejected. |
| `snmp_multi_host` | negative | Negative: comma in target_host rejected. |
| `snmp_missing_params` | negative | Negative: no params -> error. |

Input metadata keys (stripped before the monitor sees them): `_comment`,
`expect_status` (`completed` default, or `error`), `expect_keys` (keys that must
be present on success), `requires_root`, `skip_on_error`.
