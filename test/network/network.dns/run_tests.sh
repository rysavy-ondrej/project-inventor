#!/usr/bin/env bash
#
# Self-contained test runner for the network.dns monitor.
#
# Creates a throwaway virtual environment, installs the monitor's pinned
# requirements into it, then executes the DNS test cases under inputs/ and
# writes results to outputs/.
#
# Usage:  ./run_tests.sh
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$HERE/../../.." && pwd)"
REQUIREMENTS="$REPO_ROOT/src/network/network.dns/requirements.txt"

VENV_DIR="$(mktemp -d -t network-dns-test-XXXXXX)"
cleanup() { rm -rf "$VENV_DIR"; }
trap cleanup EXIT

echo ">> Creating virtual environment in $VENV_DIR"
python3 -m venv "$VENV_DIR"

echo ">> Installing requirements from $REQUIREMENTS"
"$VENV_DIR/bin/pip" install -q --disable-pip-version-check -r "$REQUIREMENTS"

echo ">> Running DNS test cases"
"$VENV_DIR/bin/python" "$HERE/run_dns_tests.py"
