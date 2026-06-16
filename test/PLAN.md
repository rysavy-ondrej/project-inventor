# Test implementation plan — network & security monitors

Plan for adding runnable tests under `test/` for every monitor in
`src/network/` and `src/security/`, following the conventions in
[Readme.md](Readme.md). Each monitor gets a `test/<group>/<group>.<name>/`
directory with `inputs/`, `outputs/`, `run_<name>_tests.py`, `run_tests.sh`,
and a per-monitor `Readme.md`.

Two monitors are already done and serve as the templates:

- [network/network.dns](network/network.dns) — calls `run()` directly; shows the
  summary/`failed_tests` assertion style and the two negative-case styles.
- [security/security.tls](security/security.tls) — calls a core probe function
  directly to avoid the root-only capture path; shows enforced-value assertions.

## Shared facts (verified from source)

- **Uniform entry point.** Every monitor exposes
  `run(params: dict, run_id: int, queue: Queue = None) -> dict`. Unlike TLS,
  none of the monitors below start a packet-capture thread, so all are driven
  via `run(params, run_id)` directly — no need to reach for an inner function.
- **Result schema.** Success returns `status: "completed"` (some also carry a
  `summary`/`details` or probe fields); failure returns
  `status: "error"` with an `error: {error_code, description}` object produced by
  each module's `error_json()`.
- **Negative cases available everywhere.** All `run()` bodies wrap a
  `try/except` that returns `status: "error"` on missing params
  (`"Parametrs not specified"` / `"CONFIG FILE ERROR"`) or bad input. That gives
  every monitor a deterministic top-level negative case with no network needed.
- **icmplib is mostly a helper.** ftp, imap, mqtt, ntp, smtp, snmp, ldap, ssh
  import only `is_hostname`/`resolve`/`is_ipv6_address` from icmplib — **no raw
  sockets, no root**. Only ping (`from icmplib import *`) and traceroute
  (`icmplib.traceroute`) actually open raw sockets.

## Work tiers (by feasibility)

### Tier 1 — straightforward (do first)

Pure socket/library clients: call `run()` directly, no root, stable public
targets exist. Same shape as the dns reference.

| Monitor | Module | Key config params | Suggested live targets | Negative case |
| --- | --- | --- | --- | --- |
| network.ntp | `network_ntp` | `target_host` | `pool.ntp.org`, `time.google.com`, `tik.cesnet.cz` | missing `target_host` → error |
| network.mqtt | `network_mqtt` | `target_host`, `topic_names` (comma-sep) | `test.mosquitto.org` with `$SYS/broker/version,$SYS/broker/uptime` | unresolvable host → error |
| security.ssh | `security_ssh` | `target_host` | `github.com`, `gitlab.com` | comma in `target_host` → error |
| security.ldap | `security_ldap` | `target_host` | `ldap.forumsys.com`, `db.debian.org` | missing `target_host` → error |
| network.ftp | `network_ftp` | `target_host` | `ftp.gnu.org`, `test.rebex.net` | unresolvable host → error |
| network.imap | `network_imap` | `target_host`, `target_port`, `login_flag` (keep `"False"`), `login_username`, `login_server` | `imap.gmail.com:993` (banner, no login) | bad port → error |

**Use public targets only.** The existing `src/.../test/input.json` examples
point at internal VUT FIT hosts; replace them with the public equivalents above
so the tests run anywhere. Concretely:

- ssh: `eva.fit.vutbr.cz` → `github.com` / `gitlab.com`
- ldap: `ldap.fit.vutbr.cz` → `ldap.forumsys.com` / `db.debian.org`
- imap: `kazi.fit.vutbr.cz` → `imap.gmail.com`
- smtp (Tier 3): `kazi.fit.vutbr.cz` → a public MX
- snmp (Tier 3): `isa.fit.vutbr.cz` → n/a (negative-only, see Tier 3)

Notes:
- Keep `login_flag`/`send_email_flag` style booleans `"False"` so no credentials
  are ever needed; the monitors only probe banner/connectivity in that mode.
- For each monitor, assert `status == "completed"` for the positive cases and
  `status == "error"` for the negative case. Add monitor-specific
  `expect_*` keys where a result field is worth pinning (e.g. ntp offset
  present, imap port echoed back).

### Tier 2 — privileged (raw sockets, need root)

`run()` opens raw ICMP sockets, so these fail unprivileged. Decision:

