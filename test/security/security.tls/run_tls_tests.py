#!/usr/bin/env python3
#
# Materialized test harness for src/security/security.tls.
#
# Loads every JSON config under inputs/, runs the real TLS handshake from
# security_tls.perform_tls_handshake against the live target, and writes the
# result to outputs/<name>.json. Exercises both TLSv1.2 (set_cipher_list path)
# and TLSv1.3 (SSL_CTX_set_ciphersuites FFI path), plus a negative case that
# must be rejected.
#
# perform_tls_handshake is called directly rather than security_tls.run() so
# the test does not require root for the scapy packet-capture (sniff) path,
# which is orthogonal to the cipher/version logic under test.
#
import os
import sys
import json
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
# test/security/security.tls -> repo root is three levels up.
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
MODULE_DIR = os.path.join(REPO_ROOT, "src", "security", "security.tls")
INPUT_DIR = os.path.join(HERE, "inputs")
OUTPUT_DIR = os.path.join(HERE, "outputs")

sys.path.insert(0, MODULE_DIR)
from security_tls import perform_tls_handshake  # noqa: E402

# Keys that are test metadata, not part of the monitor's config schema.
META_KEYS = ("_comment", "expect_status", "expect_cipher")


def run_case(path, run_id):
    name = os.path.splitext(os.path.basename(path))[0]
    with open(path) as f:
        cfg = json.load(f)

    expect_status = cfg.get("expect_status", "completed")
    expect_cipher = cfg.get("expect_cipher")
    params = {k: v for k, v in cfg.items() if k not in META_KEYS}

    res = perform_tls_handshake(
        run_id,
        params["target_host"],
        params["target_port"],
        params["tls_version"],
        params["cipher_suites"],
        params.get("elliptic_curves", []),
        params.get("extensions", []),
        params["timeout"],
    )

    out_path = os.path.join(OUTPUT_DIR, name + ".json")
    with open(out_path, "w") as f:
        json.dump(res, f, indent=4)

    # Evaluate expectations.
    status = res.get("status")
    failures = []
    if status != expect_status:
        failures.append(f"status={status!r} expected {expect_status!r}")
    # For TLS 1.3, requested cipher == negotiated cipher proves enforcement.
    requested = params["cipher_suites"]
    if status == "completed" and len(requested) == 1:
        negotiated = res.get("cipher_suite")
        want = expect_cipher or requested[0]
        if negotiated != want:
            failures.append(f"cipher={negotiated!r} expected {want!r}")

    ok = not failures
    summary = {
        "name": name,
        "host": params["target_host"],
        "tls_version": params["tls_version"],
        "requested_cipher": requested,
        "status": status,
        "negotiated_version": res.get("tls_version"),
        "negotiated_cipher": res.get("cipher_suite"),
        "handshake_time_ms": res.get("handshake_time"),
        "error": res.get("error"),
        "output_file": os.path.relpath(out_path, REPO_ROOT),
        "result": "PASS" if ok else "FAIL",
        "failures": failures,
    }
    return ok, summary


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    inputs = sorted(glob.glob(os.path.join(INPUT_DIR, "*.json")))
    if not inputs:
        print("No input configs found in", INPUT_DIR)
        return 1

    all_ok = True
    print(f"Running {len(inputs)} TLS test case(s)\n" + "=" * 60)
    for i, path in enumerate(inputs, 1):
        ok, s = run_case(path, i)
        all_ok = all_ok and ok
        line = (f"[{s['result']}] {s['name']}: {s['host']} {s['tls_version']} "
                f"req={s['requested_cipher']}")
        print(line)
        if s["status"] == "completed":
            print(f"        -> {s['negotiated_version']} / {s['negotiated_cipher']} "
                  f"({s['handshake_time_ms']} ms)")
        else:
            desc = (s["error"] or {}).get("description") if isinstance(s["error"], dict) else s["error"]
            print(f"        -> status={s['status']}  {desc}")
        if s["failures"]:
            print(f"        !! {'; '.join(s['failures'])}")
        print(f"        wrote {s['output_file']}")

    print("=" * 60)
    print("ALL PASSED" if all_ok else "SOME TESTS FAILED")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
