#!/usr/bin/env bash
# install.sh — deploy inventor-monitor from GitHub

set -euo pipefail

GITHUB_RAW="https://raw.githubusercontent.com/rysavy-ondrej/project-inventor/main"
GITHUB_API="https://api.github.com/repos/rysavy-ondrej/project-inventor/contents"

SERVICE_NAME="inventor-monitor"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

info()    { echo "[INFO]  $*"; }
success() { echo "[OK]    $*"; }
warn()    { echo "[WARN]  $*"; }
error()   { echo "[ERROR] $*" >&2; exit 1; }

require_cmd() {
    command -v "$1" &>/dev/null || error "Required command not found: $1"
}

# Download a single file, optionally marking it executable.
download_file() {
    local url="$1" dest="$2" executable="${3:-false}"
    mkdir -p "$(dirname "$dest")"
    if command -v curl &>/dev/null; then
        curl -fsSL "$url" -o "$dest"
    else
        wget -qO "$dest" "$url"
    fi
    [[ "$executable" == "true" ]] && chmod +x "$dest"
}

# Recursively download *.py files under a GitHub contents path into a local dir.
download_tree() {
    local api_path="$1" local_dir="$2"
    local entries parsed

    if ! entries=$(curl -fsSL "${GITHUB_API}/${api_path}" 2>/dev/null); then
        warn "Failed to fetch listing for ${api_path}"
        return
    fi

    # Single Python call: emit one "type\tname\turl" line per entry.
    # Directories have download_url=null, so we emit an empty url for them.
    parsed=$(echo "$entries" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    sys.exit(1)
for e in data:
    print(e['type'] + '\t' + e['name'] + '\t' + (e.get('download_url') or ''))
") || { warn "Failed to parse listing for ${api_path}"; return; }

    # Use a here-string (not a pipe) so the while loop runs in the current shell,
    # keeping recursive curl calls out of the pipe's stdin.
    while IFS=$'\t' read -r etype ename edl; do
        if [[ "$etype" == "file" && "$ename" == *.py && -n "$edl" ]]; then
            info "  $api_path/$ename"
            download_file "$edl" "$local_dir/$ename"
        elif [[ "$etype" == "dir" ]]; then
            download_tree "$api_path/$ename" "$local_dir/$ename"
        fi
    done <<< "$parsed"
}

# ---------------------------------------------------------------------------
# Prompt for install prefix
# ---------------------------------------------------------------------------

DEFAULT_PREFIX="./inventor-monitor"
read -r -p "Target folder [${DEFAULT_PREFIX}]: " PREFIX
PREFIX="${PREFIX:-$DEFAULT_PREFIX}"
PREFIX="${PREFIX%/}"

# Resolve to absolute path (create it first so realpath/cd works).
mkdir -p "$PREFIX"
PREFIX=$(cd "$PREFIX" && pwd)

info "Installing to: $PREFIX"

# ---------------------------------------------------------------------------
# Verify dependencies
# ---------------------------------------------------------------------------

require_cmd python3
command -v curl &>/dev/null || require_cmd wget

# ---------------------------------------------------------------------------
# Create directory layout
# ---------------------------------------------------------------------------

for dir in src bin etc var; do
    mkdir -p "$PREFIX/$dir"
done

success "Directory layout created"

# ---------------------------------------------------------------------------
# 1. src/ — monitoring test-case modules
# ---------------------------------------------------------------------------

info "Downloading monitoring modules (src/) ..."

for module in \
    network/network.dns        \
    network/network.ftp        \
    network/network.imap       \
    network/network.mqtt       \
    network/network.ntp        \
    network/network.ping       \
    network/network.smtp       \
    network/network.snmp       \
    network/network.traceroute \
    other/other.nosql          \
    other/other.sql            \
    performance/performance.bandwidth \
    security/security.ldap     \
    security/security.ssh      \
    security/security.tls      \
    webapp/webapp.dynamic      \
    webapp/webapp.http         \
    webapp/webapp.rest         \
    webapp/webapp.security     \
    common/dummy
do
    download_tree "src/$module" "$PREFIX/src/$module"
done

success "Monitoring modules installed to $PREFIX/src/"

# ---------------------------------------------------------------------------
# 2. bin/ — testbed runner scripts
# ---------------------------------------------------------------------------

info "Downloading runner scripts (bin/) ..."

for script in \
    Run-MonitorSession.ps1       \
    inventor-testbed.run-all.sh  \
    inventor-testbed.kill-all.sh
do
    info "  $script"
    download_file "${GITHUB_RAW}/testbed/${script}" "$PREFIX/bin/$script" true
done

success "Scripts installed to $PREFIX/bin/"

# ---------------------------------------------------------------------------
# 3. etc/ — schedule configuration pre-populated from minimal templates
# ---------------------------------------------------------------------------

info "Downloading schedule templates (etc/) ..."

for template in \
    network.dns.yaml         \
    network.imap.yaml        \
    network.ntp.yaml         \
    network.ping.yaml        \
    network.smtp.yaml        \
    network.snmp.yaml        \
    network.traceroute.yaml  \
    security.ldap.yaml       \
    security.ssh.yaml        \
    security.tls.yaml        \
    webapp.http.yaml         \
    webapp.http.dynamic.yaml
do
    dest="$PREFIX/etc/$template"
    if [[ -f "$dest" ]]; then
        info "  (skipping $template — already exists)"
    else
        info "  $template"
        download_file "${GITHUB_RAW}/src/templates/${template}" "$dest"
    fi
done

success "Schedule templates installed to $PREFIX/etc/"

# ---------------------------------------------------------------------------
# 4. var/ — output directory (empty, created above)
# ---------------------------------------------------------------------------

success "Output directory ready at $PREFIX/var/"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo ""
echo "============================================================"
echo "  inventor-monitor deployed to: $PREFIX"
echo "============================================================"
echo "  Monitoring modules : $PREFIX/src/"
echo "  Runner scripts     : $PREFIX/bin/"
echo "  Schedule configs   : $PREFIX/etc/    (edit before running)"
echo "  Monitor output     : $PREFIX/var/"
echo ""
echo "Quick start:"
echo "  pwsh $PREFIX/bin/Run-MonitorSession.ps1 -TestSuiteFile $PREFIX/etc/<schedule>.yaml -OutPath $PREFIX/var/"
echo "  # or run all schedules:"
echo "  bash $PREFIX/bin/inventor-testbed.run-all.sh $PREFIX/etc/ $PREFIX/var/"
echo ""

# ---------------------------------------------------------------------------
# Optional: install as system service
# ---------------------------------------------------------------------------

read -r -p "Install inventor-monitor as a system service? [y/N]: " install_svc
[[ "${install_svc,,}" != "y" ]] && exit 0

require_cmd pwsh

OS=$(uname -s)
case "$OS" in
    Linux)  INIT_SYS="systemd" ;;
    Darwin) INIT_SYS="launchd" ;;
    *)      error "System service installation is not supported on $OS" ;;
