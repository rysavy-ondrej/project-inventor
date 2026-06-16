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
| security.ssh | `security_ssh` | `target_host` | `github.com`, a public university host | comma in `target_host` → error |
| security.ldap | `security_ldap` | `target_host` | `ldap.forumsys.com`, `db.debian.org` | missing `target_host` → error |
| network.ftp | `network_ftp` | `target_host` | `ftp.gnu.org`, `test.rebex.net` | unresolvable host → error |
| network.imap | `network_imap` | `target_host`, `target_port`, `login_flag` (keep `"False"`), `login_username`, `login_server` | `imap.gmail.com:993` (banner, no login) | bad port → error |

Notes:
- Keep `login_flag`/`send_email_flag` style booleans `"False"` so no credentials
  are ever needed; the monitors only probe banner/connectivity in that mode.
- For each monitor, assert `status == "completed"` for the positive cases and
  `status == "error"` for the negative case. Add monitor-specific
  `expect_*` keys where a result field is worth pinning (e.g. ntp offset
  present, imap port echoed back).

### Tier 2 — privileged (raw sockets, need root)

`run()` opens raw ICMP sockets, so these fail unprivileged. Two options per the
Readme's "privileged capture paths" rule:

1. Preferred: make `run_tests.sh` detect lack of privilege and **skip with a
   clear message** (exit 0 but print `SKIPPED: needs root`), and document the
   `sudo ./run_tests.sh` invocation in the per-monitor Readme.
2. Still always include the **top-level negative case** (missing params), which
   needs no socket and runs unprivileged — so the suite has at least one real
   assertion even without root.

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
| network.snmp | `easysnmp` is a C-extension binding to system net-snmp libs (`libsnmp-dev`); also needs a live SNMP agent (public ones are scarce/unstable). | Document the apt prereq; target a known public/test agent if one is available, otherwise ship only the unprivileged negative cases (missing `oids`/`community_string`, which hit the validation branch before any network I/O) and mark the live case as opt-in. |
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
3. **Tier 2:** ping, then traceroute (add the privilege-skip guard once, reuse).
4. **Tier 3:** smtp, then snmp (document prereqs; ship negative cases at minimum).

## Open decisions to confirm before/while implementing

- **Live-network dependence.** All positive cases hit public hosts. Acceptable
  per the Readme ("tests hit live targets"), but Tier 2/3 add privilege/egress
  variance — confirm the skip-vs-fail behaviour is desired.
- **Pinned target hosts.** The targets above are suggestions; confirm or swap for
  hosts known-stable in the project's environment (the existing
  `src/.../test/input.json` files use VUT FIT hosts that may be internal).
- **snmp scope.** Decide whether to invest in a live SNMP agent target or ship
  snmp as negative-cases-only with the live case marked opt-in.
