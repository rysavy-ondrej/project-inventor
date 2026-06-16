#!/usr/bin/env python3
#
# Materialized test harness for src/network/network.dns.
#
# Loads every JSON config under inputs/, runs the real monitor entry point
# network_dns.run() against live DNS, and writes the result to
# outputs/<name>.json. Exercises several query types (A, AAAA, NS, PTR) plus
# two negative cases: a per-domain NXDOMAIN failure (still completes, counted
# in summary.failed_tests) and a top-level invalid query_type (status=error).
#
# run() is pure dnspython with no packet capture, so it is called directly and
# needs no elevated privileges.
#
import os
import sys
import json
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
# test/network/network.dns -> repo root is three levels up.
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
MODULE_DIR = os.path.join(REPO_ROOT, "src", "network", "network.dns")
INPUT_DIR = os.path.join(HERE, "inputs")
OUTPUT_DIR = os.path.join(HERE, "outputs")

sys.path.insert(0, MODULE_DIR)
from network_dns import run  # noqa: E402

# Keys that are test metadata, not part of the monitor's config schema.
META_KEYS = ("_comment", "expect_status", "expect_failed_tests",
             "expect_successful_tests")


def run_case(path, run_id):
    name = os.path.splitext(os.path.basename(path))[0]
    with open(path) as f:
        cfg = json.load(f)

    expect_status = cfg.get("expect_status", "completed")
    expect_failed = cfg.get("expect_failed_tests")
    expect_ok = cfg.get("expect_successful_tests")
    params = {k: v for k, v in cfg.items() if k not in META_KEYS}

    res = run(params, run_id)

    out_path = os.path.join(OUTPUT_DIR, name + ".json")
    with open(out_path, "w") as f:
        json.dump(res, f, indent=4)

    summary = res.get("summary") or {}
    failures = []
    status = res.get("status")
    if status != expect_status:
        failures.append(f"status={status!r} expected {expect_status!r}")
    if expect_failed is not None and summary.get("failed_tests") != expect_failed:
        failures.append(f"failed_tests={summary.get('failed_tests')} expected {expect_failed}")
    if expect_ok is not None and summary.get("successful_tests") != expect_ok:
        failures.append(f"successful_tests={summary.get('successful_tests')} expected {expect_ok}")

    ok = not failures
    return ok, {
        "name": name,
        "query_type": params.get("query_type"),
        "hosts": params.get("target_hosts"),
        "status": status,
        "summary": summary,
        "error": res.get("error"),
        "output_file": os.path.relpath(out_path, REPO_ROOT),
        "result": "PASS" if ok else "FAIL",
        "failures": failures,
    }


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    inputs = sorted(glob.glob(os.path.join(INPUT_DIR, "*.json")))
    if not inputs:
        print("No input configs found in", INPUT_DIR)
        return 1

    all_ok = True
    print(f"Running {len(inputs)} DNS test case(s)\n" + "=" * 60)
    for i, path in enumerate(inputs, 1):
        ok, s = run_case(path, i)
        all_ok = all_ok and ok
        print(f"[{s['result']}] {s['name']}: {s['query_type']} {s['hosts']}")
        if s["status"] == "completed":
            sm = s["summary"]
            print(f"        -> status=completed  ok={sm.get('successful_tests')}/"
                  f"{sm.get('total_tests')}  failed={sm.get('failed_tests')}  "
                  f"avg={sm.get('response_time_avg')}ms")
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
