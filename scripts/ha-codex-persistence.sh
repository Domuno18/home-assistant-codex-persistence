#!/bin/sh
#
# One-time installation and automatic restart bootstrap for persistent Codex
# and GitHub CLI operation in Home Assistant Studio Code Server.
#
# User-facing lifecycle:
#   install  - run once after Codex and gh are installed and logged in
#   boot     - runs automatically through Studio Code Server init_commands
#   audit    - read-only verification

set -u

PROGRAM_VERSION=0.9.0-beta.2
RUNTIME_ROOT=${HACP_RUNTIME_ROOT:-/data/codex-persistence}
CODEX_SOURCE=${HACP_CODEX_SOURCE:-/root/.codex}
GH_SOURCE=${HACP_GH_SOURCE:-/root/.config/gh}
GIT_CONFIG_SOURCE=${HACP_GIT_CONFIG_SOURCE:-/root/.gitconfig}
BIN_LINK_ROOT=${HACP_BIN_LINK_ROOT:-/usr/local/bin}
CURRENT_ROOT=$RUNTIME_ROOT/current
STATE_ROOT=$RUNTIME_ROOT/state
LOCK_ROOT=$RUNTIME_ROOT/locks
BOOTSTRAP_ROOT=$RUNTIME_ROOT/bootstrap
RUNTIME_OWNER_MARKER=$RUNTIME_ROOT/.hacp-runtime-owner
RUNTIME_OWNER_ID=home-assistant-codex-persistence-v1
ACTIVE_MARKER=$STATE_ROOT/active-generation
READY_MARKER=$STATE_ROOT/ready-generation
CODEX_TARGET=$CURRENT_ROOT/codex-home
GH_TARGET=$CURRENT_ROOT/gh
META_ROOT=$CURRENT_ROOT/meta
CODEX_MANIFEST=$META_ROOT/codex.tree
GH_MANIFEST=$META_ROOT/github.tree
META_SUMS=$META_ROOT/SHA256SUMS
CURRENT_GENERATION=$META_ROOT/generation
TOOLS_ROOT=$CURRENT_ROOT/tools
TOOLS_BIN=$TOOLS_ROOT/bin
CODEX_TOOL=$TOOLS_BIN/codex
GH_TOOL=$TOOLS_BIN/gh
CODEX_LINK=$BIN_LINK_ROOT/codex
GH_LINK=$BIN_LINK_ROOT/gh
GITHUB_GIT_HELPER_KEY=credential.https://github.com.helper
GIST_GIT_HELPER_KEY=credential.https://gist.github.com.helper
GIT_HELPER_VALUE="!GH_CONFIG_DIR=$GH_SOURCE $GH_LINK auth git-credential"
BOOTSTRAP_SCRIPT=$BOOTSTRAP_ROOT/ha-codex-persistence.sh
MAX_COPY_ATTEMPTS=${HACP_MAX_COPY_ATTEMPTS:-3}
EXIT_CODE=0
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
SCRIPT_PATH=$SCRIPT_DIR/$(basename "$0")
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd -P)
MEMORY_SETUP=${HACP_MEMORY_SETUP:-YES}
WORKSPACE_ROOT=${HACP_WORKSPACE_ROOT:-/config/Codex}
MEMORY_ROOT=$WORKSPACE_ROOT/Memories
MEMORY_BLOCK_BEGIN='<!-- BEGIN HACP MEMORY -->'
MEMORY_BLOCK_END='<!-- END HACP MEMORY -->'
EFFECTIVE_GLOBAL_AGENTS=
EFFECTIVE_GIT_CONFIG=
RUNTIME_CANONICAL=
LAST_BACKUP=

report() {
    level=$1
    check=$2
    target=$3
    detail=$4
    printf '%s\t%s\t%s\t%s\n' "$level" "$check" "$target" "$detail"
}

set_exit() {
    requested=$1
    if [ "$EXIT_CODE" -eq 0 ] || [ "$EXIT_CODE" -eq 1 ]; then
        EXIT_CODE=$requested
    fi
}

path_exists() {
    [ -e "$1" ] || [ -L "$1" ]
}

is_nonempty_dir() {
    [ -d "$1" ] && [ ! -L "$1" ] || return 1
    first_entry=$(find "$1" -mindepth 1 -print -quit 2>/dev/null) || return 1
    [ -n "$first_entry" ]
}

dir_mode() {
    stat -c '%a' "$1" 2>/dev/null || printf '%s' unknown
}

dir_owner() {
    stat -c '%u:%g' "$1" 2>/dev/null || printf '%s' unknown
}

is_test_mode() {
    [ "${HACP_TEST_MODE:-}" = YES ]
}

check_tools() {
    missing=no
    for tool in \
        awk basename chmod chown cmp command cp curl date dirname find flock git id \
        jq ln mkdir mktemp mv pwd readlink rm rmdir sed sha256sum sleep sort \
        stat sync tar tr wc grep
    do
        if command -v "$tool" >/dev/null 2>&1; then
            :
        else
            report BLOCK tool "$tool" "missing"
            missing=yes
        fi
    done
    if [ "$missing" = yes ]; then
        set_exit 3
        return 3
    fi
    return 0
}

