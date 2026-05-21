#!/usr/bin/env bash
# run-all-tests.sh

set -euo pipefail

SCHEDULE_DIR="${1:-schedules}"
OUT_DIR="${2:-./out}"

mkdir -p "$OUT_DIR"

echo "Launching test suites from $SCHEDULE_DIR ..."

pids=()

for suite in "$SCHEDULE_DIR"/*.yaml; do
    echo "Starting $suite ..."
    pwsh Run-MonitorSession.ps1 -TestSuiteFile "$suite" -OutPath "$OUT_DIR" &
    pids+=($!)
done

echo "All tests started, waiting for them to finish..."

# just wait for all jobs
wait

echo "✅ All monitor sessions finished."
