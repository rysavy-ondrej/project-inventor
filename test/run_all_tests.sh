#!/usr/bin/env bash
#
# Run every monitor test suite sequentially.
#
# Discovers all per-monitor run_tests.sh scripts under test/ (network/ and
# security/), runs them one at a time, and prints a pass/fail summary. Each
# suite builds its own throwaway virtual environment, so they are independent.
#
# Privileged suites (network.ping, network.traceroute) skip their live cases
# when not run as root; run with 'sudo ./run_all_tests.sh' to execute those too.
#
# Usage:  ./run_all_tests.sh
#
# Exits non-zero if any suite fails.
#
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Collect every per-monitor runner, excluding this orchestrator, sorted for a
# stable, deterministic run order.
mapfile -t SUITES < <(find "$HERE" -mindepth 2 -name run_tests.sh -type f | sort)

if [ "${#SUITES[@]}" -eq 0 ]; then
    echo "No run_tests.sh suites found under $HERE" >&2
    exit 1
fi

passed=()
failed=()

for suite in "${SUITES[@]}"; do
    name="$(basename "$(dirname "$suite")")"
    echo
    echo "============================================================"
    echo ">> RUNNING $name  ($suite)"
    echo "============================================================"
    if bash "$suite"; then
        passed+=("$name")
    else
        failed+=("$name")
    fi
done

echo
echo "============================================================"
echo ">> SUMMARY"
echo "============================================================"
echo "Passed (${#passed[@]}):"
for n in "${passed[@]}"; do echo "  [PASS] $n"; done
echo "Failed (${#failed[@]}):"
for n in "${failed[@]}"; do echo "  [FAIL] $n"; done

if [ "${#failed[@]}" -ne 0 ]; then
    exit 1
fi
echo
echo ">> All ${#passed[@]} suites passed."