validate_safe_path() {
    label=$1
    candidate=$2
    case "$candidate" in
        /*) ;;
        *)
            report BLOCK "$label-path" "$candidate" "absolute path required"
            return 1
            ;;
    esac
    case "$candidate/" in
        *"/../"*|*"/./"*|*"//"*|*" "*|*"	"*)
            report BLOCK "$label-path" "$candidate" \
                "canonical path without whitespace required"
            return 1
            ;;
    esac
    case "$candidate" in
        *[!A-Za-z0-9_./-]*)
            report BLOCK "$label-path" "$candidate" \
                "only letters, digits, dot, underscore, slash and hyphen allowed"
            return 1
            ;;
    esac
    return 0
}

runtime_has_git_ancestor() {
    probe=$1
    if [ ! -d "$probe" ]; then
        probe=$(dirname "$probe")
    fi
    while [ "$probe" != / ]
    do
        if path_exists "$probe/.git"; then
            return 0
        fi
        next_probe=$(dirname "$probe")
        [ "$next_probe" != "$probe" ] || break
        probe=$next_probe
    done
    return 1
}

resolve_runtime_root_path() {
    runtime_parent=$(dirname "$RUNTIME_ROOT")
    if [ ! -d "$runtime_parent" ] || [ -L "$runtime_parent" ]; then
        report BLOCK runtime-parent "$runtime_parent" \
            "parent must already be a regular persistent directory"
        return 1
    fi
    parent_canonical=$(CDPATH= cd -- "$runtime_parent" && pwd -P) || return 1
    if path_exists "$RUNTIME_ROOT"; then
        if [ ! -d "$RUNTIME_ROOT" ] || [ -L "$RUNTIME_ROOT" ]; then
            report BLOCK runtime-root "$RUNTIME_ROOT" \
                "regular directory or absent target required"
            return 1
        fi
        runtime_candidate=$(CDPATH= cd -- "$RUNTIME_ROOT" && pwd -P) || return 1
    else
        runtime_candidate=$parent_canonical/$(basename "$RUNTIME_ROOT")
    fi
    if [ "$runtime_candidate" != "$RUNTIME_ROOT" ]; then
        report BLOCK runtime-root "$RUNTIME_ROOT" \
            "canonical path differs: $runtime_candidate"
        return 1
    fi
    if [ "$SCRIPT_PATH" != "$BOOTSTRAP_SCRIPT" ]; then
        case "$runtime_candidate" in
            "$PROJECT_ROOT"|"$PROJECT_ROOT"/*)
                report BLOCK runtime-root "$RUNTIME_ROOT" \
                    "target must stay outside the installer checkout"
                return 1
                ;;
        esac
    fi
    if runtime_has_git_ancestor "$runtime_candidate"; then
        report BLOCK runtime-root "$RUNTIME_ROOT" \
            "private runtime must stay outside every Git checkout"
        return 1
    fi
    RUNTIME_CANONICAL=$runtime_candidate
}

validate_configuration() {
    if ! is_test_mode &&
        { [ "${HACP_SKIP_PROCESS_CHECK:-}" = YES ] ||
            [ "${HACP_SKIP_ADDON_CONFIG:-}" = YES ]; }; then
        report BLOCK test-bypass runtime \
            "skip controls require HACP_TEST_MODE=YES"
        return 1
    fi

    validate_safe_path runtime-root "$RUNTIME_ROOT" || return 1
    validate_safe_path codex-source "$CODEX_SOURCE" || return 1
    validate_safe_path github-source "$GH_SOURCE" || return 1
    validate_safe_path git-config-source "$GIT_CONFIG_SOURCE" || return 1
    validate_safe_path bin-link-root "$BIN_LINK_ROOT" || return 1
    resolve_runtime_root_path || return 1

    case "$RUNTIME_ROOT" in
        /|/root|/root/*|/data|/config|/share|/media)
            report BLOCK runtime-root "$RUNTIME_ROOT" "target is unsafe or too broad"
            return 1
            ;;
    esac
    if [ "${HACP_TEST_MODE:-}" != YES ]; then
        if [ "$CODEX_SOURCE" != /root/.codex ] ||
            [ "$GH_SOURCE" != /root/.config/gh ] ||
            [ "$BIN_LINK_ROOT" != /usr/local/bin ]; then
            report BLOCK container-paths runtime \
                "production source and command paths must use the documented defaults"
            return 1
        fi
        case "$RUNTIME_ROOT" in
            /data/*|/config/*|/share/*) ;;
            *)
                report BLOCK runtime-root "$RUNTIME_ROOT" \
                    "expected persistent storage below /data, /config or /share"
                return 1
                ;;
        esac
    fi
    case "$RUNTIME_ROOT/" in
        "$CODEX_SOURCE/"*|"$GH_SOURCE/"*)
            report BLOCK runtime-root "$RUNTIME_ROOT" \
                "target must not be inside a source"
            return 1
            ;;
    esac
    case "$CODEX_SOURCE/" in
        "$RUNTIME_ROOT/"*)
            report BLOCK codex-source "$CODEX_SOURCE" \
                "source must not be inside target"
            return 1
            ;;
    esac
    case "$GH_SOURCE/" in
        "$RUNTIME_ROOT/"*)
            report BLOCK github-source "$GH_SOURCE" \
                "source must not be inside target"
            return 1
            ;;
    esac

    case "$MAX_COPY_ATTEMPTS" in
        ''|*[!0-9]*)
            report BLOCK copy-attempts "$MAX_COPY_ATTEMPTS" \
                "positive integer required"
            return 1
            ;;
    esac
    if [ "$MAX_COPY_ATTEMPTS" -lt 1 ] || [ "$MAX_COPY_ATTEMPTS" -gt 10 ]; then
        report BLOCK copy-attempts "$MAX_COPY_ATTEMPTS" "allowed range is 1..10"
        return 1
    fi
    if [ "$(id -u)" -ne 0 ] && [ "${HACP_TEST_MODE:-}" != YES ]; then
        report BLOCK runtime-user "$(id -u)" "root privileges required"
        return 1
    fi
    return 0
}

ensure_private_dir() {
    path=$1
    parent=$2
    if [ -L "$path" ]; then
        return 1
    fi
    if [ -d "$path" ]; then
        chmod 700 "$path" || return 1
        chown 0:0 "$path" 2>/dev/null || {
            [ "${HACP_TEST_MODE:-}" = YES ] || return 1
        }
        return 0
    fi
    path_exists "$path" && return 1
    [ -d "$parent" ] && [ ! -L "$parent" ] || return 1
    mkdir "$path" || return 1
    chmod 700 "$path" || return 1
    chown 0:0 "$path" 2>/dev/null || {
        [ "${HACP_TEST_MODE:-}" = YES ] || return 1
    }
}

runtime_owner_marker_valid() (
    [ -f "$RUNTIME_OWNER_MARKER" ] && [ ! -L "$RUNTIME_OWNER_MARKER" ] ||
        return 1
    [ "$(stat -c '%h' "$RUNTIME_OWNER_MARKER" 2>/dev/null)" = 1 ] || return 1
    [ "$(dir_mode "$RUNTIME_OWNER_MARKER")" = 600 ] || return 1
    if ! is_test_mode &&
        [ "$(dir_owner "$RUNTIME_OWNER_MARKER")" != 0:0 ]; then
        return 1
    fi
    actual_hash=$(sha256sum "$RUNTIME_OWNER_MARKER" | awk '{print $1}') ||
        return 1
    expected_hash=$(printf '%s\n' "$RUNTIME_OWNER_ID" | sha256sum |
        awk '{print $1}') || return 1
    [ "$actual_hash" = "$expected_hash" ]
)

runtime_top_level_is_managed() {
    unexpected=$(
        find "$RUNTIME_ROOT" -mindepth 1 -maxdepth 1 \
            ! -name '.hacp-runtime-owner' \
            ! -name current \
            ! -name state \
            ! -name locks \
            ! -name bootstrap \
            ! -name '.hacp-work-*' \
            -print -quit 2>/dev/null
    ) || return 1
    [ -z "$unexpected" ]
}

claim_runtime_root() {
    resolve_runtime_root_path || return 1
    runtime_parent=$(dirname "$RUNTIME_ROOT")
    if [ -d "$RUNTIME_ROOT" ]; then
        if runtime_owner_marker_valid; then
            if ! runtime_top_level_is_managed; then
                report BLOCK runtime-owner "$RUNTIME_ROOT" \
                    "claimed runtime contains an unknown top-level entry"
                return 1
            fi
            report OK runtime-owner "$RUNTIME_ROOT" \
                "validated HACP ownership marker"
        elif is_nonempty_dir "$RUNTIME_ROOT"; then
            report BLOCK runtime-owner "$RUNTIME_ROOT" \
                "non-empty unclaimed runtime; nothing changed"
            return 1
        fi
    else
        mkdir -m 700 "$RUNTIME_ROOT" || {
            report BLOCK runtime-root "$RUNTIME_ROOT" "cannot create safely"
            return 1
        }
    fi

    chmod 700 "$RUNTIME_ROOT" || return 1
    chown 0:0 "$RUNTIME_ROOT" 2>/dev/null || {
        is_test_mode || return 1
    }
    if runtime_owner_marker_valid; then
        return 0
    fi

    owner_anchor=$(mktemp "$runtime_parent/.hacp-owner.XXXXXX") || return 1
    trap 'rm -f -- "$owner_anchor"' 0 1 2 3 15
    printf '%s\n' "$RUNTIME_OWNER_ID" > "$owner_anchor" || return 1
    chmod 600 "$owner_anchor" || return 1
    chown 0:0 "$owner_anchor" 2>/dev/null || {
        is_test_mode || return 1
    }
    sync "$owner_anchor" 2>/dev/null || sync || return 1
    if ! ln "$owner_anchor" "$RUNTIME_OWNER_MARKER"; then
        report BLOCK runtime-owner "$RUNTIME_ROOT" \
            "ownership marker appeared concurrently; nothing was adopted"
        return 1
    fi
    marker_identity=$(stat -c '%d:%i' "$RUNTIME_OWNER_MARKER" 2>/dev/null || true)
    anchor_identity=$(stat -c '%d:%i' "$owner_anchor" 2>/dev/null || true)
    concurrent=$(
        find "$RUNTIME_ROOT" -mindepth 1 -maxdepth 1 \
            ! -name '.hacp-runtime-owner' -print -quit 2>/dev/null
    ) || concurrent=unsafe
    if [ -z "$marker_identity" ] || [ "$marker_identity" != "$anchor_identity" ] ||
        [ -n "$concurrent" ]; then
        current_identity=$(stat -c '%d:%i' "$RUNTIME_OWNER_MARKER" 2>/dev/null || true)
        if [ -n "$current_identity" ] &&
            [ "$current_identity" = "$anchor_identity" ]; then
            rm -f -- "$RUNTIME_OWNER_MARKER" || true
        fi
        report BLOCK runtime-owner "$RUNTIME_ROOT" \
            "runtime changed during ownership claim; foreign entries were preserved"
        return 1
    fi
    rm -f -- "$owner_anchor" || return 1
    trap - 0 1 2 3 15
    runtime_owner_marker_valid || {
        report BLOCK runtime-owner "$RUNTIME_OWNER_MARKER" \
            "published ownership marker failed verification"
        return 1
    }
    sync "$RUNTIME_OWNER_MARKER" "$RUNTIME_ROOT" "$runtime_parent" \
        2>/dev/null || sync || return 1
    report OK runtime-owner "$RUNTIME_ROOT" "private runtime claimed"
}

ensure_runtime_layout() {
    claim_runtime_root || return 1
    ensure_private_dir "$STATE_ROOT" "$RUNTIME_ROOT" || return 1
    ensure_private_dir "$LOCK_ROOT" "$RUNTIME_ROOT" || return 1
    ensure_private_dir "$BOOTSTRAP_ROOT" "$RUNTIME_ROOT" || return 1
    return 0
}

verify_runtime_layout() {
    resolve_runtime_root_path || return 1
    if ! runtime_owner_marker_valid; then
        report BLOCK runtime-owner "$RUNTIME_OWNER_MARKER" \
            "valid private runtime ownership marker required"
        return 1
    fi
    if ! runtime_top_level_is_managed; then
        report BLOCK runtime-owner "$RUNTIME_ROOT" \
            "claimed runtime contains an unknown top-level entry"
        return 1
    fi
    for path in "$RUNTIME_ROOT" "$STATE_ROOT" "$LOCK_ROOT" "$BOOTSTRAP_ROOT"
    do
        if [ ! -d "$path" ] || [ -L "$path" ]; then
            report BLOCK runtime-layout "$path" \
                "installed regular directory required"
            return 1
        fi
        mode=$(dir_mode "$path")
        owner=$(dir_owner "$path")
        if [ "$mode" != 700 ] ||
            { [ "${HACP_TEST_MODE:-}" != YES ] && [ "$owner" != 0:0 ]; }; then
            report BLOCK runtime-layout "$path" \
                "expected root:root mode 0700, found $owner mode $mode"
            return 1
        fi
    done
    runtime_canonical=$(CDPATH= cd -- "$RUNTIME_ROOT" && pwd -P) || return 1
    if [ "$runtime_canonical" != "$RUNTIME_ROOT" ]; then
        report BLOCK runtime-root "$RUNTIME_ROOT" \
            "canonical path differs: $runtime_canonical"
        return 1
    fi
    return 0
}

codex_config_file_store_line() (
    config_path=$1
    awk '
        BEGIN { section = 0; matches = 0; selected = 0 }
        /^[[:space:]]*\[/ { section = 1 }
        /^[[:space:]]*cli_auth_credentials_store[[:space:]]*=/ {
            matches++
            if (!section) selected = NR
        }
        END {
            if (matches == 1 && selected > 0) print selected
        }
    ' "$config_path"
)

codex_config_uses_file_store() (
    config_path=$1
    [ -s "$config_path" ] && [ -f "$config_path" ] &&
        [ ! -L "$config_path" ] || return 1
    store_line=$(codex_config_file_store_line "$config_path") || return 1
    [ -n "$store_line" ] || return 1
    sed -n "${store_line}p" "$config_path" |
        grep -Eq '^[[:space:]]*cli_auth_credentials_store[[:space:]]*=[[:space:]]*"file"[[:space:]]*(#[^[:cntrl:]]*)?$'
)

codex_config_can_append_top_level() (
    config_path=$1
    [ -f "$config_path" ] && [ ! -L "$config_path" ] || return 1
    [ "$(stat -c '%h' "$config_path" 2>/dev/null)" = 1 ] || return 1
    ! grep -q "$(printf '\r')" "$config_path" || return 1
    ! grep -Eq '^[[:space:]]*sqlite_home[[:space:]]*=' "$config_path" ||
        return 1
    ! grep -Eq '^[[:space:]]*\[' "$config_path" || return 1
    ! grep -Fq "$(printf '\047\047\047')" "$config_path" || return 1
    ! grep -Fq "$(printf '\042\042\042')" "$config_path" || return 1
    [ "$(grep -Ec \
        '^[[:space:]]*cli_auth_credentials_store[[:space:]]*=' \
        "$config_path" || true)" -eq 0 ] 2>/dev/null
)

ensure_codex_file_credentials_store() (
    config_path=$CODEX_SOURCE/config.toml
    if [ -L "$config_path" ]; then
        report BLOCK codex-config "$config_path" \
            "symlink is not accepted"
        return 1
    fi
    if ! path_exists "$config_path"; then
        temporary=$(mktemp "$CODEX_SOURCE/.hacp-config.XXXXXX") || return 1
        trap "rm -f -- \"$temporary\"" 0 1 2 3 15
        printf "%s\n" "cli_auth_credentials_store = \"file\"" > "$temporary" ||
            return 1
        chmod 600 "$temporary" || return 1
        chown 0:0 "$temporary" 2>/dev/null || {
            is_test_mode || return 1
        }
        sync "$temporary" 2>/dev/null || sync || return 1
        if ln "$temporary" "$config_path"; then
            rm -f -- "$temporary" || return 1
            trap - 0 1 2 3 15
            report OK codex-config cli_auth_credentials_store \
                "missing config.toml atomically created with file storage"
            return 0
        fi

        rm -f -- "$temporary" || return 1
        trap - 0 1 2 3 15
        if path_exists "$config_path"; then
            report BLOCK codex-config "$config_path" \
                "path appeared concurrently and was not overwritten"
        else
            report BLOCK codex-config "$config_path" \
                "atomic no-clobber creation failed"
        fi
        return 1
    fi
    if [ ! -f "$config_path" ]; then
        report BLOCK codex-config "$config_path" \
            "existing path is not a regular file"
        return 1
    fi
    if [ "$(stat -c '%h' "$config_path" 2>/dev/null)" != 1 ]; then
        report BLOCK codex-config "$config_path" \
            "hard-linked config is not accepted"
        return 1
    fi
    if grep -q "$(printf '\r')" "$config_path"; then
        report BLOCK codex-config "$config_path" \
            "CR characters make safe TOML handling ambiguous"
        return 1
    fi
    if grep -Eq '^[[:space:]]*sqlite_home[[:space:]]*=' "$config_path"; then
        report BLOCK codex-config sqlite_home \
            "external SQLite home is not supported; use the Codex home default"
        return 1
    fi

    match_count=$(grep -Ec \
        '^[[:space:]]*cli_auth_credentials_store[[:space:]]*=' \
        "$config_path" || true)
    case "$match_count" in
        0) ;;
        1)
            store_line=$(codex_config_file_store_line "$config_path") ||
                return 1
            [ -n "$store_line" ] || {
                report BLOCK codex-config cli_auth_credentials_store \
                    "credential-store key is not an unambiguous top-level key"
                return 1
            }
            current_line=$(sed -n "${store_line}p" "$config_path") || return 1
            printf '%s\n' "$current_line" |
                grep -Eq '^[[:space:]]*cli_auth_credentials_store[[:space:]]*=[[:space:]]*"(auto|file|keyring)"[[:space:]]*(#[^[:cntrl:]]*)?$' || {
                report BLOCK codex-config cli_auth_credentials_store \
                    "unsupported TOML syntax; set the top-level value to \"file\" manually"
                return 1
            }
            if codex_config_uses_file_store "$config_path"; then
                report OK codex-config cli_auth_credentials_store \
                    "top-level credential store already set to file"
                return 0
            fi
            report BLOCK codex-config cli_auth_credentials_store \
                "existing non-file store preserved; set the top-level value to \"file\" manually"
            return 1
            ;;
        *)
            report BLOCK codex-config cli_auth_credentials_store \
                "duplicate credential-store keys; refusing ambiguous TOML edit"
            return 1
            ;;
    esac

    if ! codex_config_can_append_top_level "$config_path"; then
        report BLOCK codex-config "$config_path" \
            "cannot append a top-level file store safely; add it manually before the first table"
        return 1
    fi
    before_identity=$(stat -c '%d:%i' "$config_path") || return 1
    before_hash=$(sha256sum "$config_path" | awk '{print $1}') || return 1
    exec 6<"$config_path" || return 1
    exec 7>>"/proc/self/fd/6" || {
        exec 6<&-
        return 1
    }
    if ! flock -n 7; then
        report BLOCK codex-config "$config_path" \
            "config is locked by another writer"
        exec 7>&-
        exec 6<&-
        return 1
    fi
    path_identity=$(stat -c '%d:%i' "$config_path" 2>/dev/null || true)
    reader_identity=$(stat -L -c '%d:%i' /proc/self/fd/6 2>/dev/null || true)
    writer_identity=$(stat -L -c '%d:%i' /proc/self/fd/7 2>/dev/null || true)
    path_links=$(stat -c '%h' "$config_path" 2>/dev/null || true)
    reader_links=$(stat -L -c '%h' /proc/self/fd/6 2>/dev/null || true)
    writer_links=$(stat -L -c '%h' /proc/self/fd/7 2>/dev/null || true)
    if [ -z "$path_identity" ] || [ "$path_identity" != "$before_identity" ] ||
        [ "$path_identity" != "$reader_identity" ] ||
        [ "$path_identity" != "$writer_identity" ] ||
        [ "$path_links" != 1 ] || [ "$reader_links" != 1 ] ||
        [ "$writer_links" != 1 ] ||
        [ "$(sha256sum "$config_path" | awk '{print $1}')" != "$before_hash" ] ||
        ! codex_config_can_append_top_level "$config_path"; then
        report BLOCK codex-config "$config_path" \
            "config changed before safe append; concurrent content was not overwritten"
        exec 7>&-
        exec 6<&-
        return 1
    fi
    if ! printf '\n%s\n' 'cli_auth_credentials_store = "file"' >&7; then
        exec 7>&-
        exec 6<&-
        return 1
    fi
    sync "$config_path" 2>/dev/null || sync || {
        exec 7>&-
        exec 6<&-
        return 1
    }
    exec 7>&-
    exec 6<&-
    if [ "$(stat -c '%d:%i' "$config_path" 2>/dev/null || true)" != \
        "$before_identity" ] || ! codex_config_uses_file_store "$config_path"; then
        report BLOCK codex-config "$config_path" \
            "config changed after append; no existing content was replaced"
        return 1
    fi
    report OK codex-config cli_auth_credentials_store \
        "file storage appended without replacing existing config bytes"
)
validate_codex_storage_rules() (
    root=$1
    label=$2
    if [ ! -s "$root/auth.json" ] || [ ! -f "$root/auth.json" ] ||
        [ -L "$root/auth.json" ]; then
        report BLOCK "$label-auth" "$root/auth.json" \
            "non-empty regular Codex login file required"
        return 1
    fi
    if ! codex_config_uses_file_store "$root/config.toml"; then
        report BLOCK "$label-config" "$root/config.toml" \
            "top-level cli_auth_credentials_store must equal file"
        return 1
    fi
    if grep -Eq '^[[:space:]]*sqlite_home[[:space:]]*=' \
        "$root/config.toml"; then
        report BLOCK "$label-config" sqlite_home \
            "external SQLite home is not supported"
        return 1
    fi
    if path_exists "$root/sessions" &&
        { [ ! -d "$root/sessions" ] || [ -L "$root/sessions" ]; }; then
        report BLOCK "$label-sessions" "$root/sessions" \
            "regular native session directory required"
        return 1
    fi
    if path_exists "$root/ipc/ipc.sock" &&
        { [ -L "$root/ipc/ipc.sock" ] || [ ! -S "$root/ipc/ipc.sock" ]; }; then
        report BLOCK "$label-ipc" "$root/ipc/ipc.sock" \
            "reserved path may only contain a live Unix socket"
        return 1
    fi
    return 0
)

validate_github_storage_rules() (
    root=$1
    label=$2
    if [ ! -s "$root/hosts.yml" ] || [ ! -f "$root/hosts.yml" ] ||
        [ -L "$root/hosts.yml" ]; then
        report BLOCK "$label-auth" "$root/hosts.yml" \
            "non-empty regular GitHub CLI login file required"
        return 1
    fi
    if ! awk '
        function trim(value) {
            sub(/^[[:space:]]+/, "", value)
            sub(/[[:space:]]+$/, "", value)
            return value
        }
        function token_is_invalid(value, lower) {
            value = trim(value)
            sub(/[[:space:]]+#.*/, "", value)
            value = trim(value)
            if (value == "" || value ~ /^#/) return 1
            if (value == "\"\"" || value == "\047\047") return 1
            lower = tolower(value)
            if (lower == "null" || value == "~") return 1
            if (substr(value, 1, 1) == "|" ||
                substr(value, 1, 1) == ">") return 1
            return 0
        }
        BEGIN {
            github_blocks = 0
            in_github = 0
            token_keys = 0
            invalid_tokens = 0
        }
        /^[^[:space:]#]/ {
            if ($0 ~ /^github[.]com:[[:space:]]*(#.*)?$/) {
                github_blocks++
                in_github = 1
            } else {
                in_github = 0
            }
        }
        in_github && /^[[:space:]]+oauth_token[[:space:]]*:/ {
            value = $0
            sub(/^[[:space:]]+oauth_token[[:space:]]*:[[:space:]]*/, "", value)
            token_keys++
            if (token_is_invalid(value)) invalid_tokens++
        }
        END {
            if (github_blocks != 1 || token_keys < 1 || invalid_tokens != 0)
                exit 1
            exit 0
        }
    ' "$root/hosts.yml" >/dev/null 2>&1; then
        report BLOCK "$label-auth" "$root/hosts.yml" \
            "keyring-only login is not persistent; use --insecure-storage"
        return 1
    fi
    return 0
)

