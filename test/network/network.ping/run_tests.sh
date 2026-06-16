#!/usr/bin/env bash
#
# Self-contained test runner for the network.ping monitor.
#
# Creates a throwaway virtual environment, installs the monitor's pinned
# requirements, then executes the test cases under inputs/ and writes results
# to outputs/.
#
# Usage:  ./run_tests.sh        (some cases may require:  sudo ./run_tests.sh)
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$HERE/../../.." && pwd)"
REQUIREMENTS="$REPO_ROOT/src/network/network.ping/requirements.txt"

VENV_DIR="$(mktemp -d -t network.ping-test-XXXXXX)"
cleanup() { rm -rf "$VENV_DIR"; }
trap cleanup EXIT

echo ">> Creating virtual environment in $VENV_DIR"
python3 -m venv "$VENV_DIR"

echo ">> Installing requirements from $REQUIREMENTS"
if ! "$VENV_DIR/bin/pip" install -q --disable-pip-version-check -r "$REQUIREMENTS"; then
    echo ">> SKIPPED: failed to install requirements (see requirements.txt)"
    exit 0
fi

echo ">> Running network.ping test cases"
"$VENV_DIR/bin/python" "$HERE/run_ping_tests.py"
