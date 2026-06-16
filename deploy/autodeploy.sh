#!/usr/bin/env bash
# autodeploy.sh — deploy the inventor testbed locally with Docker Compose.
#
# Builds a self-contained deployment directory in which each selected *profile*
# (a folder of monitoring schedules under ../profiles) runs as its own Docker
# container. Every schedule in a profile is executed by Run-MonitorSession.ps1
# and its results are published to Kafka via Out-Kafka.ps1. The Kafka topic for
# each schedule is resolved from the schedule YAML in priority order —
# monitors[].topic, then monitors[].name, then the file name without .yaml
# (e.g. network.dns.yaml -> topic "network.dns").
#
# Like install.sh, autodeploy.sh downloads the project sources from GitHub (a
# branch tarball) and assembles a self-contained deployment folder from them, so
# it can run straight from `curl ... | bash` without a local clone. It then
# generates a run.sh that brings the whole environment up with docker compose.

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

# ---------------------------------------------------------------------------
# Source location on GitHub
#
# The repository is downloaded as a branch tarball and the deployment is
# assembled from it. Override the branch by exporting INVENTOR_BRANCH.
# ---------------------------------------------------------------------------
GITHUB_REPO="rysavy-ondrej/project-inventor"
GITHUB_BRANCH="${INVENTOR_BRANCH:-main}"
GITHUB_TARBALL="https://github.com/${GITHUB_REPO}/archive/refs/heads/${GITHUB_BRANCH}.tar.gz"

IMAGE_NAME="inventor-monitor:local"

# Populated once the sources are downloaded (see "Download sources" below).
SRC_ROOT=""
PROFILES_DIR=""

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

# ---------------------------------------------------------------------------
# Interactive UI helpers (pure bash, no external dependencies)
#
# These render arrow-key driven menus directly on the controlling terminal.
# When no terminal is available they fall back to sensible defaults.
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
# Verify dependencies
# ---------------------------------------------------------------------------

require_cmd docker
if ! docker compose version &>/dev/null; then
    error "Docker Compose v2 is required ('docker compose'). Install Docker Desktop or the compose plugin."
fi
# Needed to download and unpack the source tarball from GitHub.
require_cmd tar
command -v curl &>/dev/null || require_cmd wget
success "Docker, Docker Compose and download tools are available"

# ---------------------------------------------------------------------------
# Prompt for install prefix
# ---------------------------------------------------------------------------

DEFAULT_PREFIX="./inventor-testbed"
read -r -p "Target deployment folder [${DEFAULT_PREFIX}]: " PREFIX
PREFIX="${PREFIX:-$DEFAULT_PREFIX}"
PREFIX="${PREFIX%/}"

mkdir -p "$PREFIX"
PREFIX=$(cd "$PREFIX" && pwd)

info "Deploying to: $PREFIX"

# ---------------------------------------------------------------------------
# Download sources from GitHub
#
# Fetch the repository as a branch tarball into a temporary staging area and
# extract it. Everything baked into the image (Dockerfile, src/, testbed/) and
# the list of available profiles are taken from this download.
# ---------------------------------------------------------------------------

STAGING="$(mktemp -d "${TMPDIR:-/tmp}/inventor-autodeploy.XXXXXX")"
cleanup_staging() { [[ -n "${STAGING:-}" && -d "$STAGING" ]] && rm -rf "$STAGING"; }
trap cleanup_staging EXIT

info "Downloading sources from $GITHUB_TARBALL ..."
if command -v curl &>/dev/null; then
    curl -fsSL "$GITHUB_TARBALL" -o "$STAGING/repo.tar.gz" \
        || error "Failed to download $GITHUB_TARBALL"
else
    wget -qO "$STAGING/repo.tar.gz" "$GITHUB_TARBALL" \
        || error "Failed to download $GITHUB_TARBALL"
fi

info "Extracting sources ..."
tar -xzf "$STAGING/repo.tar.gz" -C "$STAGING" || error "Failed to extract the downloaded archive"

# GitHub names the extracted directory "<repo>-<branch>".
SRC_ROOT="$STAGING/${GITHUB_REPO##*/}-${GITHUB_BRANCH}"
[[ -d "$SRC_ROOT" ]] || error "Unexpected archive layout: $SRC_ROOT not found"
PROFILES_DIR="$SRC_ROOT/profiles"

success "Sources downloaded for branch '$GITHUB_BRANCH'"

# ---------------------------------------------------------------------------
# Discover and select profiles
#
# Each immediate sub-directory of profiles/ is a deployable profile (a folder
# of *.yaml monitoring schedules). One Docker container is created per profile.
# ---------------------------------------------------------------------------