validate_storage_rules() (
    codex_root=$1
    github_root=$2
    label=$3
    validate_codex_storage_rules "$codex_root" "$label-codex" || return 1
    validate_github_storage_rules "$github_root" "$label-github" || return 1
)

codex_auth_status() (
    binary=$1
    root=$2
    CODEX_HOME="$root" "$binary" login status >/dev/null 2>&1
)

github_auth_status() (
    binary=$1
    root=$2
    unset GH_TOKEN GITHUB_TOKEN GH_ENTERPRISE_TOKEN GITHUB_ENTERPRISE_TOKEN
    GH_CONFIG_DIR="$root" "$binary" auth status --hostname github.com --active \
        >/dev/null 2>&1 || return 1
    credential_source=$(
        GH_CONFIG_DIR="$root" "$binary" auth status \
            --hostname github.com \
            --active \
            --json hosts \
            --jq '.hosts | add | map(select(.active == true))[0].tokenSource' \
            2>/dev/null
    ) || return 1
    [ "$credential_source" = "$root/hosts.yml" ]
)

resolve_persistent_git_config() {
    EFFECTIVE_GIT_CONFIG=
    if [ ! -f "$GIT_CONFIG_SOURCE" ]; then
        report BLOCK git-config "$GIT_CONFIG_SOURCE" \
            "regular persistent Git config or symlink required"
        return 1
    fi
    git_config_canonical=$(readlink -f "$GIT_CONFIG_SOURCE" 2>/dev/null || true)
    if [ -z "$git_config_canonical" ]; then
        report BLOCK git-config "$GIT_CONFIG_SOURCE" \
            "cannot resolve persistent Git config"
        return 1
    fi
    validate_safe_path git-config-target "$git_config_canonical" || return 1
    if [ ! -f "$git_config_canonical" ] || [ -L "$git_config_canonical" ]; then
        report BLOCK git-config "$git_config_canonical" \
            "canonical target must be a regular file"
        return 1
    fi
    if ! is_test_mode; then
        case "$git_config_canonical" in
            /data/*|/config/*|/share/*) ;;
            *)
                report BLOCK git-config "$GIT_CONFIG_SOURCE" \
                    "must resolve below /data, /config or /share"
                return 1
                ;;
        esac
    fi
    EFFECTIVE_GIT_CONFIG=$git_config_canonical
    return 0
}

git_helper_value_migratable() {
    helper_value=$1
    [ -z "$helper_value" ] && return 0
    [ "$helper_value" = "$GIT_HELPER_VALUE" ] && return 0
    printf "%s\n" "$helper_value" |
        grep -Eq "^!([^[:space:]]*/)?gh auth git-credential$"
}

git_helper_key_is_migratable() (
    helper_key=$1
    config_path=${2:-$EFFECTIVE_GIT_CONFIG}
    helper_values=$(git config --file "$config_path" \
        --get-all "$helper_key" 2>/dev/null)
    git_status=$?
    case "$git_status" in
        0) ;;
        1) return 0 ;;
        *)
            report BLOCK git-helper "$helper_key" \
                "cannot inspect existing global helper values"
            return 1
            ;;
    esac
    if ! printf "%s\n" "$helper_values" |
        while IFS= read -r helper_value
        do
            git_helper_value_migratable "$helper_value" || exit 1
        done; then
        report BLOCK git-helper "$helper_key" \
            "foreign credential helper is preserved; refusing automatic change"
        return 1
    fi
    return 0
)

preflight_git_credential_helpers() {
    resolve_persistent_git_config || return 1
    git_helper_key_is_migratable "$GITHUB_GIT_HELPER_KEY" || return 1
    git_helper_key_is_migratable "$GIST_GIT_HELPER_KEY" || return 1
    report OK git-config "$GIT_CONFIG_SOURCE" \
        "canonical persistent target: $EFFECTIVE_GIT_CONFIG"
}

git_helper_key_matches() (
    helper_key=$1
    config_path=${2:-$EFFECTIVE_GIT_CONFIG}
    helper_values=$(git config --file "$config_path" \
        --get-all "$helper_key" 2>/dev/null) || return 1
    expected_values=$(printf "\n%s" "$GIT_HELPER_VALUE") || return 1
    [ "$helper_values" = "$expected_values" ] || return 1
    helper_count=$(git config --file "$config_path" \
        --get-all "$helper_key" 2>/dev/null | wc -l | tr -d " ") || return 1
    [ "$helper_count" -eq 2 ] 2>/dev/null
)

git_credential_helpers_match_file() {
    config_path=$1
    git_helper_key_matches "$GITHUB_GIT_HELPER_KEY" "$config_path" &&
        git_helper_key_matches "$GIST_GIT_HELPER_KEY" "$config_path"
}

git_credential_helpers_match_current() {
    [ -n "$EFFECTIVE_GIT_CONFIG" ] || return 1
    git_credential_helpers_match_file "$EFFECTIVE_GIT_CONFIG"
}

cleanup_git_helper_update() {
    cleanup_status=0
    if [ -n "${git_update_temp:-}" ]; then
        rm -f -- "$git_update_temp" || cleanup_status=1
    fi
    if [ "${git_lock_owned:-no}" = yes ] &&
        [ -n "${git_lock_path:-}" ] && [ -n "${git_lock_anchor:-}" ]; then
        lock_identity=$(stat -c "%d:%i" "$git_lock_path" 2>/dev/null || true)
        anchor_identity=$(stat -c "%d:%i" "$git_lock_anchor" 2>/dev/null || true)
        if [ -n "$lock_identity" ] && [ "$lock_identity" = "$anchor_identity" ]; then
            rm -f -- "$git_lock_path" || cleanup_status=1
        else
            cleanup_status=1
        fi
    fi
    if [ -n "${git_lock_anchor:-}" ]; then
        rm -f -- "$git_lock_anchor" || cleanup_status=1
    fi
    return "$cleanup_status"
}

ensure_git_credential_helpers() (
    preflight_git_credential_helpers || return 1
    if git_credential_helpers_match_current; then
        report OK git-helper "$EFFECTIVE_GIT_CONFIG" \
            "GitHub and Gist use the persistent gh command"
        return 0
    fi

    source_config=$EFFECTIVE_GIT_CONFIG
    source_parent=$(dirname "$source_config")
    source_identity=$(stat -c "%d:%i" "$source_config") || return 1
    source_hash=$(sha256sum "$source_config" | awk "{print \$1}") || return 1
    source_metadata=$(stat -c "%a:%u:%g" "$source_config") || return 1
    git_lock_path=$source_config.lock
    git_lock_owned=no

    if path_exists "$git_lock_path"; then
        report BLOCK git-helper "$git_lock_path" \
            "Git config is already locked; nothing was changed"
        return 1
    fi
    git_lock_anchor=$(mktemp "$source_parent/.hacp-git-lock.XXXXXX") || return 1
    git_update_temp=$(mktemp "$source_parent/.hacp-git-update.XXXXXX") || {
        rm -f -- "$git_lock_anchor"
        return 1
    }
    trap "cleanup_git_helper_update" 0 1 2 3 15
    chmod 600 "$git_lock_anchor" "$git_update_temp" || return 1
    if ! ln "$git_lock_anchor" "$git_lock_path"; then
        report BLOCK git-helper "$git_lock_path" \
            "could not reserve the standard Git config lock"
        return 1
    fi
    git_lock_owned=yes

    current_identity=$(stat -c "%d:%i" "$source_config" 2>/dev/null || true)
    git_helper_key_is_migratable \
        "$GITHUB_GIT_HELPER_KEY" "$source_config" || return 1
    git_helper_key_is_migratable \
        "$GIST_GIT_HELPER_KEY" "$source_config" || return 1
    current_hash=$(sha256sum "$source_config" | awk "{print \$1}") || return 1
    if [ "$current_identity" != "$source_identity" ] ||
        [ "$current_hash" != "$source_hash" ]; then
        report BLOCK git-helper "$source_config" \
            "Git config changed while the lock was acquired; nothing was overwritten"
        return 1
    fi

    cp -p "$source_config" "$git_update_temp" || return 1
    [ "$(sha256sum "$git_update_temp" | awk "{print \$1}")" = \
        "$source_hash" ] || return 1
    git_helper_key_is_migratable \
        "$GITHUB_GIT_HELPER_KEY" "$git_update_temp" || return 1
    git_helper_key_is_migratable \
        "$GIST_GIT_HELPER_KEY" "$git_update_temp" || return 1
    for helper_key in "$GITHUB_GIT_HELPER_KEY" "$GIST_GIT_HELPER_KEY"
    do
        git config --file "$git_update_temp" --replace-all \
            "$helper_key" "" &&
            git config --file "$git_update_temp" --add \
                "$helper_key" "$GIT_HELPER_VALUE" || {
            report BLOCK git-helper "$helper_key" \
                "targeted reset-and-helper update failed in private copy"
            return 1
        }
    done
    if ! git_credential_helpers_match_file "$git_update_temp"; then
        report BLOCK git-helper "$git_update_temp" \
            "exact helper verification failed in private copy"
        return 1
    fi
    [ "$(stat -c "%a:%u:%g" "$git_update_temp")" = "$source_metadata" ] || {
        report BLOCK git-helper "$git_update_temp" \
            "private copy did not preserve mode or ownership"
        return 1
    }
    sync "$git_update_temp" 2>/dev/null || sync || return 1

    git_helper_key_is_migratable \
        "$GITHUB_GIT_HELPER_KEY" "$source_config" || return 1
    git_helper_key_is_migratable \
        "$GIST_GIT_HELPER_KEY" "$source_config" || return 1
    current_identity=$(stat -c "%d:%i" "$source_config" 2>/dev/null || true)
    current_hash=$(sha256sum "$source_config" | awk "{print \$1}") || return 1
    lock_identity=$(stat -c "%d:%i" "$git_lock_path" 2>/dev/null || true)
    anchor_identity=$(stat -c "%d:%i" "$git_lock_anchor" 2>/dev/null || true)
    if [ "$current_identity" != "$source_identity" ] ||
        [ "$current_hash" != "$source_hash" ] ||
        [ -z "$lock_identity" ] || [ "$lock_identity" != "$anchor_identity" ]; then
        report BLOCK git-helper "$source_config" \
            "source or owned lock changed before publication; nothing was overwritten"
        return 1
    fi

    mv "$git_update_temp" "$source_config" || return 1
    sync "$source_config" "$source_parent" 2>/dev/null || sync || return 1
    git_update_temp=
    if ! git_credential_helpers_match_file "$source_config"; then
        report BLOCK git-helper "$source_config" \
            "published helper verification failed"
        return 1
    fi
    cleanup_git_helper_update || return 1
    git_lock_owned=no
    git_lock_anchor=
    trap - 0 1 2 3 15
    report OK git-helper "$source_config" \
        "only GitHub and Gist helper keys migrated atomically to persistent gh"
)