1. **Skip the privileged (live-target) cases when not run as root.**
   `run_tests.sh` checks `id -u` (equivalently `EUID`); if it is not 0 it prints
   a clear note — e.g. `SKIPPED: network.ping live cases require root privilege
   to open raw ICMP sockets; re-run with 'sudo ./run_tests.sh' to execute them` —
   and exits 0 without running those cases. When run as root the live cases
   execute normally.
2. **Always run the top-level negative case** (missing params), which needs no
   socket and runs unprivileged — so the suite has at least one real assertion
   even when the privileged cases are skipped.

The per-monitor `Readme.md` states the root requirement and the
`sudo ./run_tests.sh` invocation.

| Monitor | Module | Key config params | Targets | Extra |
| --- | --- | --- | --- | --- |
| network.ping | `network_ping` | `target_host`, `packet_size`, `packet_count`, `interpacket_delay`, `timeout` | `8.8.8.8`, `1.1.1.1` | raw ICMP → root |
| network.traceroute | `network_traceroute` | `target_host`, `ttl_max`, `packet_size`, `timeout`, `repeats` | `8.8.8.8` | raw sockets → root; also pulls in `numpy` (slower venv build) |

### Tier 3 — special dependency / infrastructure

These need more than a throwaway venv + public host. Implement last; document the
constraint loudly in the per-monitor Readme and make `run_tests.sh` fail/skip
with that explanation rather than a confusing pip or timeout error.

| Monitor | Obstacle | Plan |
| --- | --- | --- |
| network.snmp | `easysnmp` is a C-extension binding to system net-snmp libs (`libsnmp-dev`); also needs a live SNMP agent (public ones are scarce/unstable). | **Negative testing only — no live agent target.** Ship only the cases that hit `run()`'s validation branches before any network I/O: missing/empty `oids`, missing `community_string`, a space inside `oids`, and missing params. These run without a live agent. The per-monitor Readme still documents the `libsnmp-dev` prereq needed for the import to succeed. |
| network.smtp | Outbound port 25 is frequently blocked by ISPs/cloud, so a live banner probe is environment-dependent. Keep `send_email_flag: "False"`. | Use a public MX (e.g. a provider's mail host) for the positive case but treat a connection timeout as an environment skip; always ship the negative case (bad port / missing params). |

## Per-monitor deliverables (same for all)

For each monitor, following [Readme.md](Readme.md) §1–7:

1. `test/<group>/<group>.<name>/inputs/*.json` — 2–4 positive cases across
   meaningful variations + at least one negative case. Strip-able metadata keys:
   `_comment`, `expect_status` (default `completed`), and any `expect_*` field.
2. `run_<name>_tests.py` — resolve repo root from `__file__`, import the module,
   run each input through `run(params, run_id)`, write `outputs/<case>.json`,
   assert `status` and any `expect_*`, print `[PASS]/[FAIL]`, exit non-zero on
   failure. (Reuse the dns runner as the starting point — same result shape.)
3. `run_tests.sh` — temp venv from the monitor's own
   `src/<group>/<group>.<name>/requirements.txt`, run the Python runner, clean up
   on exit. Tier 2/3 scripts add the privilege/dependency skip guard.
4. `Readme.md` — layout, run command, root/dependency caveat, case table.
5. Run it; commit `inputs/` and generated `outputs/`.

## Suggested sequencing

1. **Tier 1, batch A:** ntp, ssh, ldap (simplest single-param probes) — fastest
   way to validate the runner generalizes beyond dns.
2. **Tier 1, batch B:** ftp, imap, mqtt.
3. **Tier 2:** ping, then traceroute (add the root-skip guard once, reuse).
4. **Tier 3:** smtp, then snmp (snmp is negative-only; document prereqs).

## Decisions (locked)

- **Public targets only.** All live cases use the public hosts listed in Tier 1
  / Tier 3; the internal VUT FIT hosts from the `src/.../test/input.json`
  examples are not used (mapping under the Tier 1 table).
- **Privileged cases skip without root.** Tier 2 (ping, traceroute) skips its
  live raw-socket cases when not run as root, printing a note that the operation
  requires privilege and to re-run with `sudo ./run_tests.sh`; the negative case
  still runs unprivileged.
- **snmp is negative-testing only.** No live SNMP agent target; only the
  validation-branch negative cases are shipped.

## Open decisions to confirm before/while implementing

- **smtp positive case.** Outbound port 25 is often blocked, so the live banner
  probe is environment-dependent. Confirm whether to keep a public-MX positive
  case (treating a timeout as an environment skip) or make smtp negative-only
  like snmp.