esac

info "Detected init system: $INIT_SYS"

# ---------------------------------------------------------------------------
# systemd (Linux)
# ---------------------------------------------------------------------------

install_systemd_service() {
    local prefix="$1"
    local unit_file="/etc/systemd/system/${SERVICE_NAME}.service"

    # Run as the invoking user (not root) even when the script is sudo'd.
    local run_user="${SUDO_USER:-$(whoami)}"

    info "Writing unit file: $unit_file"

    local tmp_unit
    tmp_unit=$(mktemp)
    cat > "$tmp_unit" <<EOF
[Unit]
Description=Inventor Monitor Service
Documentation=https://github.com/rysavy-ondrej/project-inventor
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${run_user}
WorkingDirectory=${prefix}
ExecStart=/usr/bin/env bash ${prefix}/bin/inventor-testbed.run-all.sh ${prefix}/etc/ ${prefix}/var/
Restart=on-failure
RestartSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    if [[ $EUID -ne 0 ]]; then
        sudo cp "$tmp_unit" "$unit_file"
        sudo systemctl daemon-reload
    else
        cp "$tmp_unit" "$unit_file"
        systemctl daemon-reload
    fi
    rm -f "$tmp_unit"

    success "Unit file installed: $unit_file"

    read -r -p "Enable and start the service now? [y/N]: " start_now
    if [[ "${start_now,,}" == "y" ]]; then
        if [[ $EUID -ne 0 ]]; then
            sudo systemctl enable --now "$SERVICE_NAME"
        else
            systemctl enable --now "$SERVICE_NAME"
        fi
        success "Service enabled and started"
    else
        info "To start later:"
        info "  sudo systemctl enable --now ${SERVICE_NAME}"
    fi

    echo ""
    echo "Useful commands:"
    echo "  sudo systemctl status  ${SERVICE_NAME}"
    echo "  sudo systemctl restart ${SERVICE_NAME}"
    echo "  sudo systemctl stop    ${SERVICE_NAME}"
    echo "  sudo journalctl -u     ${SERVICE_NAME} -f"
}