[[ -d "$PROFILES_DIR" ]] || error "Profiles directory not found in download: $PROFILES_DIR"

ALL_PROFILES=()
while IFS= read -r d; do
    name="$(basename "$d")"
    # A profile must contain at least one schedule (*.yaml) file.
    if compgen -G "$d/*.yaml" > /dev/null; then
        ALL_PROFILES+=("$name")
    fi
done < <(find "$PROFILES_DIR" -mindepth 1 -maxdepth 1 -type d | sort)

(( ${#ALL_PROFILES[@]} > 0 )) || error "No profiles with *.yaml schedules found under $PROFILES_DIR"

SELECTED_PROFILES=()
if ui_interactive; then
    # Build labelled options ("home   3 schedules") aligned to ALL_PROFILES.
    prof_labels=()
    for prof in "${ALL_PROFILES[@]}"; do
        count=$(find "$PROFILES_DIR/$prof" -maxdepth 1 -name '*.yaml' | wc -l | tr -d ' ')
        prof_labels+=("$(printf '%-16s %s schedule(s)' "$prof" "$count")")
    done
    ui_multiselect "Select profiles to deploy (one container each):" "${prof_labels[@]}"
    for idx in "${UI_SELECTED_INDICES[@]:-}"; do
        [[ -n "$idx" ]] && SELECTED_PROFILES+=("${ALL_PROFILES[$idx]}")
    done
    if (( ${#SELECTED_PROFILES[@]} == 0 )); then
        warn "No profiles selected — deploying all."
        SELECTED_PROFILES=("${ALL_PROFILES[@]}")
    fi
else
    # Non-interactive (no terminal): deploy everything.
    SELECTED_PROFILES=("${ALL_PROFILES[@]}")
fi

info "Selected profiles: ${SELECTED_PROFILES[*]}"

# ---------------------------------------------------------------------------
# Kafka configuration (provided by the user during setup)
#
# Results are published to an external Kafka broker. The topic for each schedule
# is derived from its file name; an optional prefix can namespace those topics.
# ---------------------------------------------------------------------------

DEFAULT_BROKER="localhost:9092"
read -r -p "Kafka bootstrap broker(s) [${DEFAULT_BROKER}]: " KAFKA_BROKER
KAFKA_BROKER="${KAFKA_BROKER:-$DEFAULT_BROKER}"

read -r -p "Kafka topic prefix (optional, blank = topic equals schedule name, e.g. network.dns): " KAFKA_TOPIC_PREFIX
KAFKA_TOPIC_PREFIX="${KAFKA_TOPIC_PREFIX:-}"

info "Kafka broker      : $KAFKA_BROKER"
if [[ -n "$KAFKA_TOPIC_PREFIX" ]]; then
    info "Kafka topic format: ${KAFKA_TOPIC_PREFIX}<schedule-name>"
else
    info "Kafka topic format: <schedule-name>"
fi

# ---------------------------------------------------------------------------
# Build the deployment directory layout
#
#   <PREFIX>/
#     app/              build context assembled from the GitHub download
#       Dockerfile
#       deploy/inventor-requirements.txt
#       src/
#       testbed/        (+ generated inventor-profile.run-kafka.sh)
#     profiles/<name>/  editable schedules, mounted into each container
#     docker-compose.yaml
#     .env              Kafka settings consumed by docker compose
#     run.sh            convenience wrapper around docker compose
# ---------------------------------------------------------------------------

APP_DIR="$PREFIX/app"
info "Assembling build context in $APP_DIR ..."
mkdir -p "$APP_DIR/deploy"

# Prefer rsync (handles excludes / repeat runs cleanly); fall back to cp.
copy_tree() {
    local src="$1" dest="$2"
    if command -v rsync &>/dev/null; then
        rsync -a --delete "$src/" "$dest/"
    else
        rm -rf "$dest"
        mkdir -p "$dest"
        cp -R "$src/." "$dest/"
    fi
}

cp "$SRC_ROOT/Dockerfile" "$APP_DIR/Dockerfile"
cp "$SRC_ROOT/deploy/inventor-requirements.txt" "$APP_DIR/deploy/inventor-requirements.txt"
copy_tree "$SRC_ROOT/src" "$APP_DIR/src"
copy_tree "$SRC_ROOT/testbed" "$APP_DIR/testbed"

# Note: the Dockerfile already installs kcat (kafkacat), which Out-Kafka.ps1
# requires to publish results, so no patching is needed here.

success "Build context assembled in $APP_DIR"

# Copy the selected profiles to an editable, mounted location (not baked into
# the image), so schedules can be tweaked without rebuilding.
info "Copying selected profiles ..."
mkdir -p "$PREFIX/profiles"
for prof in "${SELECTED_PROFILES[@]}"; do
    copy_tree "$PROFILES_DIR/$prof" "$PREFIX/profiles/$prof"
    info "  $prof"
done
success "Profiles copied to $PREFIX/profiles"

# ---------------------------------------------------------------------------
# Generate the in-container profile runner
#
# Runs every *.yaml schedule in PROFILE_DIR concurrently, each piped into the
# Kafka sink with a topic derived from the schedule file name.
# ---------------------------------------------------------------------------

RUN_KAFKA="$APP_DIR/testbed/inventor-profile.run-kafka.sh"
info "Generating profile runner: testbed/inventor-profile.run-kafka.sh"
cat > "$RUN_KAFKA" <<'EOF'
#!/usr/bin/env bash
# inventor-profile.run-kafka.sh — run every schedule in a profile and publish
# results to Kafka. Generated by deploy/autodeploy.sh.
#
# Configuration is taken from the environment:
#   PROFILE_DIR        directory of *.yaml schedules to run (required)
#   KAFKA_BROKER       Kafka bootstrap broker(s)            (required)
#   KAFKA_TOPIC_PREFIX prefix prepended to each topic       (optional)
#
# The Kafka topic for each schedule is "<KAFKA_TOPIC_PREFIX><schedule-name>",
# where <schedule-name> is resolved from the schedule YAML in priority order:
#   1. monitors[].topic   (first monitor entry that defines a 'topic')
#   2. monitors[].name    (first monitor entry that defines a 'name')
#   3. the schedule file name without its .yaml extension
# (e.g. network.dns.yaml -> network.dns). The YAML fields are read via the
# powershell-yaml module already required by Run-MonitorSession.ps1.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PROFILE_DIR="${PROFILE_DIR:?PROFILE_DIR environment variable is required}"
KAFKA_BROKER="${KAFKA_BROKER:?KAFKA_BROKER environment variable is required}"
KAFKA_TOPIC_PREFIX="${KAFKA_TOPIC_PREFIX:-}"

if ! compgen -G "$PROFILE_DIR/*.yaml" > /dev/null; then
    echo "No *.yaml schedules found in $PROFILE_DIR" >&2
    exit 1
fi

# Resolve a schedule's logical name in priority order: monitors[].topic, then
# monitors[].name, then the file name without its .yaml extension. The first two
# are parsed from the YAML with powershell-yaml; any parse error or missing
# value falls through to the file name.
resolve_schedule_name() {
    local file="$1" name=""
    name="$(SUITE="$file" pwsh -NoProfile -Command '
        try { $cfg = Get-Content -Raw -LiteralPath $env:SUITE | ConvertFrom-Yaml } catch { exit 0 }
        $monitors = @($cfg.monitors)
        $val = $null
        foreach ($m in $monitors) { if ($m.topic) { $val = $m.topic; break } }
        if (-not $val) { foreach ($m in $monitors) { if ($m.name) { $val = $m.name; break } } }
        if ($val) { Write-Output ([string]$val).Trim() }
    ' 2>/dev/null)"
    [[ -n "$name" ]] || name="$(basename "$file" .yaml)"
    printf '%s' "$name"
}

echo "Launching schedules from $PROFILE_DIR -> Kafka broker $KAFKA_BROKER ..."

for suite in "$PROFILE_DIR"/*.yaml; do
    base="$(resolve_schedule_name "$suite")"
    topic="${KAFKA_TOPIC_PREFIX}${base}"
    echo "Starting $base -> topic '$topic' ..."
    pwsh -Command "& '$SCRIPT_DIR/Run-MonitorSession.ps1' -TestSuiteFile '$suite' | & '$SCRIPT_DIR/Out-Kafka.ps1' -KafkaBroker '$KAFKA_BROKER' -KafkaTopic '$topic'" &
done

echo "All schedules started; waiting ..."
wait
echo "All monitor sessions finished."
EOF
chmod +x "$RUN_KAFKA"
success "Profile runner generated"

# ---------------------------------------------------------------------------
# Generate .env (Kafka settings consumed by docker compose interpolation)
# ---------------------------------------------------------------------------

info "Writing $PREFIX/.env ..."
cat > "$PREFIX/.env" <<EOF
# Kafka settings for the inventor testbed deployment.
# Edit and re-run ./run.sh to apply changes.
KAFKA_BROKER=${KAFKA_BROKER}
KAFKA_TOPIC_PREFIX=${KAFKA_TOPIC_PREFIX}
EOF
success ".env written"

# ---------------------------------------------------------------------------
# Generate docker-compose.yaml (one service per selected profile)
# ---------------------------------------------------------------------------

COMPOSE_FILE="$PREFIX/docker-compose.yaml"
info "Writing $COMPOSE_FILE ..."
{
    echo "# Generated by deploy/autodeploy.sh — one container per profile."
    echo "# Each container runs its profile's schedules and publishes results to Kafka."
    echo "services:"
    for prof in "${SELECTED_PROFILES[@]}"; do
        # Docker Compose service names must be DNS-safe: map '.' and '_' to '-'.
        svc="testbed-$(echo "$prof" | tr '._' '--')"
        cat <<EOF
  ${svc}:
    image: ${IMAGE_NAME}
    build:
      context: ./app
      dockerfile: Dockerfile
    restart: on-failure
    working_dir: /inventor/testbed
    environment:
      PROFILE_DIR: /inventor/profiles/${prof}
      KAFKA_BROKER: "\${KAFKA_BROKER}"
      KAFKA_TOPIC_PREFIX: "\${KAFKA_TOPIC_PREFIX}"
    volumes:
      - ./profiles/${prof}:/inventor/profiles/${prof}:ro
    command: ["bash", "/inventor/testbed/inventor-profile.run-kafka.sh"]
EOF
    done
} > "$COMPOSE_FILE"
success "docker-compose.yaml written"

# ---------------------------------------------------------------------------
# Generate run.sh in the deployment root
# ---------------------------------------------------------------------------

RUN_SH="$PREFIX/run.sh"
info "Writing $RUN_SH ..."
cat > "$RUN_SH" <<'EOF'
#!/usr/bin/env bash
# run.sh — control the inventor testbed deployment. Generated by autodeploy.sh.
#
# Usage:
#   ./run.sh              build images (if needed) and start all profiles
#   ./run.sh up           same as above (foreground)
#   ./run.sh up -d        start detached (background)
#   ./run.sh logs         follow container logs
#   ./run.sh ps           show container status
#   ./run.sh stop         stop containers (keep them)
#   ./run.sh down         stop and remove containers
#   ./run.sh build        (re)build the image
#   ./run.sh <args...>    pass any other arguments straight to docker compose

set -euo pipefail

# Always operate from the deployment directory so relative paths and .env resolve.
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cmd="${1:-up}"
case "$cmd" in
    up)
        shift || true
        # Default to building so source/profile edits are picked up.
        exec docker compose up --build "$@"
        ;;
    logs)
        shift || true
        exec docker compose logs -f "$@"
        ;;
    ps)
        shift || true
        exec docker compose ps "$@"
        ;;
    stop)
        shift || true
        exec docker compose stop "$@"
        ;;
    down)
        shift || true
        exec docker compose down "$@"
        ;;
    build)
        shift || true
        exec docker compose build "$@"
        ;;
    *)
        exec docker compose "$@"
        ;;
esac
EOF
chmod +x "$RUN_SH"
success "run.sh written"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo ""
echo "============================================================"
echo "  inventor testbed deployed to: $PREFIX"
echo "============================================================"
echo "  Profiles        : ${SELECTED_PROFILES[*]}"
echo "  Containers      : one per profile (service 'testbed-<profile>')"
echo "  Kafka broker    : $KAFKA_BROKER"
if [[ -n "$KAFKA_TOPIC_PREFIX" ]]; then
    echo "  Kafka topics    : ${KAFKA_TOPIC_PREFIX}<schedule-name>"
else
    echo "  Kafka topics    : <schedule-name>   (e.g. network.dns)"
fi
echo "  Build context   : $APP_DIR"
echo "  Editable configs: $PREFIX/profiles/   (mounted into containers)"
echo "  Kafka settings  : $PREFIX/.env"
echo "  Compose file    : $COMPOSE_FILE"
echo ""
echo "Quick start:"
echo "  cd $PREFIX"
echo "  ./run.sh             # build images and start all profiles"
echo "  ./run.sh up -d       # or start in the background"
echo "  ./run.sh logs        # follow output"
echo "  ./run.sh down        # stop and remove containers"
echo ""

if ui_yesno "Build images and start the deployment now?" no; then
    info "Starting deployment (docker compose up --build) ..."
    ( cd "$PREFIX" && docker compose up --build -d )
    success "Deployment started. Follow logs with:  cd $PREFIX && ./run.sh logs"
else
    info "Skipping startup. Launch later with:  cd $PREFIX && ./run.sh"
fi
