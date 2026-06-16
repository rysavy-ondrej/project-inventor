# Monitor tests

This folder holds self-contained, runnable tests for the monitors in
[`src/`](../src). Each test builds a throwaway virtual environment from the
monitor's own pinned requirements, runs the monitor against several real
targets using JSON configs, writes the results back as JSON, and asserts
expectations.

[`security/security.tls`](security/security.tls) is the reference
implementation — read it alongside these instructions.

---

## Instructions for creating a new monitor test

Follow these steps when asked to create a test for an existing monitor from
`src/`. The goal is a directory that anyone (or any agent) can run with a single
`./run_tests.sh` and get a clear pass/fail plus captured input/output JSONs.

### 1. Mirror the source path

Monitors live at `src/<group>/<group>.<name>/` (e.g.
`src/security/security.tls`, `src/network/network.dns`). Create the test at the
**same relative path** under `test/`:

```
src/<group>/<group>.<name>/        ->  test/<group>/<group>.<name>/
```

Create this structure inside it:

```
test/<group>/<group>.<name>/
├── Readme.md            # short per-monitor doc: layout, how to run, case table
├── run_tests.sh         # builds the venv, installs requirements, runs the suite
├── run_<name>_tests.py  # loads inputs/, runs the monitor, writes outputs/, asserts
├── inputs/              # one JSON config per case (committed)
│   └── *.json
└── outputs/             # generated results, one per input (committed)
    └── *.json
```

### 2. Learn the monitor's contract

Before writing configs, read the source so the test matches reality:

- **Entry point.** Every monitor's core module
  `src/<group>/<group>.<name>/<group>_<name>.py` exposes
  `run(params: dict, run_id: int, queue: Queue = None) -> dict`. `params` is the
  per-target config; the return value is the result dict (status + fields).
- **Config schema.** Derive the required keys from `run()` (the `params.get(...)`
  / `raise ValueError(...)` block near the top of `run()`) and from the existing
  `src/<group>/<group>.<name>/test/input.json`, which is a known-good example.
- **Result schema.** Note the keys the monitor sets on success (e.g.
  `status`, plus monitor-specific fields) and on failure (`status: "error"`
  with an `error` object). Your assertions key off these.

### 3. Decide how to invoke the monitor

Prefer calling the public **`run(config, run_id)`** entry point — it is the most
faithful test and needs no special handling for most monitors.

**Exception — privileged capture paths.** Some monitors (e.g. `security.tls`,
and anything using `scapy.sniff` or raw sockets) start a packet capture inside
`run()` that requires **root**. To keep the test runnable unprivileged, import
and call the core probe function directly instead (for TLS that is
`perform_tls_handshake`), bypassing the capture. When you do this, add a comment
explaining *why* and note that the skipped path is orthogonal to what is being
tested. If a monitor genuinely cannot be exercised without root, say so in its
Readme and make `run_tests.sh` fail loudly with that explanation.

### 4. Write the input configs (`inputs/*.json`)

- One file per case; name it for what it exercises (e.g. `tls12_google.json`).
- Use **several real, stable, public targets**, and cover the meaningful
  variations of the monitor (protocol versions, options, address families).
- Always include at least one **negative case** that must fail, to prove errors
  are surfaced rather than swallowed.
- A config is the monitor's normal `params` plus optional **test-only metadata
  keys**, which the runner strips before calling the monitor:
  - `_comment` — free-text note on the case's intent.
  - `expect_status` — expected `status` (default `"completed"`).
  - `expect_*` — any other expected result field to assert (e.g. for TLS,
    `expect_cipher`); add per monitor as needed.

### 5. Write the Python runner (`run_<name>_tests.py`)

- Resolve the repo root from `__file__` (do not hardcode paths), then
  `sys.path.insert(0, <module dir>)` and import the monitor.
- For each `inputs/*.json`: load it, split off the metadata keys, invoke the
  monitor, write the full result to `outputs/<case>.json` (indented).
- Assert `status == expect_status` and any `expect_*` fields. For monitors that
  echo a negotiated/observed value back (like TLS ciphers), assert the observed
  value equals the requested one — that proves the config was *enforced*, not
  ignored.
- Print a one-line `[PASS]/[FAIL]` per case and exit non-zero if any fail.

### 6. Write the shell harness (`run_tests.sh`)

Use the reference verbatim where possible — it must:

- `set -euo pipefail` and resolve paths relative to the script.
- `mktemp -d` a venv dir, `python3 -m venv` it, and `trap` cleanup on exit.
- `pip install -r src/<group>/<group>.<name>/requirements.txt` (the monitor's
  own pinned deps — never invent versions).
- Run `run_<name>_tests.py` with the venv's Python.

### 7. Run it and commit the results

```sh
chmod +x test/<group>/<group>.<name>/run_tests.sh test/<group>/<group>.<name>/run_<name>_tests.py
./test/<group>/<group>.<name>/run_tests.sh
```

Confirm every case behaves as expected (including the negative one), then commit
the `inputs/` **and** the generated `outputs/` so the captured results are part
of the record. Write the per-monitor `Readme.md` with the layout, the run
command, the root caveat (if any), and a table of cases and expectations.

---

## Conventions summary

| Concern | Rule |
|---------|------|
| Location | `test/<group>/<group>.<name>/` mirrors the source path |
| Dependencies | a temp venv built from the monitor's own `requirements.txt` |
| Invocation | `run(config, run_id)` by default; core probe fn directly only to avoid root |
| Targets | several real public hosts + at least one negative case |
| Metadata keys | `_comment`, `expect_status`, `expect_*` (stripped before the monitor sees them) |
| Artifacts | commit both `inputs/` and generated `outputs/` |
| Network | tests hit live targets, so a network connection is required |