# ---------------------------------------------------------------------------
# launchd (macOS)
# ---------------------------------------------------------------------------

install_launchd_service() {
    local prefix="$1"
    local label="${SERVICE_NAME}"

    echo ""
    echo "Service scope:"
    echo "  1) User   — ~/Library/LaunchAgents   (starts on login, no sudo needed)"
    echo "  2) System — /Library/LaunchDaemons   (starts at boot, requires sudo)"
    read -r -p "Choice [1]: " scope
    scope="${scope:-1}"

    local plist_dir plist_file use_sudo=false
    if [[ "$scope" == "2" ]]; then
        plist_dir="/Library/LaunchDaemons"
        use_sudo=true
    else
        plist_dir="${HOME}/Library/LaunchAgents"
    fi
    plist_file="${plist_dir}/${label}.plist"
    mkdir -p "$plist_dir"

    local run_user
    run_user=$(whoami)

    info "Writing plist: $plist_file"

    local tmp_plist
    tmp_plist=$(mktemp)
    cat > "$tmp_plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${label}</string>
    <key>UserName</key>
    <string>${run_user}</string>
    <key>WorkingDirectory</key>
    <string>${prefix}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/env</string>
        <string>bash</string>
        <string>${prefix}/bin/inventor-testbed.run-all.sh</string>
        <string>${prefix}/etc/</string>
        <string>${prefix}/var/</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    <key>StandardOutPath</key>
    <string>${prefix}/var/${label}.log</string>
    <key>StandardErrorPath</key>
    <string>${prefix}/var/${label}.err</string>
</dict>
</plist>
EOF

    if [[ "$use_sudo" == "true" ]]; then
        sudo cp "$tmp_plist" "$plist_file"
        sudo chown root:wheel "$plist_file"
        sudo chmod 644 "$plist_file"
    else
        cp "$tmp_plist" "$plist_file"
    fi
    rm -f "$tmp_plist"

    success "Plist installed: $plist_file"

    read -r -p "Load and start the service now? [y/N]: " start_now
    if [[ "${start_now,,}" == "y" ]]; then
        if [[ "$use_sudo" == "true" ]]; then
            sudo launchctl load -w "$plist_file"
        else
            launchctl load -w "$plist_file"
        fi
        success "Service loaded and started"
    else
        if [[ "$use_sudo" == "true" ]]; then
            info "To start later: sudo launchctl load -w $plist_file"
        else
            info "To start later: launchctl load -w $plist_file"
        fi
    fi

    echo ""
    echo "Useful commands:"
    echo "  launchctl list | grep ${label}"
    echo "  launchctl stop  ${label}"
    echo "  launchctl start ${label}"
    echo "  tail -f ${prefix}/var/${label}.log"
}

# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

case "$INIT_SYS" in
    systemd) install_systemd_service "$PREFIX" ;;
    launchd) install_launchd_service "$PREFIX" ;;
esac
