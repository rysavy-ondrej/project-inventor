# network.mqtt — tests

Auto-generated tests for the monitor in
[`src/network/network.mqtt`](../../../src/network/network.mqtt), following
[../../Readme.md](../../Readme.md).

## Running

```sh
./run_tests.sh
```

Builds a throwaway venv from `src/network/network.mqtt/requirements.txt`, runs every
case in `inputs/`, writes results to `outputs/`, and reports `[PASS]/[FAIL]/[SKIP]`.

## Targets

`test.mosquitto.org`

## Caveats

None.

## Cases

| Case | Kind | Note |
| --- | --- | --- |
| `mqtt_sys_topics` | live | Subscribe to broker $SYS topics on the public test broker. |
| `mqtt_multi_target` | negative | Negative: comma in target_host is rejected before any I/O. |

Input metadata keys (stripped before the monitor sees them): `_comment`,
`expect_status` (`completed` default, or `error`), `expect_keys` (keys that must
be present on success), `requires_root`, `skip_on_error`.
