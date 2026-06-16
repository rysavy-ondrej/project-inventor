# security.ldap — tests

Auto-generated tests for the monitor in
[`src/security/security.ldap`](../../../src/security/security.ldap), following
[../../Readme.md](../../Readme.md).

## Running

```sh
./run_tests.sh
```

Builds a throwaway venv from `src/security/security.ldap/requirements.txt`, runs every
case in `inputs/`, writes results to `outputs/`, and reports `[PASS]/[FAIL]/[SKIP]`.

## Targets

`ldap.forumsys.com`, `db.debian.org`

## Caveats

On success the monitor does not set a `status` field; success is detected by the absence of an error marker.

## Cases

| Case | Kind | Note |
| --- | --- | --- |
| `ldap_forumsys` | live | Anonymous bind + root-DSE search against the public forumsys test server. |
| `ldap_debian` | live | Anonymous bind against the Debian public LDAP. |
| `ldap_multi_target` | negative | Negative: comma in target_host is rejected. |

Input metadata keys (stripped before the monitor sees them): `_comment`,
`expect_status` (`completed` default, or `error`), `expect_keys` (keys that must
be present on success), `requires_root`, `skip_on_error`.
