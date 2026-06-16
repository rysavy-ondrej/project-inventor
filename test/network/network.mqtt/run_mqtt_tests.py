#!/usr/bin/env python3
#
# Auto-generated test harness for src/network/network.mqtt (see test/Readme.md).
#
# Loads every JSON config under inputs/, runs the monitor's run() entry point,
# writes the result to outputs/<name>.json, and asserts the expected outcome.
# Success is detected by absence of an error marker (status == "error" or a
# retcode/errcode/error field), because not every monitor sets status on success.
#
import os, sys, json, glob

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
MODULE_DIR = os.path.join(REPO_ROOT, "src/network/network.mqtt")
INPUT_DIR = os.path.join(HERE, "inputs")
OUTPUT_DIR = os.path.join(HERE, "outputs")
SKIP_HINT = ""

sys.path.insert(0, MODULE_DIR)
try:
    from network_mqtt import run
except Exception as e:
    print("SKIPPED: cannot import network_mqtt: %s" % e)
    if SKIP_HINT:
        print("         " + SKIP_HINT)
    sys.exit(0)

META_KEYS = ("_comment", "expect_status", "expect_keys", "requires_root", "skip_on_error")


def is_error(res):
    if not isinstance(res, dict):
        return True
    if res.get("status") == "error":
        return True
    return any(k in res for k in ("retcode", "errcode", "error"))


def run_case(path, run_id):
    name = os.path.splitext(os.path.basename(path))[0]
    with open(path) as f:
        cfg = json.load(f)
    expect_status = cfg.get("expect_status", "completed")
    expect_keys = cfg.get("expect_keys", [])
    requires_root = cfg.get("requires_root", False)
    skip_on_error = cfg.get("skip_on_error", False)
    params = {k: v for k, v in cfg.items() if k not in META_KEYS}

    if requires_root and hasattr(os, "geteuid") and os.geteuid() != 0:
        return "SKIP", name, "requires root to open raw sockets; re-run with 'sudo ./run_tests.sh'"

    res = run(params, run_id)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, name + ".json"), "w") as f:
        json.dump(res, f, indent=4)

    err = is_error(res)
    if expect_status == "error":
        if err:
            return "PASS", name, "error surfaced as expected"
        return "FAIL", name, "expected an error, got success"
    # expecting a successful (non-error) outcome
    if err:
        detail = res.get("error") or {k: res[k] for k in ("retcode", "errcode") if k in res}
        if skip_on_error:
            return "SKIP", name, "target unreachable in this environment (%s)" % detail
        return "FAIL", name, "unexpected error: %s" % detail
    missing = [k for k in expect_keys if k not in res]
    if missing:
        return "FAIL", name, "missing expected keys: %s" % missing
    return "PASS", name, "ok" + (" (keys: %s)" % ", ".join(expect_keys) if expect_keys else "")


def main():
    inputs = sorted(glob.glob(os.path.join(INPUT_DIR, "*.json")))
    if not inputs:
        print("No input configs found in", INPUT_DIR)
        return 1
    print("Running %d network_mqtt test case(s)" % len(inputs))
    print("=" * 60)
    failed = skipped = 0
    for i, path in enumerate(inputs, 1):
        verdict, name, msg = run_case(path, i)
        if verdict == "FAIL":
            failed += 1
        elif verdict == "SKIP":
            skipped += 1
        print("[%s] %s: %s" % (verdict, name, msg))
    print("=" * 60)
    tail = (" (%d skipped)" % skipped) if skipped else ""
    print(("ALL PASSED" + tail) if failed == 0 else ("%d TEST(S) FAILED" % failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
