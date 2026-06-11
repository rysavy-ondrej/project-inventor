#!/usr/bin/env bash
# install.sh — deploy inventor-monitor from GitHub

set -euo pipefail

# ---------------------------------------------------------------------------
# Require bash 4+ (associative arrays, ${var,,}, fractional read timeouts).
# macOS ships bash 3.2 by default — install a newer one (e.g. `brew install bash`)
# and re-run with it.
# ---------------------------------------------------------------------------

if [[ -z "${BASH_VERSINFO:-}" || "${BASH_VERSINFO[0]}" -lt 4 ]]; then
    echo "[ERROR] This installer requires bash 4.0 or newer (found ${BASH_VERSION:-unknown})." >&2
    echo "        On macOS:  brew install bash, then run:  \$(brew --prefix)/bin/bash $0" >&2
    exit 1
fi

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
    [[ "$executable" == "true" ]] && chmod +x "$dest"
    info "  ok"
}

# ---------------------------------------------------------------------------
# Interactive UI helpers (pure bash, no external dependencies)
#
# These render arrow-key driven menus directly on the controlling terminal,
# so they keep working even when the script is piped (curl ... | bash). When
# no terminal is available they fall back to sensible defaults.
# ---------------------------------------------------------------------------

if [[ -r /dev/tty ]] && [[ -t 1 ]]; then
    UI_TTY=/dev/tty
else
    UI_TTY=""
fi

ui_interactive() { [[ -n "$UI_TTY" ]]; }

# Read a single keypress, expanding escape sequences (arrow keys) into a
# stable token printed on stdout.
ui_read_key() {
    local key="" rest=""
    IFS= read -rsn1 key < "$UI_TTY" || return 1
    # An escape byte starts an arrow-key sequence (ESC [ A/B/C/D); grab the
    # two trailing bytes. The short timeout lets a lone Esc keypress fall through.
    if [[ "$key" == $'\x1b' ]]; then
        IFS= read -rsn2 -t 0.05 rest < "$UI_TTY" || true
        key+="$rest"
    fi
    printf '%s' "$key"
}

ui_hide_cursor() { printf '\033[?25l' > "$UI_TTY"; }
ui_show_cursor() { printf '\033[?25h' > "$UI_TTY"; }

# ui_menu TITLE DEFAULT_INDEX OPTION...
# Single choice. Result in UI_RESULT (value) and UI_RESULT_INDEX.
ui_menu() {
    local title="$1"; shift
    local cur="$1"; shift
    local opts=("$@")
    local n=${#opts[@]}
    (( cur < 0 || cur >= n )) && cur=0

    printf '%s\n' "$title" > "$UI_TTY"
    printf '  \033[2m(↑/↓ to move · Enter to select)\033[0m\n' > "$UI_TTY"
    ui_hide_cursor
    trap 'ui_show_cursor' RETURN

    local first=1 i key
    while true; do
        (( first == 0 )) && printf '\033[%dA' "$n" > "$UI_TTY"
        first=0
        for ((i = 0; i < n; i++)); do
            printf '\r\033[K' > "$UI_TTY"
            if (( i == cur )); then
                printf '  \033[7m ❯ %s \033[0m\n' "${opts[i]}" > "$UI_TTY"
            else
                printf '    %s\n' "${opts[i]}" > "$UI_TTY"
            fi
        done
        key=$(ui_read_key)
        case "$key" in
            $'\x1b[A'|k) (( cur = (cur - 1 + n) % n )) ;;
            $'\x1b[B'|j) (( cur = (cur + 1) % n )) ;;
            ''|$'\n')    break ;;
        esac
    done
    UI_RESULT="${opts[cur]}"
    UI_RESULT_INDEX=$cur
    ui_show_cursor
    trap - RETURN
}

# ui_multiselect TITLE OPTION...
# Multiple choice; every option pre-selected. Chosen indices in UI_SELECTED_INDICES.
ui_multiselect() {
    local title="$1"; shift
    local opts=("$@")
    local n=${#opts[@]}
    local cur=0 first=1 i key
    local checked=()
    for ((i = 0; i < n; i++)); do checked[i]=1; done

    printf '%s\n' "$title" > "$UI_TTY"
    printf '  \033[2m(↑/↓ move · Space toggle · a all · n none · Enter confirm)\033[0m\n' > "$UI_TTY"
    ui_hide_cursor
    trap 'ui_show_cursor' RETURN

    while true; do
        (( first == 0 )) && printf '\033[%dA' "$n" > "$UI_TTY"
        first=0
        for ((i = 0; i < n; i++)); do
            printf '\r\033[K' > "$UI_TTY"
            local box="[ ]"
            (( checked[i] == 1 )) && box="[x]"
            if (( i == cur )); then
                printf '  \033[7m ❯ %s %s \033[0m\n' "$box" "${opts[i]}" > "$UI_TTY"
            else
                printf '    %s %s\n' "$box" "${opts[i]}" > "$UI_TTY"
            fi
        done
        key=$(ui_read_key)
        case "$key" in
            $'\x1b[A'|k) (( cur = (cur - 1 + n) % n )) ;;
            $'\x1b[B'|j) (( cur = (cur + 1) % n )) ;;
            ' ')         checked[cur]=$(( 1 - checked[cur] )) ;;
            a|A)         for ((i = 0; i < n; i++)); do checked[i]=1; done ;;
            n|N)         for ((i = 0; i < n; i++)); do checked[i]=0; done ;;
            ''|$'\n')    break ;;
        esac
    done
    UI_SELECTED_INDICES=()
    for ((i = 0; i < n; i++)); do
        (( checked[i] == 1 )) && UI_SELECTED_INDICES+=("$i")
    done
    ui_show_cursor
    trap - RETURN
}