audit_git_credential_helpers() {
    if resolve_persistent_git_config &&
        git_credential_helpers_match_current; then
        report OK git-helper "$EFFECTIVE_GIT_CONFIG" \
            "exact persistent GitHub and Gist helpers active"
        return 0
    fi
    report BLOCK git-helper "$GIT_CONFIG_SOURCE" \
        "exact persistent GitHub or Gist helper missing"
    return 1
}

safe_remove_work_path() {
    candidate=$1
    case "$candidate" in
        "$RUNTIME_ROOT"/.hacp-work-*)
            path_exists "$candidate" && rm -rf -- "$candidate"
            ;;
        *)
            report BLOCK cleanup "$candidate" "refusing unexpected path"
            return 1
            ;;
    esac
}

codex_transient_paths_valid() (
    tree=$1

    for socket_path in \
        "$tree/ipc.sock" \
        "$tree/ipc/ipc.sock"
    do
        if path_exists "$socket_path"; then
            [ ! -L "$socket_path" ] && [ -S "$socket_path" ] || return 1
        fi
    done

    if path_exists "$tree/ipc"; then
        [ -d "$tree/ipc" ] && [ ! -L "$tree/ipc" ] || return 1
    fi
    if path_exists "$tree/tmp"; then
        [ -d "$tree/tmp" ] && [ ! -L "$tree/tmp" ] || return 1
    fi
    return 0
)

# Codex owns transient Unix sockets and Argo runtime directories here.
# Their contents and parent-directory metadata are not durable state.
tree_manifest() (
    tree=$1
    output=$2
    [ -d "$tree" ] && [ ! -L "$tree" ] || return 1
    codex_transient_paths_valid "$tree" || return 3

    special=$(
        cd "$tree" &&
            find . -mindepth 1 \
                \( -path './ipc' -o -path './ipc.sock' -o -path './tmp' \) \
                -prune -o \
                ! -type d ! -type f ! -type l \
                -print -quit
    ) || return 1
    [ -z "$special" ] || return 2

    (
        cd "$tree" || exit 1
        {
            find . -mindepth 1 \
                \( -path './ipc' -o -path './ipc.sock' -o -path './tmp' \) \
                -prune -o \
                -printf '%y\t%m\t%U:%G\t%P\t%l\n'
            find . \
                \( -path './ipc' -o -path './ipc.sock' -o -path './tmp' \) \
                -prune -o \
                -type f -exec sha256sum -- '{}' \;
        } | LC_ALL=C sort
    ) > "$output"
)

copy_native_tree() (
    source_path=$1
    destination=$2
    codex_transient_paths_valid "$source_path" || return 3
    (
        cd "$source_path" || exit 1
        tar \
            --exclude='./ipc' \
            --exclude='./ipc.sock' \
            --exclude='./tmp' \
            -cpf - .
    ) | (
        cd "$destination" || exit 1
        tar -xpf -
    )
)

copy_stable_tree() (
    source_path=$1
    destination=$2
    manifest_output=$3
    label=$4
    attempt=1

    while [ "$attempt" -le "$MAX_COPY_ATTEMPTS" ]
    do
        work=$(mktemp -d "$RUNTIME_ROOT/.hacp-work-${label}.XXXXXX") ||
            return 1
        chmod 700 "$work" || return 1
        stage=$work/tree
        mkdir "$stage" || return 1
        chmod 700 "$stage" || return 1

        tree_manifest "$source_path" "$work/before.tree"
        manifest_status=$?
        if [ "$manifest_status" -eq 3 ]; then
            report BLOCK "$label-copy" "$source_path/ipc/ipc.sock" \
                "reserved path is not a live Unix socket"
            safe_remove_work_path "$work" || true
            return 1
        fi
        if [ "$manifest_status" -eq 2 ]; then
            report BLOCK "$label-copy" "$source_path" \
                "unsupported socket/device/FIFO outside ipc/ipc.sock"
            safe_remove_work_path "$work" || true
            return 1
        fi
        if [ "$manifest_status" -ne 0 ]; then
            report BLOCK "$label-copy" "$source_path" "cannot inventory source"
            safe_remove_work_path "$work" || true
            return 1
        fi

        if copy_native_tree "$source_path" "$stage" &&
            tree_manifest "$source_path" "$work/after.tree" &&
            tree_manifest "$stage" "$work/copied.tree" &&
            cmp -s "$work/before.tree" "$work/after.tree" &&
            cmp -s "$work/before.tree" "$work/copied.tree"; then
            sleep 1
            if tree_manifest "$source_path" "$work/quiet.tree" &&
                cmp -s "$work/after.tree" "$work/quiet.tree"; then
                if path_exists "$destination"; then
                    report BLOCK "$label-copy" "$destination" \
                        "destination already exists"
                    safe_remove_work_path "$work" || true
                    return 1
                fi
                mv "$stage" "$destination" || {
                    safe_remove_work_path "$work" || true
                    return 1
                }
                cp "$work/copied.tree" "$manifest_output" || return 1
                chmod 600 "$manifest_output" || return 1
                safe_remove_work_path "$work" || true
                report OK "$label-copy" "$destination" \
                    "stable verified native copy"
                return 0
            fi
        fi
        report WARN "$label-copy" "$source_path" \
            "source changed; retry $attempt/$MAX_COPY_ATTEMPTS"
        safe_remove_work_path "$work" || true
        attempt=$((attempt + 1))
    done
    report BLOCK "$label-copy" "$source_path" \
        "no stable copy; source remains untouched"
    return 1
)

copy_stable_binary() {
    source_path=$1
    destination=$2
    label=$3

    [ -f "$source_path" ] && [ ! -L "$source_path" ] &&
        [ -x "$source_path" ] || {
        report BLOCK "$label-tool" "$source_path" \
            "resolved executable is not a regular executable file"
        return 1
    }
    before=$(sha256sum "$source_path" | awk '{print $1}') || return 1
    cp "$source_path" "$destination" || return 1
    chmod 755 "$destination" || return 1
    after=$(sha256sum "$source_path" | awk '{print $1}') || return 1
    copied=$(sha256sum "$destination" | awk '{print $1}') || return 1
    if [ "$before" != "$after" ] || [ "$before" != "$copied" ]; then
        report BLOCK "$label-tool" "$source_path" \
            "executable changed during copy"
        return 1
    fi
    if ! "$destination" --version >/dev/null 2>&1; then
        report BLOCK "$label-tool" "$destination" \
            "persistent executable failed version check"
        return 1
    fi
    report OK "$label-tool" "$destination" "persistent executable verified"
    return 0
}

codex_process_present() (
    is_test_mode && [ "${HACP_SKIP_PROCESS_CHECK:-}" = YES ] &&
        return 1
    for comm_file in /proc/[0-9]*/comm
    do
        [ -r "$comm_file" ] || continue
        IFS= read -r process_name < "$comm_file" || continue
        case "$process_name" in
            codex|codex-*) return 0 ;;
        esac
    done
    return 1
)

code_server_process_present() (
    is_test_mode && [ "${HACP_SKIP_PROCESS_CHECK:-}" = YES ] &&
        return 1
    for comm_file in /proc/[0-9]*/comm
    do
        [ -r "$comm_file" ] || continue
        IFS= read -r process_name < "$comm_file" || continue
        case "$process_name" in
            code-server) return 0 ;;
            node)
                cmdline_file=${comm_file%/comm}/cmdline
                [ -r "$cmdline_file" ] || continue
                process_args=$(tr '\000' ' ' < "$cmdline_file" 2>/dev/null) ||
                    continue
                case "$process_args" in
                    *"/code-server/"*|*" code-server "*) return 0 ;;
                esac
                ;;
        esac
    done
    return 1
)

write_generation_marker() {
    marker_path=$1
    generation=$2
    case "$marker_path" in
        "$ACTIVE_MARKER"|"$READY_MARKER") ;;
        *) return 1 ;;
    esac
    marker_name=$(basename "$marker_path")
    temporary=$STATE_ROOT/.$marker_name-$$
    printf '%s\n' "$generation" > "$temporary" || return 1
    chmod 600 "$temporary" || return 1
    mv "$temporary" "$marker_path" || return 1
}

write_active_marker() {
    write_generation_marker "$ACTIVE_MARKER" "$1"
}

write_ready_marker() {
    write_generation_marker "$READY_MARKER" "$1"
}

read_generation_marker() {
    marker_path=$1
    case "$marker_path" in
        "$ACTIVE_MARKER"|"$READY_MARKER") ;;
        *) return 1 ;;
    esac
    [ -f "$marker_path" ] && [ ! -L "$marker_path" ] || return 1
    generation=$(sed -n '1p' "$marker_path" 2>/dev/null) || return 1
    case "$generation" in
        ''|*[!A-Za-z0-9._-]*) return 1 ;;
    esac
    [ "$(wc -l < "$marker_path" | tr -d ' ')" -eq 1 ] 2>/dev/null ||
        return 1
    printf '%s\n' "$generation"
}

read_active_marker() {
    read_generation_marker "$ACTIVE_MARKER"
}

read_ready_marker() {
    read_generation_marker "$READY_MARKER"
}

remove_ready_marker() {
    if [ -L "$READY_MARKER" ]; then
        return 1
    fi
    [ -e "$READY_MARKER" ] || return 0
    [ -f "$READY_MARKER" ] || return 1
    rm -- "$READY_MARKER"
}

read_current_generation() {
    [ -f "$CURRENT_GENERATION" ] && [ ! -L "$CURRENT_GENERATION" ] ||
        return 1
    generation=$(sed -n '1p' "$CURRENT_GENERATION" 2>/dev/null) || return 1
    case "$generation" in
        ''|*[!A-Za-z0-9._-]*) return 1 ;;
    esac
    [ "$(wc -l < "$CURRENT_GENERATION" | tr -d ' ')" -eq 1 ] \
        2>/dev/null || return 1
    printf '%s\n' "$generation"
}

verify_current_runtime() {
    [ -d "$CURRENT_ROOT" ] && [ ! -L "$CURRENT_ROOT" ] || return 1
    for directory in "$CODEX_TARGET" "$GH_TARGET" "$META_ROOT" "$TOOLS_ROOT"
    do
        [ -d "$directory" ] && [ ! -L "$directory" ] || return 1
    done
    for metadata in \
        "$CODEX_MANIFEST" "$GH_MANIFEST" "$META_SUMS" "$CURRENT_GENERATION"
    do
        [ -s "$metadata" ] && [ -f "$metadata" ] &&
            [ ! -L "$metadata" ] || return 1
    done
    (
        cd "$META_ROOT" || exit 1
        sha256sum generation codex.tree github.tree |
            cmp -s - SHA256SUMS
    ) || return 1
    [ -x "$CODEX_TOOL" ] && [ ! -L "$CODEX_TOOL" ] || return 1
    [ -x "$GH_TOOL" ] && [ ! -L "$GH_TOOL" ] || return 1
    [ -f "$TOOLS_ROOT/SHA256SUMS" ] &&
        [ ! -L "$TOOLS_ROOT/SHA256SUMS" ] || return 1
    (
        cd "$TOOLS_ROOT" || exit 1
        sha256sum bin/codex bin/gh |
            cmp -s - SHA256SUMS
    ) || return 1
    "$CODEX_TOOL" --version >/dev/null 2>&1 || return 1
    "$GH_TOOL" --version >/dev/null 2>&1 || return 1
    return 0
}

