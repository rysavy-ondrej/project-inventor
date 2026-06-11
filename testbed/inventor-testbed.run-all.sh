#!/usr/bin/env bash
# run-all-tests.sh

set -euo pipefail

# Resolve this script's own directory so the runner and sink scripts are found
# regardless of the caller's current working directory (e.g. when launched as a
# systemd/launchd service whose WorkingDirectory is the install prefix).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SCHEDULE_DIR="${1:-schedules}"
OUT_DIR="${2:-./out}"

mkdir -p "$OUT_DIR"

echo "Launching test suites from $SCHEDULE_DIR ..."

pids=()

for suite in "$SCHEDULE_DIR"/*.yaml; do
    echo "Starting $suite ..."
    # Use the suite's file name (without extension) as the per-day file base name.
    base="$(basename "$suite" .yaml)"
    # Pipe the session's result stream into the file sink (one file per day).
    pwsh -Command "& '$SCRIPT_DIR/Run-MonitorSession.ps1' -TestSuiteFile '$suite' | & '$SCRIPT_DIR/Out-FileByDay.ps1' -BaseName '$base' -OutPath '$OUT_DIR'" &
    pids+=($!)
done

echo "All tests started, waiting for them to finish..."

# just wait for all jobs
wait

echo "✅ All monitor sessions finished."