# ui_yesno QUESTION [default:yes|no] -> exit status 0 for yes, 1 for no.
ui_yesno() {
    local q="$1" default="${2:-no}"
    if ! ui_interactive; then
        [[ "$default" == "yes" ]]
        return
    fi
    local di=1
    [[ "$default" == "yes" ]] && di=0
    ui_menu "$q" "$di" "Yes" "No"
    [[ "$UI_RESULT" == "Yes" ]]
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
# Verify build toolchain
#
# Several requirements (notably numpy) are compiled from source on a minimal
# machine that has no prebuilt wheel. That needs a C compiler (gcc) AND the
# Python development headers (python3-dev, which provides Python.h). Test for
# both together up front so the failure surfaces here rather than mid-build.
# ---------------------------------------------------------------------------

check_build_prereqs() {
    local missing=()

    command -v gcc &>/dev/null || missing+=(gcc)

    # python3-dev provides Python.h, used when compiling C extensions.
    local python_h
    python_h="$(python3 -c 'import os, sysconfig; print(os.path.join(sysconfig.get_path("include"), "Python.h"))' 2>/dev/null || true)"
    [[ -n "$python_h" && -f "$python_h" ]] || missing+=(python3-dev)

    if (( ${#missing[@]} == 0 )); then
        success "Build prerequisites present (gcc + Python headers)"
        return 0
    fi

    warn "Missing build prerequisite(s): ${missing[*]}"
    warn "These are required to compile packages such as numpy on a minimal system."

    if command -v apt-get &>/dev/null; then
        echo "  Install with:  sudo apt install ${missing[*]}"
        if ui_yesno "Install the missing build prerequisites now (sudo apt install ${missing[*]})?" yes; then
            sudo apt-get update
            sudo apt-get install -y "${missing[@]}"
            success "Build prerequisites installed"
        else
            warn "Continuing without them — installing Python requirements may fail."
        fi
    else
        warn "Install a C compiler and the Python development headers before installing requirements."
    fi
}

check_build_prereqs

# ---------------------------------------------------------------------------
# Select monitor categories
# ---------------------------------------------------------------------------

# All categories that ship monitoring modules. "common" holds shared helpers
# (e.g. the dummy module) and is always installed regardless of the selection.
ALL_CATEGORIES=(network performance security webapp other)

declare -A CATEGORY_DESC=(
    [network]="DNS, FTP, IMAP, MQTT, NTP, ping, SMTP, SNMP, traceroute probes"
    [performance]="iperf3 bandwidth client/server"
    [security]="LDAP, SSH, TLS probes"
    [webapp]="HTTP, REST and web security probes"
    [other]="SQL and NoSQL database monitors"
)

SELECTED_CATEGORIES=()
if ui_interactive; then
    # Build labelled options ("network — DNS, FTP, ...") aligned to ALL_CATEGORIES.
    cat_labels=()
    for cat in "${ALL_CATEGORIES[@]}"; do
        cat_labels+=("$(printf '%-12s %s' "$cat" "${CATEGORY_DESC[$cat]}")")
    done
    ui_multiselect "Select monitor categories to install:" "${cat_labels[@]}"
    for idx in "${UI_SELECTED_INDICES[@]:-}"; do
        [[ -n "$idx" ]] && SELECTED_CATEGORIES+=("${ALL_CATEGORIES[$idx]}")
    done
    if (( ${#SELECTED_CATEGORIES[@]} == 0 )); then
        warn "No categories selected — installing all."
        SELECTED_CATEGORIES=("${ALL_CATEGORIES[@]}")
    fi
else
    # Non-interactive (no terminal): install everything.
    SELECTED_CATEGORIES=("${ALL_CATEGORIES[@]}")
fi

# "common" is always required by the other modules.
SELECTED_CATEGORIES+=(common)

# Quick membership test used while filtering downloads.
category_selected() {
    local needle="$1" cat
    for cat in "${SELECTED_CATEGORIES[@]}"; do
        [[ "$cat" == "$needle" ]] && return 0
    done
    return 1
}

info "Selected categories: ${SELECTED_CATEGORIES[*]}"

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
    # The category is the first path component (e.g. network/network.dns/... -> network).
    cat="${rel%%/*}"
    category_selected "$cat" || continue
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
    Out-Console.ps1              \
    Out-FileByDay.ps1            \
    Out-Kafka.ps1                \
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
    # Template names are prefixed with their category (e.g. network.dns.yaml).
    cat="${template%%.*}"
    category_selected "$cat" || continue
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
# 3b. src/<category>/requirements.txt — per-category Python dependencies
# ---------------------------------------------------------------------------

info "Downloading per-category Python requirements ..."

# Collect the requirements files that actually got installed so the venv step
# can install exactly the selected categories.
INSTALLED_REQUIREMENTS=()
for cat in "${SELECTED_CATEGORIES[@]}"; do
    rel="${cat}/requirements.txt"
    info "  $rel"
    download_file "${GITHUB_RAW}/src/${rel}" "$PREFIX/src/${rel}"
    INSTALLED_REQUIREMENTS+=("$PREFIX/src/${rel}")
done

success "Per-category requirements installed under $PREFIX/src/"

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
echo "  Categories         : ${SELECTED_CATEGORIES[*]}"
echo "  Monitoring modules : $PREFIX/src/"
echo "  Runner scripts     : $PREFIX/bin/"
echo "  Schedule configs   : $PREFIX/etc/    (edit before running)"
echo "  Monitor output     : $PREFIX/var/"
echo "  Python environment : $PREFIX/venv/"
echo ""
echo "Activate the environment for manual runs:"
echo "  source $PREFIX/venv/bin/activate"
echo ""
echo "Quick start:"
echo "  # Run a schedule and store results to a per-day file (other sinks: Out-Console.ps1, Out-Kafka.ps1):"
echo "  pwsh -Command \"& $PREFIX/bin/Run-MonitorSession.ps1 -TestSuiteFile $PREFIX/etc/<schedule>.yaml | & $PREFIX/bin/Out-FileByDay.ps1 -BaseName <schedule> -OutPath $PREFIX/var/\""
echo "  # or run all schedules:"
echo "  bash $PREFIX/bin/inventor-testbed.run-all.sh $PREFIX/etc/ $PREFIX/var/"
echo ""

# ---------------------------------------------------------------------------
# 5. venv/ — Python virtual environment
# ---------------------------------------------------------------------------

VENV_DIR="$PREFIX/venv"
info "Creating Python virtual environment at $VENV_DIR ..."
python3 -m venv "$VENV_DIR"
success "Virtual environment created"

if ui_yesno "Install Python requirements into the virtual environment now?" no; then
    info "Installing Python requirements for selected categories ..."
    "$VENV_DIR/bin/pip" install --upgrade pip --quiet
    for req in "${INSTALLED_REQUIREMENTS[@]}"; do
        info "  pip install -r $req"
        "$VENV_DIR/bin/pip" install -r "$req"
    done
    success "Requirements installed"
else
    info "Skipping requirements installation."
    echo ""
    echo "To install them later, run:"
    echo "  source $VENV_DIR/bin/activate"
    echo "  pip install --upgrade pip"
    for req in "${INSTALLED_REQUIREMENTS[@]}"; do
        echo "  pip install -r $req"
    done
    echo ""
    echo "Or without activating the environment:"
    for req in "${INSTALLED_REQUIREMENTS[@]}"; do
        echo "  $VENV_DIR/bin/pip install -r $req"
    done
    echo ""
fi

# ---------------------------------------------------------------------------
# 6. Patch bin scripts to activate the virtual environment
# ---------------------------------------------------------------------------

info "Patching runner scripts to use virtual environment ..."
for script in inventor-testbed.run-all.sh; do
    script_path="$PREFIX/bin/$script"
    tmp=$(mktemp)
    {
        head -1 "$script_path"
        echo "# Activate the inventor-monitor virtual environment"
        echo "source \"$VENV_DIR/bin/activate\""
        tail -n +2 "$script_path"
    } > "$tmp"
    mv "$tmp" "$script_path"
    chmod +x "$script_path"
    info "  patched $script"
done
success "Runner scripts updated to use $VENV_DIR"

# ---------------------------------------------------------------------------
# Optional: install as system service
# ---------------------------------------------------------------------------

ui_yesno "Install inventor-monitor as a system service?" no || exit 0

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

    if ui_yesno "Enable and start the service now?" no; then
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

    local plist_dir plist_file use_sudo=false
    if ui_interactive; then
        ui_menu "Service scope:" 0 \
            "User   — ~/Library/LaunchAgents   (starts on login, no sudo needed)" \
            "System — /Library/LaunchDaemons   (starts at boot, requires sudo)"
        [[ "$UI_RESULT_INDEX" == "1" ]] && use_sudo=true
    fi
    if [[ "$use_sudo" == "true" ]]; then
        plist_dir="/Library/LaunchDaemons"
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

    if ui_yesno "Load and start the service now?" no; then
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