verify_generation_identity() {
    expected=$1
    actual=$(read_current_generation 2>/dev/null) || return 1
    [ "$actual" = "$expected" ] || {
        report BLOCK generation "$CURRENT_GENERATION" \
            "metadata generation does not match state marker"
        return 1
    }
}

verify_tree_against_manifest() {
    tree=$1
    stored_manifest=$2
    label=$3
    work=$(mktemp -d "$RUNTIME_ROOT/.hacp-work-verify.XXXXXX") || return 1
    chmod 700 "$work" || return 1
    tree_manifest "$tree" "$work/current.tree"
    manifest_status=$?
    if [ "$manifest_status" -ne 0 ]; then
        report BLOCK "$label-manifest" "$tree" \
            "cannot safely inventory persistent tree"
        safe_remove_work_path "$work" || true
        return 1
    fi
    if ! cmp -s "$stored_manifest" "$work/current.tree"; then
        report BLOCK "$label-manifest" "$tree" \
            "tree differs from sealed READY manifest"
        safe_remove_work_path "$work" || true
        return 1
    fi
    safe_remove_work_path "$work" || true
    report OK "$label-manifest" "$tree" "matches sealed READY manifest"
}

verify_ready_runtime() {
    generation=$1
    verify_current_runtime || return 1
    verify_generation_identity "$generation" || return 1
    validate_storage_rules "$CODEX_TARGET" "$GH_TARGET" ready || return 1
    verify_tree_against_manifest \
        "$CODEX_TARGET" "$CODEX_MANIFEST" codex || return 1
    verify_tree_against_manifest \
        "$GH_TARGET" "$GH_MANIFEST" github || return 1
}

verify_active_runtime() {
    generation=$1
    verify_current_runtime || return 1
    verify_generation_identity "$generation" || return 1
    validate_storage_rules "$CODEX_TARGET" "$GH_TARGET" active || return 1
}

publish_ready_generation() {
    generation=$1
    sync "$CURRENT_ROOT" "$BOOTSTRAP_ROOT" 2>/dev/null || sync || return 1
    write_ready_marker "$generation" || return 1
    sync "$STATE_ROOT" 2>/dev/null || sync
}

promote_active_generation() {
    generation=$1
    write_active_marker "$generation" || return 1
    remove_ready_marker || return 1
    sync "$STATE_ROOT" 2>/dev/null || sync
}

source_matches_target() {
    source_path=$1
    target_path=$2
    label=$3

    work=$(mktemp -d "$RUNTIME_ROOT/.hacp-work-match.XXXXXX") || return 1
    tree_manifest "$source_path" "$work/source.tree" || {
        safe_remove_work_path "$work" || true
        return 1
    }
    tree_manifest "$target_path" "$work/target.tree" || {
        safe_remove_work_path "$work" || true
        return 1
    }
    if cmp -s "$work/source.tree" "$work/target.tree"; then
        safe_remove_work_path "$work" || true
        report OK "$label-match" "$source_path" \
            "persistent target is byte-identical"
        return 0
    fi
    safe_remove_work_path "$work" || true
    report BLOCK "$label-match" "$source_path" \
        "source and persistent target differ"
    return 1
}

preflight_link_path() {
    link_path=$1
    expected_target=$2
    label=$3
    allow_matching_directory=$4

    if [ -L "$link_path" ]; then
        link_target=$(readlink "$link_path" 2>/dev/null || true)
        [ "$link_target" = "$expected_target" ] && return 0
        report BLOCK "$label-link" "$link_path" \
            "unexpected symlink target: ${link_target:-unreadable}"
        return 1
    fi
    if ! path_exists "$link_path"; then
        return 0
    fi
    if [ "$allow_matching_directory" = yes ] && [ -d "$link_path" ]; then
        if ! is_nonempty_dir "$link_path"; then
            return 0
        fi
        source_matches_target "$link_path" "$expected_target" "$label"
        return $?
    fi
    report BLOCK "$label-link" "$link_path" \
        "existing path cannot be replaced automatically"
    return 1
}

replace_directory_with_link() {
    source_path=$1
    target_path=$2
    generation=$3
    label=$4
    LAST_BACKUP=

    if [ -L "$source_path" ]; then
        [ "$(readlink "$source_path" 2>/dev/null)" = "$target_path" ]
        return $?
    fi
    source_parent=$(dirname "$source_path")
    [ -d "$source_parent" ] || mkdir -p "$source_parent" || return 1
    [ ! -L "$source_parent" ] || return 1

    if [ -d "$source_path" ]; then
        if is_nonempty_dir "$source_path"; then
            LAST_BACKUP=$source_path.hacp-original-$generation
            path_exists "$LAST_BACKUP" && return 1
            mv "$source_path" "$LAST_BACKUP" || return 1
        else
            rmdir "$source_path" || return 1
        fi
    elif path_exists "$source_path"; then
        return 1
    fi

    if ln -s "$target_path" "$source_path"; then
        report OK "$label-link" "$source_path" "persistent via $target_path"
        return 0
    fi
    if [ -n "$LAST_BACKUP" ] && [ -d "$LAST_BACKUP" ]; then
        mv "$LAST_BACKUP" "$source_path" 2>/dev/null || true
    fi
    return 1
}

restore_directory_link_change() {
    source_path=$1
    backup_path=$2
    if [ -L "$source_path" ]; then
        rm -- "$source_path" || return 1
    fi
    if [ -n "$backup_path" ] && [ -d "$backup_path" ]; then
        mv "$backup_path" "$source_path" || return 1
    fi
}

ensure_tool_link() {
    link_path=$1
    target_path=$2
    label=$3
    if [ -L "$link_path" ]; then
        if [ "$(readlink "$link_path" 2>/dev/null)" = "$target_path" ]; then
            report OK "$label-link" "$link_path" "already persistent"
            return 0
        fi
        report BLOCK "$label-link" "$link_path" "unexpected symlink"
        return 1
    fi
    if path_exists "$link_path"; then
        report BLOCK "$label-link" "$link_path" \
            "existing non-link path; refusing overwrite"
        return 1
    fi
    [ -d "$(dirname "$link_path")" ] || return 1
    ln -s "$target_path" "$link_path" || return 1
    report OK "$label-link" "$link_path" "persistent via $target_path"
}

install_bootstrap_copy() {
    temporary=$BOOTSTRAP_ROOT/.ha-codex-persistence.sh-$$
    cp "$SCRIPT_PATH" "$temporary" || return 1
    chmod 700 "$temporary" || return 1
    mv "$temporary" "$BOOTSTRAP_SCRIPT" || return 1
}

boot_command() {
    printf "HACP_MANAGED=home-assistant-codex-persistence HACP_RUNTIME_ROOT=%s HACP_GIT_CONFIG_SOURCE=%s HACP_BOOT_OK=YES sh %s boot" \
        "$RUNTIME_ROOT" "$GIT_CONFIG_SOURCE" "$BOOTSTRAP_SCRIPT"
}

supervisor_token_valid() {
    token_value=${SUPERVISOR_TOKEN:-}
    [ -n "$token_value" ] || return 1
    invalid=$(printf '%s' "$token_value" | tr -d 'A-Za-z0-9._~=-') || return 1
    [ -z "$invalid" ]
}

supervisor_curl_request() (
    method=$1
    url=$2
    supervisor_token_valid || return 1
    token_value=$SUPERVISOR_TOKEN
    case "$method:$url" in
        GET:http://supervisor/addons/self/info|\
        POST:http://supervisor/addons/self/options) ;;
        *) return 1 ;;
    esac
    if [ "$method" = POST ]; then
        exec 3<&0
    fi
    unset SUPERVISOR_TOKEN

    if [ "$method" = GET ]; then
        printf 'header = "Authorization: Bearer %s"\n' "$token_value" |
            curl -q \
                --silent --show-error --fail \
                --noproxy '*' --proto '=http' --no-location \
                --connect-timeout 5 --max-time 20 --retry 0 \
                --config - \
                "$url"
    else
        printf 'header = "Authorization: Bearer %s"\n' "$token_value" |
            curl -q \
                --silent --show-error --fail \
                --noproxy '*' --proto '=http' --no-location \
                --connect-timeout 5 --max-time 20 --retry 0 \
                --config - \
                --request POST \
                --header 'Content-Type: application/json' \
                --data-binary @/proc/self/fd/3 \
                "$url"
    fi
)

supervisor_read_options() {
    supervisor_response=$(
        supervisor_curl_request GET http://supervisor/addons/self/info
    ) || return 1
    printf '%s' "$supervisor_response" |
        jq -e -S -c '
            if .result == "ok" and (.data.options | type) == "object" then
                .data.options
            else
                error("invalid Supervisor options response")
            end
        ' 2>/dev/null
}

configure_addon_startup() {
    command_text=$(boot_command)
    if is_test_mode &&
        [ "${HACP_SKIP_ADDON_CONFIG:-}" = YES ]; then
        report WARN addon-config init_commands \
            "test/manual mode; add this command: $command_text"
        return 0
    fi
    if ! supervisor_token_valid; then
        report BLOCK addon-config supervisor \
            "valid SUPERVISOR_TOKEN unavailable"
        return 1
    fi

    baseline=$(supervisor_read_options) || {
        report BLOCK addon-config supervisor \
            "could not read strict Supervisor option baseline"
        return 1
    }
    desired=$(
        printf '%s' "$baseline" |
            jq -e -S -c \
                --arg command "$command_text" \
                '
                    .packages = (
                        (.packages // [])
                        | if type == "array" then .
                          else error("packages must be an array") end
                        | map(select(. != "gh" and . != "github-cli"))
                    )
                    | .init_commands = (
                        [$command]
                        + (
                            (.init_commands // [])
                            | if type == "array" then .
                              else error("init_commands must be an array") end
                            | map(select(
                                (contains("HACP_MANAGED=home-assistant-codex-persistence")
                                 or contains("ha-codex-persistence.sh boot"))
                                | not
                            ))
                        )
                    )
                ' 2>/dev/null
    ) || {
        report BLOCK addon-config supervisor \
            "existing package or init-command options are not safely editable"
        return 1
    }

    if [ "$desired" = "$baseline" ]; then
        report OK addon-config init_commands \
            "automatic boot command already installed"
        return 0
    fi

    latest=$(supervisor_read_options) || {
        report BLOCK addon-config supervisor \
            "could not repeat strict Supervisor option read"
        return 1
    }
    if [ "$latest" != "$baseline" ]; then
        report BLOCK addon-config supervisor \
            "add-on options changed concurrently; no update was sent"
        return 1
    fi

    post_body=$(printf '%s' "$desired" | jq -e -c '{options: .}' 2>/dev/null) ||
        return 1
    response=$(
        printf '%s' "$post_body" |
            supervisor_curl_request POST http://supervisor/addons/self/options
    ) || {
        report BLOCK addon-config supervisor \
            "hardened Supervisor option update failed"
        return 1
    }
    if ! printf '%s' "$response" |
        jq -e '.result == "ok"' >/dev/null 2>&1; then
        report BLOCK addon-config supervisor \
            "Supervisor rejected the option update"
        return 1
    fi

    confirmed=$(supervisor_read_options) || {
        report BLOCK addon-config supervisor \
            "could not verify Supervisor options after update"
        return 1
    }
    if [ "$confirmed" != "$desired" ]; then
        report BLOCK addon-config supervisor \
            "Supervisor options differ after update; ACTIVE was not published"
        return 1
    fi
    report OK addon-config init_commands \
        "automatic boot command installed and read back"
}
memory_start_block() {
    printf '%s\n' \
        "$MEMORY_BLOCK_BEGIN" \
        "## Persistent manually maintained Codex long-term memory" \
        "1. At the start of every session, read \`$MEMORY_ROOT/AGENTS.md\` completely." \
        "2. Then read \`$MEMORY_ROOT/MEMORY.md\` completely." \
        "3. Apply the maintenance rules after confirmed durable decisions." \
        "$MEMORY_BLOCK_END"
}

legacy_memory_start_block() {
    printf '%s\n' \
        "$MEMORY_BLOCK_BEGIN" \
        "## Persistentes manuell gepflegtes Codex-Langzeitgedaechtnis" \
        "1. Bei jedem Sitzungsstart \`$MEMORY_ROOT/AGENTS.md\` vollstaendig lesen." \
        "2. Danach \`$MEMORY_ROOT/MEMORY.md\` vollstaendig lesen." \
        "3. Nach bestaetigten dauerhaften Entscheidungen die Pflegeregeln anwenden." \
        "$MEMORY_BLOCK_END"
}

memory_start_block_matches_expected() (
    agents_file=$1
    expected_command=$2
    [ -f "$agents_file" ] && [ ! -L "$agents_file" ] || return 1
    [ "$(stat -c '%h' "$agents_file" 2>/dev/null)" = 1 ] || return 1
    begin_count=$(grep -Fxc "$MEMORY_BLOCK_BEGIN" "$agents_file" || true)
    end_count=$(grep -Fxc "$MEMORY_BLOCK_END" "$agents_file" || true)
    [ "$begin_count" -eq 1 ] 2>/dev/null &&
        [ "$end_count" -eq 1 ] 2>/dev/null || return 1
    actual=$(
        awk -v begin="$MEMORY_BLOCK_BEGIN" -v end="$MEMORY_BLOCK_END" '
            $0 == begin { capture = 1 }
            capture { print }
            $0 == end && capture { capture = 0 }
        ' "$agents_file"
    ) || return 1
    expected=$($expected_command) || return 1
    [ "$actual" = "$expected" ]
)

memory_start_block_matches() {
    memory_start_block_matches_expected "$1" memory_start_block
}

legacy_memory_start_block_matches() {
    memory_start_block_matches_expected "$1" legacy_memory_start_block
}

supported_memory_start_block_matches() {
    memory_start_block_matches "$1" ||
        legacy_memory_start_block_matches "$1"
}

effective_global_agents_path() {
    codex_root=$1
    label=$2
    EFFECTIVE_GLOBAL_AGENTS=
    override_file=$codex_root/AGENTS.override.md
    agents_file=$codex_root/AGENTS.md

    for candidate in "$override_file" "$agents_file"
    do
        if [ -L "$candidate" ]; then
            report BLOCK "$label" "$candidate" "symlink is not accepted"
            return 1
        fi
        if path_exists "$candidate" && [ ! -f "$candidate" ]; then
            report BLOCK "$label" "$candidate" \
                "existing path is not a regular file"
            return 1
        fi
        if [ -f "$candidate" ] &&
            [ "$(stat -c '%h' "$candidate" 2>/dev/null)" != 1 ]; then
            report BLOCK "$label" "$candidate" \
                "hard-linked global instructions are not accepted"
            return 1
        fi
    done

    if [ -s "$override_file" ]; then
        EFFECTIVE_GLOBAL_AGENTS=$override_file
    else
        EFFECTIVE_GLOBAL_AGENTS=$agents_file
    fi
}

verify_effective_memory_start_rules() (
    codex_root=$1
    label=$2
    effective_global_agents_path "$codex_root" "$label" || return 1
    if ! supported_memory_start_block_matches "$EFFECTIVE_GLOBAL_AGENTS"; then
        report BLOCK "$label" "$EFFECTIVE_GLOBAL_AGENTS" \
            "supported exact effective global memory startup block missing"
        return 1
    fi
    report OK "$label" "$EFFECTIVE_GLOBAL_AGENTS" \
        "supported exact effective global memory startup block verified"
)

verify_memory_setup_read_only() (
    codex_root=$1
    label=$2
    case "$MEMORY_SETUP" in
        NO)
            report WARN "$label" "$WORKSPACE_ROOT" \
                "memory setup disabled explicitly"
            return 0
            ;;
        YES) ;;
        *)
            report BLOCK "$label" "$MEMORY_SETUP" "expected YES or NO"
            return 1
            ;;
    esac
    if [ ! -f "$MEMORY_ROOT/AGENTS.md" ] ||
        [ -L "$MEMORY_ROOT/AGENTS.md" ] ||
        [ ! -f "$MEMORY_ROOT/MEMORY.md" ] ||
        [ -L "$MEMORY_ROOT/MEMORY.md" ]; then
        report BLOCK "$label" "$MEMORY_ROOT" \
            "regular manual memory files required"
        return 1
    fi
    verify_effective_memory_start_rules "$codex_root" "$label" || return 1
)

