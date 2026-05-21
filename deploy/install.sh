#!/usr/bin/env bash
# install.sh — deploy inventor-monitor from GitHub

set -euo pipefail

GITHUB_RAW="https://raw.githubusercontent.com/rysavy-ondrej/project-inventor/main"

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

download_file() {
    local url="$1" dest="$2" executable="${3:-false}"
    mkdir -p "$(dirname "$dest")"
    if command -v curl &>/dev/null; then
        curl -fsSL "$url" -o "$dest"
    else
        wget -qO "$dest" "$url"
    fi
#    [[ "$executable" == "true" ]] && chmod +x "$dest"
}

# ---------------------------------------------------------------------------
# Prompt for install prefix
# ---------------------------------------------------------------------------

DEFAULT_PREFIX="./inventor-monitor"
read -r -p "Target folder [${DEFAULT_PREFIX}]: " PREFIX
PREFIX="${PREFIX:-$DEFAULT_PREFIX}"
PREFIX="${PREFIX%/}"

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
# 1. src/ — monitoring test-case modules (Python files only)
# ---------------------------------------------------------------------------

info "Downloading monitoring modules (src/) ..."

PYTHON_FILES=(
    network/network.dns/network_dns.py
    network/network.dns/monitor_dns.py
    network/network.ftp/network_ftp.py
    network/network.ftp/monitor_ftp.py
    network/network.imap/network_imap.py
    network/network.imap/monitor_imap.py
    network/network.mqtt/network_mqtt.py
    network/network.mqtt/monitor_mqtt.py
    network/network.ntp/network_ntp.py
    network/network.ntp/monitor_ntp.py
    network/network.ping/network_ping.py
    network/network.ping/monitor_ping.py
    network/network.smtp/network_smtp.py
    network/network.smtp/monitor_smtp.py
    network/network.snmp/network_snmp.py
    network/network.snmp/monitor_snmp.py
    network/network.traceroute/network_traceroute.py
    network/network.traceroute/monitor_traceroute.py
    other/other.nosql/nosql.py
    other/other.nosql/db_factory.py
    other/other.nosql/monitor_nosql.py
    other/other.sql/sql_db.py
    other/other.sql/db_factory.py
    other/other.sql/monitor_sql.py
    performance/performance.bandwidth/performance.bandwidth.client.py
    performance/performance.bandwidth/performance.bandwidth.server.py
    security/security.ldap/security_ldap.py
    security/security.ldap/monitor_ldap.py
    security/security.ssh/security_ssh.py
    security/security.ssh/monitor_ssh.py
    security/security.tls/security_tls.py
    security/security.tls/monitor_tls.py
    webapp/webapp.dynamic/monitor_webapp_dynamic_analysis.py
    webapp/webapp.http/webapp_http.py
    webapp/webapp.http/test_http.py
    webapp/webapp.rest/webapp_rest.py
    webapp/webapp.rest/test_rest.py
    webapp/webapp.security/webapp_security.py
    webapp/webapp.security/test_security.py
    common/dummy/dummy.py
)

for rel in "${PYTHON_FILES[@]}"; do
    info "  $rel"
    download_file "${GITHUB_RAW}/src/${rel}" "$PREFIX/src/${rel}"
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
# 3. etc/ — schedule templates + Python requirements
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
# 3b. src/requirements.txt — Python dependencies
# ---------------------------------------------------------------------------

info "Downloading Python requirements ..."
download_file "${GITHUB_RAW}/deploy/inventor-requirements.txt" "$PREFIX/src/requirements.txt"

success "Requirements file installed to $PREFIX/src/requirements.txt"

# ---------------------------------------------------------------------------
# 4. var/ — output directory (created above)
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
echo "Install Python dependencies:"
echo "  pip install -r $PREFIX/src/requirements.txt"
echo ""
echo "Quick start:"
echo "  pwsh $PREFIX/bin/Run-MonitorSession.ps1 -TestSuiteFile $PREFIX/etc/<schedule>.yaml -OutPath $PREFIX/var/"
echo "  # or run all schedules:"
echo "  bash $PREFIX/bin/inventor-testbed.run-all.sh $PREFIX/etc/ $PREFIX/var/"
echo ""

# ---------------------------------------------------------------------------
# Optional: create Python virtual environment and install requirements
# ---------------------------------------------------------------------------

read -r -p "Create a Python virtual environment and install requirements? [y/N]: " create_venv
if [[ "${create_venv,,}" == "y" ]]; then
    VENV_DIR="$PREFIX/venv"
    info "Creating virtual environment at $VENV_DIR ..."
    python3 -m venv "$VENV_DIR"
    success "Virtual environment created"

    info "Installing requirements ..."
    "$VENV_DIR/bin/pip" install --upgrade pip --quiet
    "$VENV_DIR/bin/pip" install -r "$PREFIX/src/requirements.txt"
    success "Requirements installed"

    echo ""
    echo "Activate the environment before running tests:"
    echo "  source $VENV_DIR/bin/activate"
    echo ""
fi

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
        info "To start later: sudo systemctl enable --now ${SERVICE_NAME}"
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