install_memory_template() (
    source_file=$1
    destination=$2
    mode=$3
    label=$4

    if [ -L "$destination" ]; then
        report BLOCK "$label-memory" "$destination" \
            "symlink is not accepted"
        return 1
    fi
    if [ -f "$destination" ]; then
        report OK "$label-memory" "$destination" \
            "existing content preserved unchanged"
        return 0
    fi
    if path_exists "$destination"; then
        report BLOCK "$label-memory" "$destination" \
            "existing path is not a regular file"
        return 1
    fi
    if [ ! -f "$source_file" ] || [ -L "$source_file" ]; then
        report BLOCK "$label-memory" "$source_file" \
            "regular neutral template required"
        return 1
    fi

    temporary=$(mktemp "$MEMORY_ROOT/.hacp-memory.XXXXXX") || return 1
    trap "rm -f -- \"$temporary\"" 0 1 2 3 15
    cp "$source_file" "$temporary" || return 1
    chmod "$mode" "$temporary" || return 1
    chown 0:0 "$temporary" 2>/dev/null || {
        [ "${HACP_TEST_MODE:-}" = YES ] || return 1
    }
    sync "$temporary" 2>/dev/null || sync || return 1
    if ln "$temporary" "$destination"; then
        rm -f -- "$temporary" || return 1
        trap - 0 1 2 3 15
        report OK "$label-memory" "$destination" "neutral template installed"
        return 0
    fi

    rm -f -- "$temporary" || return 1
    trap - 0 1 2 3 15
    if [ -f "$destination" ] && [ ! -L "$destination" ]; then
        report OK "$label-memory" "$destination" \
            "content appeared concurrently and was preserved unchanged"
        return 0
    fi
    report BLOCK "$label-memory" "$destination" \
        "atomic no-clobber publication failed"
    return 1
)

ensure_memory_start_rules() (
    codex_root=$1
    effective_global_agents_path "$codex_root" memory-start || return 1
    root_agents=$EFFECTIVE_GLOBAL_AGENTS

    if [ -f "$root_agents" ]; then
        if memory_start_block_matches "$root_agents"; then
            report OK memory-start "$root_agents" \
                "exact global memory startup block already active"
            return 0
        fi
        if grep -F "$MEMORY_BLOCK_BEGIN" "$root_agents" >/dev/null 2>&1 ||
            grep -F "$MEMORY_BLOCK_END" "$root_agents" >/dev/null 2>&1; then
            report BLOCK memory-start "$root_agents" \
                "managed memory block is incomplete or differs"
            return 1
        fi

        before=$(sha256sum "$root_agents" | awk '{print $1}') || return 1
        if ! exec 8>>"$root_agents"; then
            report BLOCK memory-start "$root_agents" \
                "cannot open global instructions for append"
            return 1
        fi
        if ! flock -n 8; then
            report BLOCK memory-start "$root_agents" \
                "global instructions are locked by another writer"
            exec 8>&-
            return 1
        fi

        path_identity=$(
            stat -L -c '%d:%i' "$root_agents" 2>/dev/null
        ) || path_identity=
        descriptor_identity=$(
            stat -L -c '%d:%i' /proc/self/fd/8 2>/dev/null
        ) || descriptor_identity=
        path_links=$(stat -c '%h' "$root_agents" 2>/dev/null || true)
        descriptor_links=$(stat -L -c '%h' /proc/self/fd/8 2>/dev/null || true)
        if [ -z "$path_identity" ] ||
            [ "$path_identity" != "$descriptor_identity" ] ||
            [ "$path_links" != 1 ] || [ "$descriptor_links" != 1 ] ||
            [ ! -f "$root_agents" ] || [ -L "$root_agents" ]; then
            report BLOCK memory-start "$root_agents" \
                "global instructions changed while opening append-only handle"
            exec 8>&-
            return 1
        fi
        if ! effective_global_agents_path "$codex_root" memory-start ||
            [ "$EFFECTIVE_GLOBAL_AGENTS" != "$root_agents" ]; then
            report BLOCK memory-start "$root_agents" \
                "effective global instructions changed before append"
            exec 8>&-
            return 1
        fi
        if [ "$(sha256sum "$root_agents" | awk '{print $1}')" != "$before" ] ||
            grep -F "$MEMORY_BLOCK_BEGIN" "$root_agents" >/dev/null 2>&1 ||
            grep -F "$MEMORY_BLOCK_END" "$root_agents" >/dev/null 2>&1; then
            report BLOCK memory-start "$root_agents" \
                "global instructions changed before append; nothing was replaced"
            exec 8>&-
            return 1
        fi

        block=$(memory_start_block) || {
            exec 8>&-
            return 1
        }
        current_path_identity=$(stat -L -c '%d:%i' "$root_agents" 2>/dev/null || true)
        current_descriptor_identity=$(
            stat -L -c '%d:%i' /proc/self/fd/8 2>/dev/null
        ) || current_descriptor_identity=
        current_path_links=$(stat -c '%h' "$root_agents" 2>/dev/null || true)
        current_descriptor_links=$(
            stat -L -c '%h' /proc/self/fd/8 2>/dev/null
        ) || current_descriptor_links=
        if [ "$current_path_identity" != "$path_identity" ] ||
            [ "$current_descriptor_identity" != "$descriptor_identity" ] ||
            [ "$current_path_links" != 1 ] ||
            [ "$current_descriptor_links" != 1 ]; then
            report BLOCK memory-start "$root_agents" \
                "global instructions changed before append; nothing was replaced"
            exec 8>&-
            return 1
        fi
        if ! printf '\n%s\n' "$block" >&8; then
            exec 8>&-
            return 1
        fi
        sync "$root_agents" 2>/dev/null || sync || {
            exec 8>&-
            return 1
        }
        exec 8>&-
        if ! effective_global_agents_path "$codex_root" memory-start ||
            [ "$EFFECTIVE_GLOBAL_AGENTS" != "$root_agents" ] ||
            ! memory_start_block_matches "$root_agents"; then
            report BLOCK memory-start "$root_agents" \
                "effective global instructions changed during append"
            return 1
        fi
        report OK memory-start "$root_agents" \
            "exact global block append-only; existing bytes preserved"
        return 0
    fi

    temporary=$(mktemp "$codex_root/.hacp-agents.XXXXXX") || return 1
    trap "rm -f -- \"$temporary\"" 0 1 2 3 15
    memory_start_block > "$temporary" || return 1
    chmod 600 "$temporary" || return 1
    chown 0:0 "$temporary" 2>/dev/null || {
        [ "${HACP_TEST_MODE:-}" = YES ] || return 1
    }
    sync "$temporary" 2>/dev/null || sync || return 1
    if ln "$temporary" "$root_agents"; then
        rm -f -- "$temporary" || return 1
        trap - 0 1 2 3 15
        report OK memory-start "$root_agents" \
            "exact global memory startup block installed"
        return 0
    fi

    rm -f -- "$temporary" || return 1
    trap - 0 1 2 3 15
    if memory_start_block_matches "$root_agents"; then
        report OK memory-start "$root_agents" \
            "exact global block appeared concurrently"
        return 0
    fi
    report BLOCK memory-start "$root_agents" \
        "global instructions appeared concurrently; nothing was overwritten"
    return 1
)

setup_memory() (
    codex_root=$1
    case "$MEMORY_SETUP" in
        NO)
            report WARN memory "$WORKSPACE_ROOT" \
                "disabled explicitly with HACP_MEMORY_SETUP=NO"
            return 0
            ;;
        YES) ;;
        *)
            report BLOCK memory "$MEMORY_SETUP" "expected YES or NO"
            return 1
            ;;
    esac

    if [ ! -d "$codex_root" ] || [ -L "$codex_root" ]; then
        report BLOCK memory-codex-home "$codex_root" \
            "regular Codex home required for global startup instructions"
        return 1
    fi
    effective_global_agents_path "$codex_root" memory-start || return 1

    validate_safe_path workspace-root "$WORKSPACE_ROOT" || return 1
    if [ "${HACP_TEST_MODE:-}" != YES ]; then
        case "$WORKSPACE_ROOT" in
            /config/*|/share/*) ;;
            *)
                report BLOCK workspace-root "$WORKSPACE_ROOT" \
                    "expected persistent workspace below /config or /share"
                return 1
                ;;
        esac
    fi

    workspace_parent=$(dirname "$WORKSPACE_ROOT")
    if [ ! -d "$workspace_parent" ] || [ -L "$workspace_parent" ]; then
        report BLOCK workspace-root "$workspace_parent" \
            "regular persistent parent required"
        return 1
    fi
    workspace_parent_canonical=$(
        CDPATH= cd -- "$workspace_parent" && pwd -P
    ) || return 1
    workspace_canonical=$workspace_parent_canonical/$(basename "$WORKSPACE_ROOT")
    if [ -d "$WORKSPACE_ROOT" ] && [ ! -L "$WORKSPACE_ROOT" ]; then
        workspace_canonical=$(CDPATH= cd -- "$WORKSPACE_ROOT" && pwd -P) ||
            return 1
    fi
    if [ "$workspace_canonical" != "$WORKSPACE_ROOT" ]; then
        report BLOCK workspace-root "$WORKSPACE_ROOT" \
            "canonical path differs: $workspace_canonical"
        return 1
    fi
    case "$workspace_canonical" in
        "$PROJECT_ROOT"|"$PROJECT_ROOT"/*)
            report BLOCK workspace-root "$WORKSPACE_ROOT" \
                "persistent workspace must stay outside the installer checkout"
            return 1
            ;;
    esac
    if [ ! -d "$WORKSPACE_ROOT" ]; then
        if path_exists "$WORKSPACE_ROOT" || ! mkdir "$WORKSPACE_ROOT"; then
            report BLOCK workspace-root "$WORKSPACE_ROOT" "cannot create safely"
            return 1
        fi
        chmod 755 "$WORKSPACE_ROOT" || return 1
        chown 0:0 "$WORKSPACE_ROOT" 2>/dev/null || {
            [ "${HACP_TEST_MODE:-}" = YES ] || return 1
        }
    elif [ -L "$WORKSPACE_ROOT" ]; then
        report BLOCK workspace-root "$WORKSPACE_ROOT" "symlink is not accepted"
        return 1
    fi

    if [ ! -d "$MEMORY_ROOT" ]; then
        if path_exists "$MEMORY_ROOT" || ! mkdir "$MEMORY_ROOT"; then
            report BLOCK memory-root "$MEMORY_ROOT" "cannot create safely"
            return 1
        fi
        chmod 700 "$MEMORY_ROOT" || return 1
        chown 0:0 "$MEMORY_ROOT" 2>/dev/null || {
            [ "${HACP_TEST_MODE:-}" = YES ] || return 1
        }
    elif [ -L "$MEMORY_ROOT" ]; then
        report BLOCK memory-root "$MEMORY_ROOT" "symlink is not accepted"
        return 1
    fi

    template_root=${HACP_MEMORY_TEMPLATE_ROOT:-$SCRIPT_DIR/../examples/memory}
    if ! path_exists "$MEMORY_ROOT/AGENTS.md" ||
        ! path_exists "$MEMORY_ROOT/MEMORY.md"; then
        if [ ! -d "$template_root" ] || [ -L "$template_root" ]; then
            report BLOCK memory-template "$template_root" \
                "repository memory templates required for missing files"
            return 1
        fi
        template_root=$(CDPATH= cd -- "$template_root" && pwd -P) || return 1
        for template_file in AGENTS.md MEMORY.md
        do
            if [ ! -f "$template_root/$template_file" ] ||
                [ -L "$template_root/$template_file" ]; then
                report BLOCK memory-template "$template_root/$template_file" \
                    "regular neutral template required"
                return 1
            fi
        done
    fi

    install_memory_template \
        "$template_root/AGENTS.md" "$MEMORY_ROOT/AGENTS.md" 600 rules ||
        return 1
    install_memory_template \
        "$template_root/MEMORY.md" "$MEMORY_ROOT/MEMORY.md" 600 facts ||
        return 1
    ensure_memory_start_rules "$codex_root" || return 1
    report OK memory "$MEMORY_ROOT" \
        "persistent manual memory active; existing content was not copied"
)

runtime_links_active() {
    [ -L "$CODEX_SOURCE" ] &&
        [ "$(readlink "$CODEX_SOURCE" 2>/dev/null)" = "$CODEX_TARGET" ] &&
        [ -L "$GH_SOURCE" ] &&
        [ "$(readlink "$GH_SOURCE" 2>/dev/null)" = "$GH_TARGET" ] &&
        [ -L "$CODEX_LINK" ] &&
        [ "$(readlink "$CODEX_LINK" 2>/dev/null)" = "$CODEX_TOOL" ] &&
        [ -L "$GH_LINK" ] &&
        [ "$(readlink "$GH_LINK" 2>/dev/null)" = "$GH_TOOL" ]
}

activate_current_links() {
    generation=$1
    if runtime_links_active; then
        ensure_git_credential_helpers || return 1
        report OK cutover "$RUNTIME_ROOT" "persistent links already active"
        return 0
    fi
    if codex_process_present; then
        report BLOCK cutover-process codex \
            "Codex started during installation; close it and run install again"
        return 1
    fi
    if ! preflight_link_path "$CODEX_SOURCE" "$CODEX_TARGET" codex yes ||
        ! preflight_link_path "$GH_SOURCE" "$GH_TARGET" github yes ||
        ! preflight_link_path "$CODEX_LINK" "$CODEX_TOOL" codex-tool no ||
        ! preflight_link_path "$GH_LINK" "$GH_TOOL" github-tool no; then
        return 1
    fi
    if codex_process_present; then
        report BLOCK cutover-process codex \
            "Codex appeared after preflight; no paths were changed"
        return 1
    fi

    replace_directory_with_link \
        "$CODEX_SOURCE" "$CODEX_TARGET" "$generation" codex || return 1
    codex_backup=$LAST_BACKUP
    if ! replace_directory_with_link \
        "$GH_SOURCE" "$GH_TARGET" "$generation" github; then
        restore_directory_link_change "$CODEX_SOURCE" "$codex_backup" || true
        return 1
    fi
    ensure_tool_link "$CODEX_LINK" "$CODEX_TOOL" codex-tool || return 1
    ensure_tool_link "$GH_LINK" "$GH_TOOL" github-tool || return 1
    ensure_git_credential_helpers || return 1
    if codex_process_present; then
        report BLOCK cutover-process codex \
            "Codex appeared during cutover; ACTIVE was not published"
        return 1
    fi
    return 0
}

install_all() {
    if [ "${HACP_INSTALL_OK:-}" != YES ]; then
        report BLOCK install-context runtime "HACP_INSTALL_OK=YES is required"
        return 8
    fi
    check_tools || return "$EXIT_CODE"
    validate_configuration || return 5
    ensure_runtime_layout || return 8

    exec 9<"$LOCK_ROOT" || return 9
    if ! flock -n 9; then
        report BLOCK lock "$LOCK_ROOT" "another operation is active"
        return 9
    fi
    preflight_git_credential_helpers || return 8

    if generation=$(read_active_marker 2>/dev/null); then
        verify_active_runtime "$generation" || {
            report BLOCK install "$CURRENT_ROOT" \
                "active runtime verification failed"
            return 8
        }
        verify_memory_setup_read_only \
            "$CODEX_TARGET" memory-active || return 8
        if path_exists "$READY_MARKER"; then
            ready_generation=$(read_ready_marker 2>/dev/null) || {
                report BLOCK install "$READY_MARKER" "invalid READY marker"
                return 8
            }
            [ "$ready_generation" = "$generation" ] || {
                report BLOCK install "$STATE_ROOT" \
                    "ACTIVE and READY generations differ"
                return 8
            }
        fi
        install_bootstrap_copy || return 8
        configure_addon_startup || return 8
        activate_current_links "$generation" || return 8
        if path_exists "$READY_MARKER"; then
            remove_ready_marker || return 8
            sync "$STATE_ROOT" 2>/dev/null || sync || return 8
        fi
        report OK install "$RUNTIME_ROOT" \
            "already installed as generation $generation"
        return 0
    fi
    if path_exists "$ACTIVE_MARKER"; then
        report BLOCK install "$ACTIVE_MARKER" "invalid ACTIVE marker"
        return 8
    fi

    if path_exists "$CURRENT_ROOT"; then
        recovered_unmarked=no
        if generation=$(read_ready_marker 2>/dev/null); then
            :
        elif path_exists "$READY_MARKER"; then
            report BLOCK install "$READY_MARKER" "invalid READY marker"
            return 8
        else
            generation=$(read_current_generation 2>/dev/null) || {
                report BLOCK install "$CURRENT_ROOT" \
                    "unmarked runtime has no valid embedded generation"
                return 8
            }
            recovered_unmarked=yes
        fi
        verify_ready_runtime "$generation" || {
            report BLOCK install "$CURRENT_ROOT" \
                "READY runtime verification failed"
            return 8
        }
        verify_memory_setup_read_only \
            "$CODEX_TARGET" memory-ready || return 8
        install_bootstrap_copy || return 8
        if [ "$recovered_unmarked" = yes ]; then
            publish_ready_generation "$generation" || return 8
            report WARN install-recovery "$CURRENT_ROOT" \
                "published READY for fully verified unmarked runtime"
        fi
        configure_addon_startup || return 8
        activate_current_links "$generation" || return 8
        promote_active_generation "$generation" || return 8
        report OK install "$RUNTIME_ROOT" \
            "recovered verified READY generation $generation"
        return 0
    fi
    if path_exists "$READY_MARKER"; then
        report BLOCK install "$READY_MARKER" \
            "READY marker exists without a runtime"
        return 8
    fi

    if codex_process_present; then
        report BLOCK install-process codex \
            "close all Codex chats/processes, then run install from a normal terminal"
        return 8
    fi
    if [ -L "$CODEX_SOURCE" ] || [ ! -d "$CODEX_SOURCE" ] ||
        ! is_nonempty_dir "$CODEX_SOURCE"; then
        report BLOCK codex-source "$CODEX_SOURCE" \
            "installed and logged-in Codex home required"
        return 8
    fi
    if [ -L "$GH_SOURCE" ] || [ ! -d "$GH_SOURCE" ] ||
        ! is_nonempty_dir "$GH_SOURCE"; then
        report BLOCK github-source "$GH_SOURCE" \
            "installed and logged-in GitHub CLI config required"
        return 8
    fi

    codex_command=$(command -v codex 2>/dev/null || true)
    gh_command=$(command -v gh 2>/dev/null || true)
    [ -n "$codex_command" ] && [ -n "$gh_command" ] || {
        report BLOCK applications codex-gh \
            "codex and gh commands must both be installed"
        return 8
    }
    codex_binary=$(readlink -f "$codex_command" 2>/dev/null || true)
    gh_binary=$(readlink -f "$gh_command" 2>/dev/null || true)
    if [ -z "$codex_binary" ] || [ -z "$gh_binary" ]; then
        report BLOCK applications codex-gh \
            "cannot resolve installed executables"
        return 8
    fi

    ensure_codex_file_credentials_store || return 8
    validate_storage_rules "$CODEX_SOURCE" "$GH_SOURCE" install || return 8
    if ! codex_auth_status "$codex_binary" "$CODEX_SOURCE"; then
        report BLOCK codex-auth codex \
            "file-based login cache is not recognized"
        return 8
    fi
    if ! github_auth_status "$gh_binary" "$GH_SOURCE"; then
        report BLOCK github-auth github.com \
            "active login is invalid or not sourced from hosts.yml"
        return 8
    fi
    if codex_process_present; then
        report BLOCK install-process codex \
            "Codex started before the copy; close it and run install again"
        return 8
    fi

    if ! preflight_link_path "$CODEX_LINK" "$CODEX_TOOL" codex-tool no ||
        ! preflight_link_path "$GH_LINK" "$GH_TOOL" github-tool no; then
        return 8
    fi
    setup_memory "$CODEX_SOURCE" || return 8

    generation=$(date -u +%Y%m%dT%H%M%SZ)-$$
    stage=$(mktemp -d "$RUNTIME_ROOT/.hacp-work-install.XXXXXX") || return 8
    chmod 700 "$stage" || return 8
    mkdir "$stage/meta" "$stage/tools" "$stage/tools/bin" || return 8
    chmod 700 "$stage/meta" "$stage/tools" "$stage/tools/bin" || return 8

    copy_stable_tree \
        "$CODEX_SOURCE" "$stage/codex-home" "$stage/meta/codex.tree" codex ||
        return 8
    if [ "$MEMORY_SETUP" = YES ]; then
        verify_effective_memory_start_rules \
            "$stage/codex-home" memory-stage || return 8
    fi
    copy_stable_tree \
        "$GH_SOURCE" "$stage/gh" "$stage/meta/github.tree" github ||
        return 8
    copy_stable_binary "$codex_binary" "$stage/tools/bin/codex" codex ||
        return 8
    copy_stable_binary "$gh_binary" "$stage/tools/bin/gh" github ||
        return 8
    printf '%s\n' "$generation" > "$stage/meta/generation" || return 8
    chmod 600 "$stage/meta/generation" || return 8
    (
        cd "$stage/meta" || exit 1
        sha256sum generation codex.tree github.tree > SHA256SUMS
        chmod 600 SHA256SUMS
    ) || return 8
    (
        cd "$stage/tools" || exit 1
        sha256sum bin/codex bin/gh > SHA256SUMS
        chmod 600 SHA256SUMS
    ) || return 8

    if path_exists "$CURRENT_ROOT"; then
        report BLOCK install "$CURRENT_ROOT" \
            "target appeared during installation"
        return 8
    fi
    mv "$stage" "$CURRENT_ROOT" || return 8
    chmod 700 \
        "$CURRENT_ROOT" "$CODEX_TARGET" "$GH_TARGET" \
        "$META_ROOT" "$TOOLS_ROOT" "$TOOLS_BIN" || return 8
    chown 0:0 \
        "$CURRENT_ROOT" "$CODEX_TARGET" "$GH_TARGET" \
        "$META_ROOT" "$TOOLS_ROOT" "$TOOLS_BIN" 2>/dev/null || {
        is_test_mode || return 8
    }
    verify_ready_runtime "$generation" || {
        report BLOCK install "$CURRENT_ROOT" \
            "persistent READY runtime verification failed"
        return 8
    }
    source_matches_target "$CODEX_SOURCE" "$CODEX_TARGET" codex || return 8
    source_matches_target "$GH_SOURCE" "$GH_TARGET" github || return 8
    if ! codex_auth_status "$CODEX_TOOL" "$CODEX_TARGET"; then
        report BLOCK codex-auth "$CODEX_TARGET" \
            "persistent Codex login cache is not recognized"
        return 8
    fi
    if ! github_auth_status "$GH_TOOL" "$GH_TARGET"; then
        report BLOCK github-auth "$GH_TARGET" \
            "persistent active GitHub login is invalid or not file-based"
        return 8
    fi

    install_bootstrap_copy || return 8
    publish_ready_generation "$generation" || return 8
    configure_addon_startup || return 8
    activate_current_links "$generation" || return 8
    promote_active_generation "$generation" || return 8

    session_count=$(
        find "$CODEX_TARGET/sessions" -type f -name '*.jsonl' 2>/dev/null |
            wc -l | tr -d ' '
    )
    report OK install "$RUNTIME_ROOT" \
        "persistent now; ${session_count:-0} native session files; restart-safe"
    return 0
}

disposable_container_directory_on_boot() (
    source_path=$1
    label=$2

    [ -d "$source_path" ] && [ ! -L "$source_path" ] || return 1
    case "$label" in
        codex)
            codex_transient_paths_valid "$source_path" || return 1
            unexpected=$(
                cd "$source_path" &&
                    find . -mindepth 1 -maxdepth 1 \
                        ! -name ipc ! -name ipc.sock ! -name tmp \
                        -print -quit
            ) || return 1
            [ -z "$unexpected" ]
            ;;
        github)
            ! is_nonempty_dir "$source_path"
            ;;
        *) return 1 ;;
    esac
)

link_runtime_directory_on_boot() {
    source_path=$1
    target_path=$2
    generation=$3
    label=$4
    if [ -L "$source_path" ]; then
        if [ "$(readlink "$source_path" 2>/dev/null)" = "$target_path" ]; then
            report OK "$label-link" "$source_path" "already persistent"
            return 0
        fi
        report BLOCK "$label-link" "$source_path" "unexpected symlink"
        return 1
    fi
    if [ -d "$source_path" ] && ! is_nonempty_dir "$source_path"; then
        rmdir "$source_path" || return 1
    elif disposable_container_directory_on_boot "$source_path" "$label"; then
        # A fresh Studio Code Server container may create only these disposable
        # runtime paths before init_commands runs. rm removes links themselves
        # rather than their targets; all other non-empty paths are blocked below.
        rm -rf -- "$source_path" || return 1
        report WARN "$label-link" "$source_path" \
            "removed expected disposable container state"
    elif path_exists "$source_path"; then
        report BLOCK "$label-link" "$source_path" \
            "new container contains unexpected non-disposable state"
        return 1
    fi
    source_parent=$(dirname "$source_path")
    [ -d "$source_parent" ] || mkdir -p "$source_parent" || return 1
    ln -s "$target_path" "$source_path" || return 1
    report OK "$label-link" "$source_path" \
        "restored for generation $generation"
}

boot_all() {
    if [ "${HACP_BOOT_OK:-}" != YES ]; then
        report BLOCK boot-context runtime "HACP_BOOT_OK=YES is required"
        return 8
    fi
    check_tools || return "$EXIT_CODE"
    validate_configuration || return 5
    verify_runtime_layout || return 8

    exec 9<"$LOCK_ROOT" || return 9
    if ! flock -n 9; then
        report BLOCK lock "$LOCK_ROOT" "another operation is active"
        return 9
    fi
    preflight_git_credential_helpers || return 8
    if codex_process_present || code_server_process_present; then
        report BLOCK boot-process runtime \
            "Codex or actual code-server process already running"
        return 8
    fi

    if generation=$(read_active_marker 2>/dev/null); then
        verify_active_runtime "$generation" || {
            report BLOCK boot "$CURRENT_ROOT" \
                "active persistent runtime verification failed"
            return 8
        }
        if path_exists "$READY_MARKER"; then
            ready_generation=$(read_ready_marker 2>/dev/null) || {
                report BLOCK boot "$READY_MARKER" "invalid READY marker"
                return 8
            }
            [ "$ready_generation" = "$generation" ] || {
                report BLOCK boot "$STATE_ROOT" \
                    "ACTIVE and READY generations differ"
                return 8
            }
        fi
        link_runtime_directory_on_boot \
            "$CODEX_SOURCE" "$CODEX_TARGET" "$generation" codex || return 8
        link_runtime_directory_on_boot \
            "$GH_SOURCE" "$GH_TARGET" "$generation" github || return 8
        ensure_tool_link "$CODEX_LINK" "$CODEX_TOOL" codex-tool || return 8
        ensure_tool_link "$GH_LINK" "$GH_TOOL" github-tool || return 8
        ensure_git_credential_helpers || return 8
        if path_exists "$READY_MARKER"; then
            remove_ready_marker || return 8
            sync "$STATE_ROOT" 2>/dev/null || sync || return 8
        fi
        report OK boot "$RUNTIME_ROOT" \
            "persistent applications and state linked before code-server"
        return 0
    fi
    if path_exists "$ACTIVE_MARKER"; then
        report BLOCK boot "$ACTIVE_MARKER" "invalid ACTIVE marker"
        return 8
    fi

    recovered_unmarked=no
    if generation=$(read_ready_marker 2>/dev/null); then
        :
    elif path_exists "$READY_MARKER"; then
        report BLOCK boot "$READY_MARKER" "invalid READY marker"
        return 8
    elif path_exists "$CURRENT_ROOT"; then
        generation=$(read_current_generation 2>/dev/null) || {
            report BLOCK boot "$CURRENT_ROOT" \
                "unmarked runtime has no valid embedded generation"
            return 8
        }
        recovered_unmarked=yes
    else
        report BLOCK boot "$ACTIVE_MARKER" \
            "not installed; refusing to create empty persistent state"
        return 8
    fi

    verify_ready_runtime "$generation" || {
        report BLOCK boot "$CURRENT_ROOT" \
            "READY persistent runtime verification failed"
        return 8
    }
    if [ "$recovered_unmarked" = yes ]; then
        if ! preflight_link_path "$CODEX_SOURCE" "$CODEX_TARGET" codex yes ||
            ! preflight_link_path "$GH_SOURCE" "$GH_TARGET" github yes ||
            ! preflight_link_path "$CODEX_LINK" "$CODEX_TOOL" codex-tool no ||
            ! preflight_link_path "$GH_LINK" "$GH_TOOL" github-tool no; then
            return 8
        fi
        install_bootstrap_copy || return 8
        publish_ready_generation "$generation" || return 8
        report WARN boot-recovery "$CURRENT_ROOT" \
            "published READY for fully verified unmarked runtime"
    fi
    activate_current_links "$generation" || return 8
    promote_active_generation "$generation" || return 8
    report WARN boot-recovery "$RUNTIME_ROOT" \
        "promoted fully verified READY generation after successful cutover"
    report OK boot "$RUNTIME_ROOT" \
        "persistent applications and state linked before code-server"
    return 0
}

audit_symlink() {
    label=$1
    link_path=$2
    target_path=$3
    if [ ! -L "$link_path" ]; then
        report BLOCK "$label-link" "$link_path" "expected symlink missing"
        set_exit 1
        return
    fi
    actual=$(readlink "$link_path" 2>/dev/null || true)
    if [ "$actual" != "$target_path" ]; then
        report BLOCK "$label-link" "$link_path" \
            "points to ${actual:-unreadable}, expected $target_path"
        set_exit 1
        return
    fi
    report OK "$label-link" "$link_path" "persistent via $target_path"
}

audit_all() {
    check_tools || return "$EXIT_CODE"
    validate_configuration || return 5
    verify_runtime_layout || return 1
    generation=$(read_active_marker 2>/dev/null) || {
        report BLOCK install "$ACTIVE_MARKER" \
            "not installed; run install once after both logins"
        return 1
    }
    verify_current_runtime || {
        report BLOCK runtime "$CURRENT_ROOT" "verification failed"
        return 1
    }
    verify_generation_identity "$generation" || {
        report BLOCK runtime "$CURRENT_ROOT" "generation verification failed"
        return 1
    }
    if ! validate_storage_rules "$CODEX_TARGET" "$GH_TARGET" audit; then
        set_exit 1
    fi
    audit_symlink codex "$CODEX_SOURCE" "$CODEX_TARGET"
    audit_symlink github "$GH_SOURCE" "$GH_TARGET"
    audit_symlink codex-tool "$CODEX_LINK" "$CODEX_TOOL"
    audit_symlink github-tool "$GH_LINK" "$GH_TOOL"
    if ! audit_git_credential_helpers; then
        set_exit 1
    fi

    mode=$(dir_mode "$CURRENT_ROOT")
    owner=$(dir_owner "$CURRENT_ROOT")
    if [ "$mode" != 700 ] ||
        { [ "${HACP_TEST_MODE:-}" != YES ] && [ "$owner" != 0:0 ]; }; then
        report BLOCK permissions "$CURRENT_ROOT" \
            "expected root:root mode 0700, found $owner mode $mode"
        set_exit 1
    else
        report OK permissions "$CURRENT_ROOT" "root:root mode 0700"
    fi

    if [ -d "$CODEX_TARGET/sessions" ] &&
        [ ! -L "$CODEX_TARGET/sessions" ]; then
        session_count=$(
            find "$CODEX_TARGET/sessions" -type f -name '*.jsonl' 2>/dev/null |
                wc -l | tr -d ' '
        )
        if [ "${session_count:-0}" -gt 0 ] 2>/dev/null; then
            report OK sessions "$CODEX_TARGET/sessions" \
                "$session_count native session files"
        else
            report WARN sessions "$CODEX_TARGET/sessions" \
                "no native session file yet"
        fi
    else
        report WARN sessions "$CODEX_TARGET/sessions" \
            "session directory does not exist yet"
    fi

    if [ "$MEMORY_SETUP" = YES ]; then
        memory_valid=yes
        if [ ! -f "$MEMORY_ROOT/AGENTS.md" ] ||
            [ -L "$MEMORY_ROOT/AGENTS.md" ] ||
            [ ! -f "$MEMORY_ROOT/MEMORY.md" ] ||
            [ -L "$MEMORY_ROOT/MEMORY.md" ]; then
            memory_valid=no
        fi
        if [ "$memory_valid" = yes ]; then
            effective_global_agents_path "$CODEX_TARGET" memory-start ||
                memory_valid=no
        fi
        if [ "$memory_valid" = yes ] &&
            ! supported_memory_start_block_matches \
                "$EFFECTIVE_GLOBAL_AGENTS"; then
            memory_valid=no
        fi
        if [ "$memory_valid" = yes ]; then
            report OK memory "$MEMORY_ROOT" \
                "exact global startup and manual maintenance logic available"
        else
            report BLOCK memory "$MEMORY_ROOT" \
                "manual files or exact effective global startup block missing"
            set_exit 1
        fi
    else
        report WARN memory "$WORKSPACE_ROOT" "memory setup was disabled"
    fi

    if [ "${HACP_CHECK_AUTH:-}" = YES ]; then
        if codex_auth_status "$CODEX_TOOL" "$CODEX_TARGET"; then
            report OK codex-auth codex "file-based login cache recognized"
        else
            report BLOCK codex-auth codex "login cache unavailable"
            set_exit 4
        fi
        if github_auth_status "$GH_TOOL" "$GH_TARGET"; then
            report OK github-auth github.com \
                "active login valid and sourced from hosts.yml"
        else
            report BLOCK github-auth github.com \
                "active login invalid or not sourced from hosts.yml"
            set_exit 4
        fi
    else
        report WARN auth codex-github \
            "not checked; rerun audit with HACP_CHECK_AUTH=YES"
    fi

    if [ "$EXIT_CODE" -eq 0 ]; then
        report OK result active \
            "generation $generation survives container replacement"
    fi
    return "$EXIT_CODE"
}

usage() {
    printf '%s\n' \
        "Home Assistant Codex Persistence $PROGRAM_VERSION" \
        "" \
        "Run once after Codex and GitHub login:" \
        "  HACP_RUNTIME_ROOT=/persistent/path HACP_INSTALL_OK=YES $0 install" \
        "" \
        "Automatic init_commands entry:" \
        "  HACP_RUNTIME_ROOT=/persistent/path HACP_BOOT_OK=YES $0 boot" \
        "" \
        "Read-only check:" \
        "  HACP_RUNTIME_ROOT=/persistent/path $0 audit"
}

case "${1:-}" in
    install)
        [ "$#" -eq 1 ] || {
            usage >&2
            exit 2
        }
        install_all
        exit $?
        ;;
    boot)
        [ "$#" -eq 1 ] || {
            usage >&2
            exit 2
        }
        boot_all
        exit $?
        ;;
    audit)
        [ "$#" -eq 1 ] || {
            usage >&2
            exit 2
        }
        audit_all
        exit $?
        ;;
    --version)
        printf '%s\n' "$PROGRAM_VERSION"
        ;;
    *)
        usage >&2
        exit 2
        ;;
esac
