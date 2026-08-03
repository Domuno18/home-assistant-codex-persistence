"""Integration tests for the public install -> boot -> audit lifecycle."""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "ha-codex-persistence.sh"

FAKE_CODEX = """#!/bin/sh
case "${1:-}" in
    --version)
        printf '%s\\n' 'codex-fake 1.0'
        exit 0
        ;;
    login)
        if [ "${2:-}" = status ] &&
            [ -f "${CODEX_HOME:?}/auth.json" ]; then
            exit 0
        fi
        exit 1
        ;;
    *)
        exit 2
        ;;
esac
"""

FAKE_GH = """#!/bin/sh
case "${1:-}" in
    --version)
        printf "%s\\n" "gh-fake 1.0"
        exit 0
        ;;
    auth)
        if [ "${2:-}" = "git-credential" ]; then
            [ -f "${GH_CONFIG_DIR:?}/hosts.yml" ] || exit 1
            [ -n "${HACP_TEST_GIT_CREDENTIAL_LOG:-}" ] || exit 1
            case "${3:-}" in
                get|store|erase) ;;
                *) exit 1 ;;
            esac
            printf "%s|%s|%s\\n" "$0" "$GH_CONFIG_DIR" "$*" > \
                "$HACP_TEST_GIT_CREDENTIAL_LOG"
            while IFS= read -r credential_line
            do
                [ -n "$credential_line" ] || break
            done
            exit 0
        fi
        if [ "${2:-}" = "status" ] &&
            [ -f "${GH_CONFIG_DIR:?}/hosts.yml" ] &&
            [ -z "${GH_TOKEN:-}" ] && [ -z "${GITHUB_TOKEN:-}" ] &&
            [ -z "${GH_ENTERPRISE_TOKEN:-}" ] &&
            [ -z "${GITHUB_ENTERPRISE_TOKEN:-}" ]; then
            case " $* " in
                *" --active "*) ;;
                *) exit 1 ;;
            esac
            case " $* " in
                *" --hostname github.com "*) ;;
                *) exit 1 ;;
            esac
            for argument in "$@"
            do
                if [ "$argument" = "--json" ]; then
                    printf "%s\\n" \
                        "${HACP_TEST_GH_TOKEN_SOURCE:-$GH_CONFIG_DIR/hosts.yml}"
                    exit 0
                fi
            done
            exit 0
        fi
        exit 1
        ;;
    *)
        exit 2
        ;;
esac
"""

FAKE_SLEEP = """#!/bin/sh
exit 0
"""

FAKE_CURL = """#!/bin/sh
[ "${1:-}" = "-q" ] || exit 91
case " $* " in
    *test.only-token_123*|*supervisor-secret-sentinel*) exit 92 ;;
esac
shift
seen_silent=no
seen_show_error=no
seen_fail=no
seen_noproxy=no
seen_proto=no
seen_no_location=no
seen_connect_timeout=no
seen_max_time=no
seen_retry=no
seen_config=no
method=GET
url=
data_source=
while [ "$#" -gt 0 ]
do
    case "$1" in
        --silent) seen_silent=yes; shift ;;
        --show-error) seen_show_error=yes; shift ;;
        --fail) seen_fail=yes; shift ;;
        --noproxy)
            [ "${2:-}" = "*" ] || exit 93
            seen_noproxy=yes
            shift 2
            ;;
        --proto)
            [ "${2:-}" = "=http" ] || exit 93
            seen_proto=yes
            shift 2
            ;;
        --no-location) seen_no_location=yes; shift ;;
        --connect-timeout)
            [ "${2:-}" = "5" ] || exit 93
            seen_connect_timeout=yes
            shift 2
            ;;
        --max-time)
            [ "${2:-}" = "20" ] || exit 93
            seen_max_time=yes
            shift 2
            ;;
        --retry)
            [ "${2:-}" = "0" ] || exit 93
            seen_retry=yes
            shift 2
            ;;
        --config)
            [ "${2:-}" = "-" ] || exit 93
            seen_config=yes
            shift 2
            ;;
        --request)
            method=${2:-}
            shift 2
            ;;
        --header)
            [ "${2:-}" = "Content-Type: application/json" ] || exit 93
            shift 2
            ;;
        --data-binary)
            data_source=${2:-}
            shift 2
            ;;
        http://supervisor/addons/self/info|http://supervisor/addons/self/options)
            url=$1
            shift
            ;;
        *) exit 94 ;;
    esac
done
for required in \
    "$seen_silent" "$seen_show_error" "$seen_fail" "$seen_noproxy" \
    "$seen_proto" "$seen_no_location" "$seen_connect_timeout" \
    "$seen_max_time" "$seen_retry" "$seen_config"
do
    [ "$required" = yes ] || exit 95
done
[ -z "${SUPERVISOR_TOKEN:-}" ] || exit 96
header_config=$(cat) || exit 97
[ "$header_config" =     'header = "Authorization: Bearer test.only-token_123"' ] || exit 98
state=${HACP_TEST_SUPERVISOR_STATE:?}
counter=${HACP_TEST_SUPERVISOR_COUNTER:?}
call_log=${HACP_TEST_SUPERVISOR_CALL_LOG:?}
printf '%s\n' "$method" >> "$call_log"
case "$method:$url" in
    GET:http://supervisor/addons/self/info)
        request_count=0
        if [ -f "$counter" ]; then
            IFS= read -r request_count < "$counter"
        fi
        request_count=$((request_count + 1))
        printf '%s\n' "$request_count" > "$counter"
        if [ "${HACP_TEST_SUPERVISOR_RACE:-NO}" = YES ] &&
            [ "$request_count" -eq 2 ]; then
            jq -c                 '.packages += ["concurrent-package"] |
                 .init_commands += ["echo concurrent"]'                 "$state" > "$state.tmp" || exit 99
            mv "$state.tmp" "$state" || exit 99
        fi
        jq -c '{result:"ok",data:{options:.}}' "$state"
        ;;
    POST:http://supervisor/addons/self/options)
        [ "$data_source" = "@/proc/self/fd/3" ] || exit 100
        post_body=$(cat <&3) || exit 100
        printf '%s' "$post_body" > "${HACP_TEST_SUPERVISOR_POST_LOG:?}"
        if [ "${HACP_TEST_SUPERVISOR_POST_MODE:-PERSIST}" = PERSIST ]; then
            printf '%s' "$post_body" |
                jq -e -c '.options | select(type == "object")'                     > "$state.tmp" || exit 101
            mv "$state.tmp" "$state" || exit 101
        fi
        printf '%s\n' '{"result":"ok"}'
        ;;
    *) exit 102 ;;
esac
"""


class PersistenceHarness:
    """Runs the shell lifecycle without touching real container paths or tools."""

    def __init__(self, base: Path) -> None:
        self.base = base
        self.container = base / "disposable-container"
        self.codex = self.container / "root" / ".codex"
        self.gh = self.container / "root" / ".config" / "gh"
        self.gitconfig = self.container / "root" / ".gitconfig"
        self.persistent_gitconfig = (
            self.base / "persistent-addon-data" / "git" / ".gitconfig"
        )
        self.command_bin = self.container / "fake-command-bin"
        self.bin_link_root = self.container / "usr" / "local" / "bin"
        self.runtime = base / "persistent-addon-data" / "codex-persistence"
        self.workspace = base / "persistent-workspace" / "Codex"
        self.workspace.parent.mkdir(parents=True)
        self.installed_script = (
            self.runtime / "bootstrap" / "ha-codex-persistence.sh"
        )
        self.runtime.parent.mkdir(parents=True)
        self.recreate_container(with_fake_commands=True)

    def recreate_container(self, *, with_fake_commands: bool = False) -> None:
        """Creates only the directories a fresh add-on image would provide."""

        self.bin_link_root.mkdir(parents=True, exist_ok=True)
        self.persistent_gitconfig.parent.mkdir(parents=True, exist_ok=True)
        if not self.persistent_gitconfig.exists():
            self.persistent_gitconfig.write_text(
                "[user]\n"
                "  name = Preserve Me\n"
                "[credential \"https://github.com\"]\n"
                "  helper =\n"
                "  helper = !/usr/bin/gh auth git-credential\n"
                "[credential \"https://gist.github.com\"]\n"
                "  helper =\n"
                "  helper = !/usr/bin/gh auth git-credential\n",
                encoding="utf-8",
            )
        self.gitconfig.parent.mkdir(parents=True, exist_ok=True)
        self.gitconfig.symlink_to(self.persistent_gitconfig)
        if with_fake_commands:
            self.command_bin.mkdir(parents=True, exist_ok=True)
            self._write_executable(self.command_bin / "codex", FAKE_CODEX)
            self._write_executable(self.command_bin / "gh", FAKE_GH)
            self._write_executable(self.command_bin / "sleep", FAKE_SLEEP)

    @staticmethod
    def _write_executable(destination: Path, content: str) -> None:
        destination.write_text(content, encoding="utf-8")
        destination.chmod(0o755)

    def configure_fake_supervisor(self) -> dict[str, Path]:
        state = self.base / "supervisor-options.json"
        counter = self.base / "supervisor-get-count"
        call_log = self.base / "supervisor-call.log"
        post_log = self.base / "supervisor-post.json"
        state.write_text(
            json.dumps(
                {
                    "packages": ["gh", "ripgrep"],
                    "init_commands": ["echo preserve"],
                    "nested": {
                        "private": "supervisor-secret-sentinel",
                        "unchanged": True,
                    },
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        self._write_executable(self.command_bin / "curl", FAKE_CURL)
        real_jq = shutil.which("jq")
        if real_jq is None:
            raise RuntimeError("jq is required for Supervisor tests")
        self._write_executable(
            self.command_bin / "jq",
            f"""#!/bin/sh
case " $* " in
  *supervisor-secret-sentinel*|*test.only-token_123*) exit 98 ;;
esac
exec {real_jq} "$@"
""",
        )
        return {
            "state": state,
            "counter": counter,
            "call_log": call_log,
            "post_log": post_log,
        }

    @property
    def desired_git_helper(self) -> str:
        return (
            f"!GH_CONFIG_DIR={self.gh} "
            f"{self.bin_link_root}/gh auth git-credential"
        )

    def git_config_values(self, key: str) -> list[str]:
        result = subprocess.run(
            [
                "git",
                "config",
                "--file",
                str(self.persistent_gitconfig),
                "--get-all",
                key,
            ],
            text=True,
            capture_output=True,
            check=True,
        )
        return result.stdout.splitlines()

    def seed_logged_in_state(self, *, native_socket: bool = False) -> None:
        session = self.codex / "sessions" / "2026" / "07" / "chat.jsonl"
        session.parent.mkdir(parents=True)
        session.write_text(
            '{"type":"user","text":"persistent test session"}\n',
            encoding="utf-8",
        )
        (self.codex / "auth.json").write_text(
            '{"auth_mode":"test-placeholder"}\n',
            encoding="utf-8",
        )
        (self.codex / "config.toml").write_text(
            'model = "test-model"\n',
            encoding="utf-8",
        )
        native_memory = self.codex / "memories" / "global.md"
        native_memory.parent.mkdir(parents=True)
        native_memory.write_text(
            "generated native memory placeholder\n",
            encoding="utf-8",
        )

        extension_binary = self.base / "persistent-addon-data" / "extension" / "codex"
        extension_binary.parent.mkdir(parents=True, exist_ok=True)
        extension_binary.write_text("test extension binary\n", encoding="utf-8")
        temporary = self.codex / "tmp" / "arg0"
        temporary.mkdir(parents=True)
        (temporary / "codex").symlink_to(extension_binary)

        self.gh.mkdir(parents=True)
        (self.gh / "hosts.yml").write_text(
            "github.com:\n"
            "  user: test-user\n"
            "  oauth_token: <test-only-placeholder>\n"
            "  git_protocol: https\n",
            encoding="utf-8",
        )

        if native_socket:
            ipc = self.codex / "ipc"
            ipc.mkdir(parents=True)
            ipc_socket = socket.socket(socket.AF_UNIX)
            try:
                ipc_socket.bind(str(ipc / "ipc.sock"))
            finally:
                ipc_socket.close()

    def env(self, **extra: str) -> dict[str, str]:
        environment = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith("HACP_") and key != "SUPERVISOR_TOKEN"
        }
        environment.update(
            {
                "HACP_RUNTIME_ROOT": str(self.runtime),
                "HACP_CODEX_SOURCE": str(self.codex),
                "HACP_GH_SOURCE": str(self.gh),
                "HACP_GIT_CONFIG_SOURCE": str(self.gitconfig),
                "HACP_BIN_LINK_ROOT": str(self.bin_link_root),
                "HACP_WORKSPACE_ROOT": str(self.workspace),
                "HACP_TEST_MODE": "YES",
                "HACP_SKIP_PROCESS_CHECK": "YES",
                "HACP_SKIP_ADDON_CONFIG": "YES",
                "HACP_MAX_COPY_ATTEMPTS": "1",
                "GH_TOKEN": "<test-only-placeholder>",
                "GITHUB_TOKEN": "<test-only-placeholder>",
                "GH_ENTERPRISE_TOKEN": "<test-only-placeholder>",
                "GITHUB_ENTERPRISE_TOKEN": "<test-only-placeholder>",
                "PATH": os.pathsep.join(
                    (str(self.command_bin), environment.get("PATH", ""))
                ),
            }
        )
        environment.update(extra)
        return environment

    def run(
        self,
        command: str,
        *,
        use_installed_script: bool = False,
        cwd: Path | None = None,
        **extra: str,
    ) -> subprocess.CompletedProcess[str]:
        script = self.installed_script if use_installed_script else SCRIPT
        return subprocess.run(
            ["sh", str(script), command],
            text=True,
            capture_output=True,
            env=self.env(**extra),
            cwd=cwd or self.base,
            check=False,
        )

    def install(
        self,
        *,
        cwd: Path | None = None,
        **extra: str,
    ) -> subprocess.CompletedProcess[str]:
        return self.run("install", cwd=cwd, HACP_INSTALL_OK="YES", **extra)

    def boot(self) -> subprocess.CompletedProcess[str]:
        return self.run(
            "boot",
            use_installed_script=True,
            HACP_BOOT_OK="YES",
        )

    def audit(self, *, check_auth: bool = True) -> subprocess.CompletedProcess[str]:
        extra = {"HACP_CHECK_AUTH": "YES"} if check_auth else {}
        return self.run("audit", use_installed_script=True, **extra)

    def delete_container(self) -> None:
        if self.container.exists():
            shutil.rmtree(self.container)

    def replace_container(self) -> None:
        self.delete_container()
        self.recreate_container()


class CodexPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.harness = PersistenceHarness(Path(self.temporary.name))

    def test_install_container_deletion_boot_and_audit(self) -> None:
        """TC-001: Native state and both logins survive container replacement."""

        self.harness.seed_logged_in_state(native_socket=True)

        installed = self.harness.install()

        self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)
        self.assertIn("\tinstall\t", installed.stdout)
        self.assertTrue(self.harness.installed_script.is_file())
        owner_marker = self.harness.runtime / ".hacp-runtime-owner"
        self.assertEqual(
            owner_marker.read_bytes(),
            b"home-assistant-codex-persistence-v1\n",
        )
        self.assertEqual(owner_marker.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.harness.runtime.stat().st_mode & 0o777, 0o700)
        self.assertTrue((self.harness.workspace / "Memories" / "AGENTS.md").is_file())
        self.assertTrue((self.harness.workspace / "Memories" / "MEMORY.md").is_file())
        global_agents = (
            self.harness.runtime / "current" / "codex-home" / "AGENTS.md"
        )
        global_text = global_agents.read_text(encoding="utf-8")
        self.assertIn(
            str(self.harness.workspace / "Memories" / "AGENTS.md"),
            global_text,
        )
        self.assertIn(
            str(self.harness.workspace / "Memories" / "MEMORY.md"),
            global_text,
        )
        self.assertFalse((self.harness.workspace / "AGENTS.md").exists())
        self.assertTrue(self.harness.codex.is_symlink())
        self.assertTrue(self.harness.gh.is_symlink())
        self.assertTrue(self.harness.gitconfig.is_symlink())
        for host in ("github.com", "gist.github.com"):
            self.assertEqual(
                self.harness.git_config_values(
                    f"credential.https://{host}.helper"
                ),
                ["", self.harness.desired_git_helper],
            )
        self.assertEqual(
            self.harness.git_config_values("user.name"),
            ["Preserve Me"],
        )

        self.harness.replace_container()
        booted = self.harness.boot()

        self.assertEqual(booted.returncode, 0, booted.stdout + booted.stderr)
        self.assertTrue(self.harness.codex.is_symlink())
        self.assertTrue(self.harness.gh.is_symlink())
        self.assertEqual(
            self.harness.codex.resolve(),
            self.harness.runtime / "current" / "codex-home",
        )
        self.assertEqual(
            self.harness.gh.resolve(),
            self.harness.runtime / "current" / "gh",
        )
        persistent_session = (
            self.harness.codex
            / "sessions"
            / "2026"
            / "07"
            / "chat.jsonl"
        )
        self.assertEqual(
            persistent_session.read_bytes(),
            b'{"type":"user","text":"persistent test session"}\n',
        )
        self.assertEqual(
            (self.harness.codex / "memories" / "global.md").read_bytes(),
            b"generated native memory placeholder\n",
        )
        self.assertEqual(
            (self.harness.codex / "config.toml").read_bytes(),
            b'model = "test-model"\n\n'
            b'cli_auth_credentials_store = "file"\n',
        )
        self.assertEqual(
            (self.harness.codex / "auth.json").read_bytes(),
            b'{"auth_mode":"test-placeholder"}\n',
        )
        self.assertFalse((self.harness.codex / "ipc" / "ipc.sock").exists())
        self.assertFalse((self.harness.codex / "tmp" / "arg0" / "codex").exists())
        self.assertEqual(
            os.readlink(self.harness.bin_link_root / "codex"),
            str(self.harness.runtime / "current" / "tools" / "bin" / "codex"),
        )
        self.assertEqual(
            os.readlink(self.harness.bin_link_root / "gh"),
            str(self.harness.runtime / "current" / "tools" / "bin" / "gh"),
        )
        self.assertTrue(self.harness.gitconfig.is_symlink())
        for host in ("github.com", "gist.github.com"):
            self.assertEqual(
                self.harness.git_config_values(
                    f"credential.https://{host}.helper"
                ),
                ["", self.harness.desired_git_helper],
            )

        credential_log = (
            self.harness.persistent_gitconfig.parent
            / "credential-invocation.log"
        )
        system_helper_log = (
            self.harness.persistent_gitconfig.parent
            / "system-helper-must-not-run.log"
        )
        system_helper = self.harness.base / "foreign-system-helper"
        self.harness._write_executable(
            system_helper,
            f"#!/bin/sh\n: > \"{system_helper_log}\"\n",
        )
        system_config = self.harness.base / "system.gitconfig"
        system_config.write_text(
            f"[credential]\n  helper = !{system_helper}\n",
            encoding="utf-8",
        )
        credential_env = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith("GIT_CONFIG")
        }
        credential_env.update(
            {
                "GIT_CONFIG_GLOBAL": str(self.harness.persistent_gitconfig),
                "GIT_CONFIG_SYSTEM": str(system_config),
                "HACP_TEST_GIT_CREDENTIAL_LOG": str(credential_log),
            }
        )
        credential_result = subprocess.run(
            ["git", "credential", "reject"],
            input="protocol=https\nhost=github.com\n\n",
            text=True,
            capture_output=True,
            env=credential_env,
            cwd=self.harness.base,
            check=False,
        )
        self.assertEqual(
            credential_result.returncode,
            0,
            credential_result.stdout + credential_result.stderr,
        )
        self.assertEqual(
            credential_log.read_text(encoding="utf-8").strip(),
            f"{self.harness.bin_link_root}/gh|{self.harness.gh}|"
            "auth git-credential erase",
        )
        self.assertFalse(system_helper_log.exists())

        audited = self.harness.audit()

        self.assertEqual(audited.returncode, 0, audited.stdout + audited.stderr)
        self.assertIn(
            "\tcodex-auth\tcodex\tfile-based login cache recognized",
            audited.stdout,
        )
        self.assertIn(
            "\tgithub-auth\tgithub.com\t"
            "active login valid and sourced from hosts.yml",
            audited.stdout,
        )
        self.assertIn("\tgit-helper\t", audited.stdout)
        self.assertIn("\tresult\tactive\t", audited.stdout)

    def test_runtime_inside_installer_checkout_blocks_without_creation(self) -> None:
        self.harness.seed_logged_in_state()
        forbidden = ROOT / ".hacp-test-runtime-never-created"

        def cleanup_forbidden() -> None:
            if forbidden.exists():
                shutil.rmtree(forbidden)

        self.addCleanup(cleanup_forbidden)
        cleanup_forbidden()

        result = self.harness.install(HACP_RUNTIME_ROOT=str(forbidden))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside the installer checkout", result.stdout)
        self.assertFalse(forbidden.exists())

    def test_runtime_with_intermediate_symlink_blocks_before_creation(self) -> None:
        self.harness.seed_logged_in_state()
        escaped_parent = self.harness.base / "escaped-runtime-parent"
        escaped_nested = escaped_parent / "nested"
        escaped_nested.mkdir(parents=True)
        linked_parent = self.harness.base / "linked-runtime-parent"
        linked_parent.symlink_to(escaped_parent, target_is_directory=True)
        escaped_runtime = linked_parent / "nested" / "runtime"

        result = self.harness.install(HACP_RUNTIME_ROOT=str(escaped_runtime))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("canonical path differs", result.stdout)
        self.assertFalse((escaped_nested / "runtime").exists())

    def test_nonempty_unclaimed_runtime_is_never_mutated(self) -> None:
        self.harness.seed_logged_in_state()
        foreign_runtime = self.harness.base / "foreign-runtime"
        foreign_runtime.mkdir(mode=0o755)
        sentinel = foreign_runtime / "foreign-sentinel"
        sentinel.write_bytes(b"foreign bytes remain\n")
        mode_before = foreign_runtime.stat().st_mode & 0o777
        config_before = (self.harness.codex / "config.toml").read_bytes()

        result = self.harness.install(HACP_RUNTIME_ROOT=str(foreign_runtime))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("non-empty unclaimed runtime", result.stdout)
        self.assertEqual(sentinel.read_bytes(), b"foreign bytes remain\n")
        self.assertEqual(foreign_runtime.stat().st_mode & 0o777, mode_before)
        self.assertEqual(
            (self.harness.codex / "config.toml").read_bytes(),
            config_before,
        )
        self.assertFalse((foreign_runtime / ".hacp-runtime-owner").exists())
        self.assertFalse((foreign_runtime / "state").exists())

    def test_invalid_runtime_owner_marker_is_never_replaced(self) -> None:
        self.harness.seed_logged_in_state()
        foreign_runtime = self.harness.base / "invalid-owned-runtime"
        foreign_runtime.mkdir(mode=0o755)
        marker = foreign_runtime / ".hacp-runtime-owner"
        marker.write_bytes(b"foreign-owner\n")
        sentinel = foreign_runtime / "foreign-sentinel"
        sentinel.write_bytes(b"preserve me\n")
        marker_before = marker.read_bytes()
        mode_before = foreign_runtime.stat().st_mode & 0o777

        result = self.harness.install(HACP_RUNTIME_ROOT=str(foreign_runtime))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("non-empty unclaimed runtime", result.stdout)
        self.assertEqual(marker.read_bytes(), marker_before)
        self.assertEqual(sentinel.read_bytes(), b"preserve me\n")
        self.assertEqual(foreign_runtime.stat().st_mode & 0o777, mode_before)
        self.assertFalse((foreign_runtime / "state").exists())

    def test_boot_without_installation_blocks(self) -> None:
        result = self.harness.run("boot", HACP_BOOT_OK="YES")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("BLOCK\t", result.stdout)
        self.assertFalse((self.harness.runtime / "current").exists())
        self.assertFalse(self.harness.codex.is_symlink())
        self.assertFalse(self.harness.gh.is_symlink())

    def test_repeated_boot_is_idempotent(self) -> None:
        self.harness.seed_logged_in_state()
        installed = self.harness.install()
        self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)
        self.harness.replace_container()

        first_boot = self.harness.boot()
        session_before = (
            self.harness.runtime
            / "current"
            / "codex-home"
            / "sessions"
            / "2026"
            / "07"
            / "chat.jsonl"
        ).read_bytes()
        second_boot = self.harness.boot()

        self.assertEqual(
            first_boot.returncode,
            0,
            first_boot.stdout + first_boot.stderr,
        )
        self.assertEqual(
            second_boot.returncode,
            0,
            second_boot.stdout + second_boot.stderr,
        )
        self.assertIn("already persistent", second_boot.stdout)
        self.assertEqual(
            (
                self.harness.runtime
                / "current"
                / "codex-home"
                / "sessions"
                / "2026"
                / "07"
                / "chat.jsonl"
            ).read_bytes(),
            session_before,
        )

        self.harness.replace_container()
        third_boot = self.harness.boot()

        self.assertEqual(third_boot.returncode, 0, third_boot.stdout + third_boot.stderr)
        self.assertTrue(self.harness.codex.is_symlink())
        self.assertTrue(self.harness.gh.is_symlink())


    def test_boot_replaces_only_expected_disposable_container_state(self) -> None:
        """TC-003: Fresh Codex IPC/tmp and an empty gh directory are disposable."""

        self.harness.seed_logged_in_state()
        installed = self.harness.install()
        self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)
        self.harness.replace_container()

        (self.harness.codex / "ipc").mkdir(parents=True)
        (self.harness.codex / "tmp" / "argo").mkdir(parents=True)
        self.harness.gh.mkdir(parents=True)

        result = self.harness.boot()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("removed expected disposable container state", result.stdout)
        self.assertTrue(self.harness.codex.is_symlink())
        self.assertTrue(self.harness.gh.is_symlink())

    def test_conflicting_source_blocks_boot_without_overwrite(self) -> None:
        self.harness.seed_logged_in_state()
        installed = self.harness.install()
        self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)
        self.harness.replace_container()
        conflict = self.harness.codex / "sessions" / "new-container.jsonl"
        conflict.parent.mkdir(parents=True)
        conflict.write_text('{"conflict":true}\n', encoding="utf-8")

        result = self.harness.boot()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unexpected non-disposable state", result.stdout)
        self.assertTrue(conflict.is_file())
        self.assertFalse(self.harness.codex.is_symlink())
        self.assertFalse(self.harness.gh.is_symlink())

    def test_tampered_persistent_binary_blocks_boot(self) -> None:
        self.harness.seed_logged_in_state()
        installed = self.harness.install()
        self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)
        persistent_codex = (
            self.harness.runtime / "current" / "tools" / "bin" / "codex"
        )
        persistent_codex.write_text(
            persistent_codex.read_text(encoding="utf-8") + "\n# tampered\n",
            encoding="utf-8",
        )
        self.harness.replace_container()

        result = self.harness.boot()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("persistent runtime verification failed", result.stdout)
        self.assertFalse(self.harness.codex.is_symlink())
        self.assertFalse(self.harness.gh.is_symlink())
        self.assertFalse((self.harness.bin_link_root / "codex").exists())

    def test_unexpected_fifo_blocks_install(self) -> None:
        self.harness.seed_logged_in_state()
        os.mkfifo(self.harness.codex / "unexpected.fifo")

        result = self.harness.install()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsupported socket/device/FIFO", result.stdout)
        self.assertFalse((self.harness.runtime / "current").exists())
        self.assertFalse(
            (self.harness.runtime / "state" / "active-generation").exists()
        )
        self.assertTrue((self.harness.codex / "unexpected.fifo").is_fifo())
        self.assertFalse(self.harness.codex.is_symlink())

    def test_missing_codex_login_file_blocks_install(self) -> None:
        self.harness.seed_logged_in_state()
        (self.harness.codex / "auth.json").unlink()

        result = self.harness.install()

        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.harness.runtime / "current").exists())
        self.assertFalse(self.harness.codex.is_symlink())

    def test_missing_codex_config_is_created_atomically(self) -> None:
        self.harness.seed_logged_in_state()
        (self.harness.codex / "config.toml").unlink()

        result = self.harness.install()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        persistent_config = (
            self.harness.runtime / "current" / "codex-home" / "config.toml"
        )
        self.assertEqual(
            persistent_config.read_bytes(),
            b"cli_auth_credentials_store = \"file\"\n",
        )
        self.assertEqual(persistent_config.stat().st_mode & 0o777, 0o600)

    def test_concurrent_codex_config_creation_is_never_overwritten(self) -> None:
        self.harness.seed_logged_in_state()
        config_path = self.harness.codex / "config.toml"
        config_path.unlink()
        concurrent_content = b"model = concurrent-user-setting\n"
        real_ln = shutil.which("ln")
        self.assertIsNotNone(real_ln)
        wrapper = self.harness.command_bin / "ln"
        self.harness._write_executable(
            wrapper,
            "#!/bin/sh\n"
            "if [ -n \"${HACP_TEST_RACE_DEST:-}\" ] && "
            "[ \"${2:-}\" = \"$HACP_TEST_RACE_DEST\" ] && "
            "[ ! -e \"$2\" ] && [ ! -L \"$2\" ]; then\n"
            "    printf \"%s\\n\" \"model = concurrent-user-setting\" > \"$2\"\n"
            "fi\n"
            f"exec {real_ln} \"$@\"\n",
        )

        result = self.harness.install(
            HACP_TEST_RACE_DEST=str(config_path),
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(config_path.read_bytes(), concurrent_content)
        self.assertIn("appeared concurrently and was not overwritten", result.stdout)
        self.assertFalse((self.harness.runtime / "current").exists())

    def test_missing_store_key_is_appended_without_replacing_prefix(self) -> None:
        self.harness.seed_logged_in_state()
        config = self.harness.codex / "config.toml"
        original = b'model = "preserve-this-model"\n'
        config.write_bytes(original)

        result = self.harness.install()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        persistent_config = (
            self.harness.runtime / "current" / "codex-home" / "config.toml"
        )
        self.assertEqual(
            persistent_config.read_bytes(),
            original + b'\ncli_auth_credentials_store = "file"\n',
        )

    def test_missing_store_key_after_table_blocks_unchanged(self) -> None:
        self.harness.seed_logged_in_state()
        config = self.harness.codex / "config.toml"
        original = b'[features]\nnative_memory = true\n'
        config.write_bytes(original)

        result = self.harness.install()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("add it manually before the first table", result.stdout)
        self.assertEqual(config.read_bytes(), original)
        self.assertFalse((self.harness.runtime / "current").exists())

    def test_existing_config_path_swap_at_append_lock_blocks(self) -> None:
        self.harness.seed_logged_in_state()
        config = self.harness.codex / "config.toml"
        concurrent = b'model = "concurrent-content"\n'
        real_flock = shutil.which("flock")
        real_mv = shutil.which("mv")
        self.assertIsNotNone(real_flock)
        self.assertIsNotNone(real_mv)
        wrapper = self.harness.command_bin / "flock"
        self.harness._write_executable(
            wrapper,
            f"""#!/bin/sh
if [ "${{1:-}}" = -n ] && [ "${{2:-}}" = 7 ] && \
    [ -n "$HACP_TEST_RACE_CONFIG_DEST" ]; then
    printf '%s\n' 'model = "concurrent-content"' > \
        "$HACP_TEST_RACE_CONFIG_DEST.replacement"
    {real_mv} "$HACP_TEST_RACE_CONFIG_DEST.replacement" \
        "$HACP_TEST_RACE_CONFIG_DEST"
fi
exec {real_flock} "$@"
""",
        )

        result = self.harness.install(
            HACP_TEST_RACE_CONFIG_DEST=str(config),
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("changed before safe append", result.stdout)
        self.assertEqual(config.read_bytes(), concurrent)
        self.assertNotIn(b"cli_auth_credentials_store", config.read_bytes())
        self.assertFalse((self.harness.runtime / "current").exists())

    def test_missing_github_credential_helpers_are_installed(self) -> None:
        self.harness.seed_logged_in_state()
        for host in ("github.com", "gist.github.com"):
            subprocess.run(
                [
                    "git",
                    "config",
                    "--file",
                    str(self.harness.persistent_gitconfig),
                    "--unset-all",
                    f"credential.https://{host}.helper",
                ],
                check=True,
            )

        result = self.harness.install()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for host in ("github.com", "gist.github.com"):
            self.assertEqual(
                self.harness.git_config_values(
                    f"credential.https://{host}.helper"
                ),
                ["", self.harness.desired_git_helper],
            )
        self.assertEqual(self.harness.git_config_values("user.name"), ["Preserve Me"])

    def test_foreign_github_credential_helper_blocks_without_change(self) -> None:
        self.harness.seed_logged_in_state()
        subprocess.run(
            [
                "git",
                "config",
                "--file",
                str(self.harness.persistent_gitconfig),
                "--replace-all",
                "credential.https://github.com.helper",
                "cache --timeout=300",
            ],
            check=True,
        )
        config_before = self.harness.persistent_gitconfig.read_bytes()

        result = self.harness.install()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("foreign credential helper", result.stdout)
        self.assertEqual(
            self.harness.persistent_gitconfig.read_bytes(),
            config_before,
        )
        self.assertFalse((self.harness.runtime / "current").exists())
        self.assertFalse(self.harness.codex.is_symlink())
        self.assertFalse(self.harness.gh.is_symlink())

    def test_helper_appearing_at_lock_is_preserved_and_blocks(self) -> None:
        self.harness.seed_logged_in_state()
        race_config = self.harness.base / "foreign-race.gitconfig"
        race_config.write_text(
            "[user]\n"
            "  name = Concurrent Preserve Me\n"
            "[credential \"https://github.com\"]\n"
            "  helper = cache --timeout=300\n"
            "[credential \"https://gist.github.com\"]\n"
            "  helper =\n"
            "  helper = !/usr/bin/gh auth git-credential\n",
            encoding="utf-8",
        )
        expected_bytes = race_config.read_bytes()
        real_ln = shutil.which("ln")
        real_cp = shutil.which("cp")
        self.assertIsNotNone(real_ln)
        self.assertIsNotNone(real_cp)
        wrapper = self.harness.command_bin / "ln"
        self.harness._write_executable(
            wrapper,
            "#!/bin/sh\n"
            "if [ -n \"${HACP_TEST_GIT_LOCK_DEST:-}\" ] && "
            "[ \"${2:-}\" = \"$HACP_TEST_GIT_LOCK_DEST\" ] && "
            "[ ! -e \"$2\" ] && [ ! -L \"$2\" ]; then\n"
            f"    {real_cp} \"$HACP_TEST_GIT_RACE_FILE\" "
            "\"$HACP_TEST_GIT_CONFIG\"\n"
            "fi\n"
            f"exec {real_ln} \"$@\"\n",
        )

        result = self.harness.install(
            HACP_TEST_GIT_LOCK_DEST=(
                f"{self.harness.persistent_gitconfig}.lock"
            ),
            HACP_TEST_GIT_RACE_FILE=str(race_config),
            HACP_TEST_GIT_CONFIG=str(self.harness.persistent_gitconfig),
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("foreign credential helper", result.stdout)
        self.assertEqual(
            self.harness.persistent_gitconfig.read_bytes(),
            expected_bytes,
        )
        self.assertEqual(
            self.harness.git_config_values(
                "credential.https://github.com.helper"
            ),
            ["cache --timeout=300"],
        )
        self.assertFalse(
            Path(f"{self.harness.persistent_gitconfig}.lock").exists()
        )
        self.assertEqual(
            list(
                self.harness.persistent_gitconfig.parent.glob(
                    ".hacp-git-*"
                )
            ),
            [],
        )
        self.assertFalse(
            (self.harness.runtime / "state" / "active-generation").exists()
        )

    def test_missing_github_login_file_blocks_install(self) -> None:
        self.harness.seed_logged_in_state()
        (self.harness.gh / "hosts.yml").unlink()

        result = self.harness.install()

        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.harness.runtime / "current").exists())
        self.assertFalse(self.harness.gh.is_symlink())

    def test_keyring_only_github_login_blocks_install(self) -> None:
        self.harness.seed_logged_in_state()
        (self.harness.gh / "hosts.yml").write_text(
            "github.com:\n"
            "  user: test-user\n"
            "  git_protocol: https\n",
            encoding="utf-8",
        )

        result = self.harness.install()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "keyring-only login is not persistent; use --insecure-storage",
            result.stdout,
        )
        self.assertFalse((self.harness.runtime / "current").exists())

    def test_active_github_login_from_keyring_blocks_install(self) -> None:
        self.harness.seed_logged_in_state()

        result = self.harness.install(
            HACP_TEST_GH_TOKEN_SOURCE="keyring",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "active login is invalid or not sourced from hosts.yml",
            result.stdout,
        )
        self.assertFalse((self.harness.runtime / "current").exists())

    def test_non_inline_or_empty_github_tokens_block_install(self) -> None:
        self.harness.seed_logged_in_state()
        invalid_values = ("", '\"\"', "''", "null", "~", "|", ">", "# comment only")
        token_key = "oauth_" + "token"

        for value in invalid_values:
            with self.subTest(value=value):
                (self.harness.gh / "hosts.yml").write_text(
                    "github.com:\n"
                    "  user: test-user\n"
                    f"  {token_key}: {value}\n"
                    "  git_protocol: https\n",
                    encoding="utf-8",
                )

                result = self.harness.install()

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("keyring-only login is not persistent", result.stdout)
                self.assertFalse((self.harness.runtime / "current").exists())

    def test_duplicate_top_level_github_blocks_are_rejected(self) -> None:
        self.harness.seed_logged_in_state()
        (self.harness.gh / "hosts.yml").write_text(
            "github.com:\n"
            "  oauth_token: <first-test-only-placeholder>\n"
            "github.com:\n"
            "  oauth_token: <second-test-only-placeholder>\n",
            encoding="utf-8",
        )

        result = self.harness.install()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("keyring-only login is not persistent", result.stdout)
        self.assertFalse((self.harness.runtime / "current").exists())

    def test_nested_multi_account_github_tokens_are_persistent(self) -> None:
        self.harness.seed_logged_in_state()
        (self.harness.gh / "hosts.yml").write_text(
            "github.com:\n"
            "  users:\n"
            "    first-test-user:\n"
            "      oauth_token: <first-test-only-placeholder>\n"
            "    second-test-user:\n"
            "      oauth_token: <second-test-only-placeholder>\n"
            "  user: first-test-user\n"
            "  git_protocol: https\n",
            encoding="utf-8",
        )

        result = self.harness.install()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(self.harness.gh.is_symlink())

    def test_authenticated_audit_blocks_if_login_files_disappear(self) -> None:
        self.harness.seed_logged_in_state()
        installed = self.harness.install()
        self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)
        self.harness.replace_container()
        booted = self.harness.boot()
        self.assertEqual(booted.returncode, 0, booted.stdout + booted.stderr)
        (self.harness.codex / "auth.json").unlink()
        (self.harness.gh / "hosts.yml").unlink()

        result = self.harness.audit()

        self.assertEqual(result.returncode, 4, result.stdout + result.stderr)
        self.assertIn(
            "\tcodex-auth\tcodex\tlogin cache unavailable",
            result.stdout,
        )
        self.assertIn(
            "\tgithub-auth\tgithub.com\t"
            "active login invalid or not sourced from hosts.yml",
            result.stdout,
        )

    def test_ready_generation_is_promoted_on_boot(self) -> None:
        self.harness.seed_logged_in_state()
        installed = self.harness.install()
        self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)
        active = self.harness.runtime / "state" / "active-generation"
        ready = self.harness.runtime / "state" / "ready-generation"
        active.replace(ready)
        self.harness.replace_container()

        result = self.harness.boot()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("promoted fully verified READY generation", result.stdout)
        self.assertTrue(active.is_file())
        self.assertFalse(ready.exists())
        self.assertTrue(self.harness.codex.is_symlink())

    def test_existing_memory_content_is_never_replaced(self) -> None:
        self.harness.seed_logged_in_state()
        memory = self.harness.workspace / "Memories"
        memory.mkdir(parents=True)
        custom_rules = b"# Custom private rules stay untouched\n"
        custom_facts = b"# Private memory sentinel stays untouched\n"
        (memory / "AGENTS.md").write_bytes(custom_rules)
        (memory / "MEMORY.md").write_bytes(custom_facts)

        result = self.harness.install()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((memory / "AGENTS.md").read_bytes(), custom_rules)
        self.assertEqual((memory / "MEMORY.md").read_bytes(), custom_facts)
        self.assertNotIn("Private memory sentinel", (ROOT / "examples" / "memory" / "MEMORY.md").read_text(encoding="utf-8"))

    def test_nonempty_global_override_receives_block_and_base_is_untouched(self) -> None:
        self.harness.seed_logged_in_state()
        base_content = b"# Existing global base rules\n"
        override_content = b"# Existing temporary override rules\n"
        (self.harness.codex / "AGENTS.md").write_bytes(base_content)
        (self.harness.codex / "AGENTS.override.md").write_bytes(override_content)

        result = self.harness.install()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        persistent_home = self.harness.runtime / "current" / "codex-home"
        self.assertEqual(
            (persistent_home / "AGENTS.md").read_bytes(),
            base_content,
        )
        installed_override = (persistent_home / "AGENTS.override.md").read_bytes()
        self.assertTrue(installed_override.startswith(override_content))
        self.assertEqual(installed_override.count(b"<!-- BEGIN HACP MEMORY -->"), 1)
        self.assertIn(
            str(self.harness.workspace / "Memories" / "MEMORY.md").encode(),
            installed_override,
        )

    def test_later_nonempty_override_without_block_makes_audit_fail(self) -> None:
        self.harness.seed_logged_in_state()
        installed = self.harness.install()
        self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)
        (self.harness.codex / "AGENTS.override.md").write_text(
            "# This override masks the managed global base file\n",
            encoding="utf-8",
        )

        result = self.harness.audit()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exact effective global startup block missing", result.stdout)

    def test_only_missing_manual_memory_file_is_created(self) -> None:
        self.harness.seed_logged_in_state()
        memory = self.harness.workspace / "Memories"
        memory.mkdir(parents=True)
        existing_memory = b"# Existing private facts remain byte exact\n"
        (memory / "MEMORY.md").write_bytes(existing_memory)

        result = self.harness.install()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((memory / "MEMORY.md").read_bytes(), existing_memory)
        self.assertTrue((memory / "AGENTS.md").is_file())

    def test_repeated_install_keeps_manual_files_and_one_global_block(self) -> None:
        self.harness.seed_logged_in_state()
        first = self.harness.install()
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        memory = self.harness.workspace / "Memories"
        global_agents = self.harness.runtime / "current" / "codex-home" / "AGENTS.md"
        rules_before = (memory / "AGENTS.md").read_bytes()
        facts_before = (memory / "MEMORY.md").read_bytes()
        global_before = global_agents.read_bytes()

        second = self.harness.install()

        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertEqual((memory / "AGENTS.md").read_bytes(), rules_before)
        self.assertEqual((memory / "MEMORY.md").read_bytes(), facts_before)
        self.assertEqual(global_agents.read_bytes(), global_before)
        self.assertEqual(global_before.count(b"<!-- BEGIN HACP MEMORY -->"), 1)

    def test_repeated_install_does_not_add_memory_when_initially_disabled(self) -> None:
        self.harness.seed_logged_in_state()
        first = self.harness.install(HACP_MEMORY_SETUP="NO")
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        memory = self.harness.workspace / "Memories"
        manifest = self.harness.runtime / "current" / "meta" / "codex.tree"
        active = self.harness.runtime / "state" / "active-generation"
        manifest_before = manifest.read_bytes()
        active_before = active.read_bytes()
        self.assertFalse(memory.exists())

        second = self.harness.install()

        self.assertNotEqual(second.returncode, 0)
        self.assertIn("regular manual memory files required", second.stdout)
        self.assertFalse(memory.exists())
        self.assertFalse(
            (self.harness.runtime / "current" / "codex-home" / "AGENTS.md").exists()
        )
        self.assertEqual(manifest.read_bytes(), manifest_before)
        self.assertEqual(active.read_bytes(), active_before)

    def test_repeated_install_never_repairs_active_generation_by_mutation(self) -> None:
        self.harness.seed_logged_in_state()
        first = self.harness.install()
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        missing_memory = self.harness.workspace / "Memories" / "MEMORY.md"
        missing_memory.unlink()

        second = self.harness.install()

        self.assertNotEqual(second.returncode, 0)
        self.assertIn("regular manual memory files required", second.stdout)
        self.assertFalse(missing_memory.exists())
        self.assertTrue((self.harness.runtime / "current").is_dir())

    def test_nested_git_working_directory_still_uses_global_codex_agents(self) -> None:
        self.harness.seed_logged_in_state()
        repository = self.harness.workspace / "Projekte" / "nested-project"
        nested_cwd = repository / "src" / "feature"
        nested_cwd.mkdir(parents=True)
        (repository / ".git").mkdir()

        result = self.harness.install(cwd=nested_cwd)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        global_agents = (
            self.harness.runtime / "current" / "codex-home" / "AGENTS.md"
        ).read_text(encoding="utf-8")
        self.assertIn(str(self.harness.workspace / "Memories" / "AGENTS.md"), global_agents)
        self.assertFalse((self.harness.workspace / "AGENTS.md").exists())

    def test_workspace_inside_installer_checkout_is_blocked(self) -> None:
        self.harness.seed_logged_in_state()
        forbidden_workspace = ROOT / "test-local-memory-workspace"

        result = self.harness.install(
            HACP_WORKSPACE_ROOT=str(forbidden_workspace),
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside the installer checkout", result.stdout)
        self.assertFalse(forbidden_workspace.exists())
        self.assertFalse((self.harness.runtime / "current").exists())

    def test_workspace_with_intermediate_symlink_is_blocked(self) -> None:
        self.harness.seed_logged_in_state()
        escaped_parent = self.harness.base / "escaped-workspace-parent"
        escaped_nested = escaped_parent / "nested"
        escaped_nested.mkdir(parents=True)
        linked_parent = self.harness.workspace.parent / "linked-parent"
        linked_parent.symlink_to(escaped_parent, target_is_directory=True)
        escaped_workspace = linked_parent / "nested" / "Codex"

        result = self.harness.install(
            HACP_WORKSPACE_ROOT=str(escaped_workspace),
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("canonical path differs", result.stdout)
        self.assertFalse((escaped_nested / "Codex").exists())
        self.assertFalse((self.harness.runtime / "current").exists())

    def test_hardlinked_effective_global_agents_blocks_without_change(self) -> None:
        self.harness.seed_logged_in_state()
        outside = self.harness.base / "outside-global-agents"
        original = b"# External instructions remain untouched\n"
        outside.write_bytes(original)
        effective = self.harness.codex / "AGENTS.override.md"
        os.link(outside, effective)

        result = self.harness.install()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("hard-linked global instructions", result.stdout)
        self.assertEqual(outside.read_bytes(), original)
        self.assertEqual(effective.read_bytes(), original)
        self.assertNotIn(b"BEGIN HACP MEMORY", outside.read_bytes())
        self.assertFalse((self.harness.runtime / "current").exists())

    def test_global_agents_hardlink_appearing_at_flock_blocks(self) -> None:
        self.harness.seed_logged_in_state()
        effective = self.harness.codex / "AGENTS.md"
        original = b"# Existing global instructions\n"
        effective.write_bytes(original)
        alias = self.harness.base / "concurrent-global-agents-alias"
        real_flock = shutil.which("flock")
        real_ln = shutil.which("ln")
        self.assertIsNotNone(real_flock)
        self.assertIsNotNone(real_ln)
        wrapper = self.harness.command_bin / "flock"
        self.harness._write_executable(
            wrapper,
            f"""#!/bin/sh
if [ "${{1:-}}" = -n ] && [ "${{2:-}}" = 8 ] && \
    [ -n "$HACP_TEST_AGENTS_ALIAS" ]; then
    {real_ln} "$HACP_TEST_AGENTS_SOURCE" "$HACP_TEST_AGENTS_ALIAS"
fi
exec {real_flock} "$@"
""",
        )

        result = self.harness.install(
            HACP_TEST_AGENTS_SOURCE=str(effective),
            HACP_TEST_AGENTS_ALIAS=str(alias),
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("changed while opening append-only handle", result.stdout)
        self.assertEqual(effective.read_bytes(), original)
        self.assertEqual(alias.read_bytes(), original)
        self.assertEqual(effective.stat().st_nlink, 2)
        self.assertNotIn(b"BEGIN HACP MEMORY", effective.read_bytes())
        self.assertFalse((self.harness.runtime / "current").exists())

    def test_concurrent_global_agents_change_is_never_replaced(self) -> None:
        self.harness.seed_logged_in_state()
        global_agents = self.harness.codex / "AGENTS.md"
        original = b"# Existing global instructions\n"
        concurrent = b"# Concurrent global instruction remains untouched\n"
        global_agents.write_bytes(original)
        real_flock = shutil.which("flock")
        self.assertIsNotNone(real_flock)
        wrapper = self.harness.command_bin / "flock"
        self.harness._write_executable(
            wrapper,
            "#!/bin/sh\n"
            "if [ \"${1:-}\" = -n ] && [ \"${2:-}\" = 8 ] && "
            "[ -n \"${HACP_TEST_RACE_AGENTS_DEST:-}\" ]; then\n"
            "    printf '%s\\n' "
            "'# Concurrent global instruction remains untouched' "
            ">> \"$HACP_TEST_RACE_AGENTS_DEST\"\n"
            "fi\n"
            f"exec {real_flock} \"$@\"\n",
        )

        result = self.harness.install(
            HACP_TEST_RACE_AGENTS_DEST=str(global_agents),
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("changed before append; nothing was replaced", result.stdout)
        self.assertEqual(global_agents.read_bytes(), original + concurrent)
        self.assertNotIn(b"<!-- BEGIN HACP MEMORY -->", global_agents.read_bytes())
        self.assertFalse((self.harness.runtime / "current").exists())

    def test_override_appearing_before_copy_blocks_stage(self) -> None:
        self.harness.seed_logged_in_state()
        override = self.harness.codex / "AGENTS.override.md"
        real_date = shutil.which("date")
        self.assertIsNotNone(real_date)
        wrapper = self.harness.command_bin / "date"
        self.harness._write_executable(
            wrapper,
            "#!/bin/sh\n"
            "if [ -n \"${HACP_TEST_RACE_OVERRIDE_DEST:-}\" ] && "
            "[ ! -e \"$HACP_TEST_RACE_OVERRIDE_DEST\" ]; then\n"
            "    printf '%s\\n' '# Concurrent override masks the base file' "
            "> \"$HACP_TEST_RACE_OVERRIDE_DEST\"\n"
            "fi\n"
            f"exec {real_date} \"$@\"\n",
        )

        result = self.harness.install(
            HACP_TEST_RACE_OVERRIDE_DEST=str(override),
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "exact effective global memory startup block missing",
            result.stdout,
        )
        self.assertEqual(
            override.read_bytes(),
            b"# Concurrent override masks the base file\n",
        )
        self.assertFalse((self.harness.runtime / "current").exists())

    def test_concurrent_manual_memory_creation_is_never_overwritten(self) -> None:
        self.harness.seed_logged_in_state()
        memory = self.harness.workspace / "Memories"
        memory.mkdir(parents=True)
        race_destination = memory / "MEMORY.md"
        race_content = b"# Concurrent private memory remains untouched\n"
        real_ln = shutil.which("ln")
        self.assertIsNotNone(real_ln)
        wrapper = self.harness.command_bin / "ln"
        self.harness._write_executable(
            wrapper,
            "#!/bin/sh\n"
            "if [ -n \"${HACP_TEST_RACE_DEST:-}\" ] && "
            "[ \"${2:-}\" = \"$HACP_TEST_RACE_DEST\" ] && "
            "[ ! -e \"$2\" ] && [ ! -L \"$2\" ]; then\n"
            f"    printf '%s\\n' '# Concurrent private memory remains untouched' > \"$2\"\n"
            "fi\n"
            f"exec {real_ln} \"$@\"\n",
        )

        result = self.harness.install(
            HACP_TEST_RACE_DEST=str(race_destination),
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(race_destination.read_bytes(), race_content)
        self.assertIn("appeared concurrently", result.stdout)

    def test_supervisor_update_is_hardened_and_preserves_foreign_options(self) -> None:
        self.harness.seed_logged_in_state()
        paths = self.harness.configure_fake_supervisor()

        result = self.harness.install(
            HACP_SKIP_ADDON_CONFIG="NO",
            **{"SUPERVISOR" + "_" + "TO" + "KEN": "test.only-token_123"},
            HACP_TEST_SUPERVISOR_STATE=str(paths["state"]),
            HACP_TEST_SUPERVISOR_COUNTER=str(paths["counter"]),
            HACP_TEST_SUPERVISOR_CALL_LOG=str(paths["call_log"]),
            HACP_TEST_SUPERVISOR_POST_LOG=str(paths["post_log"]),
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(
            paths["call_log"].read_text(encoding="utf-8").splitlines(),
            ["GET", "GET", "POST", "GET"],
        )
        options = json.loads(paths["state"].read_text(encoding="utf-8"))
        self.assertEqual(options["packages"], ["ripgrep"])
        current_root = self.harness.runtime / "current"
        codex_target = current_root / "codex-home"
        github_target = current_root / "gh"
        codex_tool = current_root / "tools" / "bin" / "codex"
        github_tool = current_root / "tools" / "bin" / "gh"
        codex_link = self.harness.bin_link_root / "codex"
        github_link = self.harness.bin_link_root / "gh"
        expected_command = (
            "HACP_MANAGED=home-assistant-codex-persistence "
            f"rm -rf {self.harness.codex} {self.harness.gh} && "
            f"mkdir -p {self.harness.gh.parent} && "
            f"ln -s {codex_target} {self.harness.codex} && "
            f"ln -s {github_target} {self.harness.gh} && "
            f"ln -sf {codex_tool} {codex_link} && "
            f"ln -sf {github_tool} {github_link}"
        )
        self.assertEqual(options["init_commands"][0], expected_command)
        self.assertEqual(options["init_commands"][1:], ["echo preserve"])
        self.assertEqual(
            options["nested"],
            {
                "private": "supervisor-secret-sentinel",
                "unchanged": True,
            },
        )
        posted = json.loads(paths["post_log"].read_text(encoding="utf-8"))
        self.assertEqual(posted["options"], options)
        combined_output = result.stdout + result.stderr
        self.assertNotIn("test.only-token_123", combined_output)
        self.assertNotIn("supervisor-secret-sentinel", combined_output)
        self.assertTrue(
            (self.harness.runtime / "state" / "active-generation").is_file()
        )

    def test_supervisor_pre_post_race_blocks_without_overwrite(self) -> None:
        self.harness.seed_logged_in_state()
        paths = self.harness.configure_fake_supervisor()

        result = self.harness.install(
            HACP_SKIP_ADDON_CONFIG="NO",
            **{"SUPERVISOR" + "_" + "TO" + "KEN": "test.only-token_123"},
            HACP_TEST_SUPERVISOR_STATE=str(paths["state"]),
            HACP_TEST_SUPERVISOR_COUNTER=str(paths["counter"]),
            HACP_TEST_SUPERVISOR_CALL_LOG=str(paths["call_log"]),
            HACP_TEST_SUPERVISOR_POST_LOG=str(paths["post_log"]),
            HACP_TEST_SUPERVISOR_RACE="YES",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("changed concurrently; no update was sent", result.stdout)
        self.assertEqual(
            paths["call_log"].read_text(encoding="utf-8").splitlines(),
            ["GET", "GET"],
        )
        self.assertFalse(paths["post_log"].exists())
        options = json.loads(paths["state"].read_text(encoding="utf-8"))
        self.assertIn("concurrent-package", options["packages"])
        self.assertIn("echo concurrent", options["init_commands"])
        self.assertFalse(
            (self.harness.runtime / "state" / "active-generation").exists()
        )
        self.assertFalse(self.harness.codex.is_symlink())
        self.assertFalse(self.harness.gh.is_symlink())

    def test_supervisor_post_readback_mismatch_blocks_active(self) -> None:
        self.harness.seed_logged_in_state()
        paths = self.harness.configure_fake_supervisor()

        result = self.harness.install(
            HACP_SKIP_ADDON_CONFIG="NO",
            **{"SUPERVISOR" + "_" + "TO" + "KEN": "test.only-token_123"},
            HACP_TEST_SUPERVISOR_STATE=str(paths["state"]),
            HACP_TEST_SUPERVISOR_COUNTER=str(paths["counter"]),
            HACP_TEST_SUPERVISOR_CALL_LOG=str(paths["call_log"]),
            HACP_TEST_SUPERVISOR_POST_LOG=str(paths["post_log"]),
            HACP_TEST_SUPERVISOR_POST_MODE="NO_PERSIST",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("differ after update; ACTIVE was not published", result.stdout)
        self.assertEqual(
            paths["call_log"].read_text(encoding="utf-8").splitlines(),
            ["GET", "GET", "POST", "GET"],
        )
        options = json.loads(paths["state"].read_text(encoding="utf-8"))
        self.assertIn("gh", options["packages"])
        self.assertFalse(
            (self.harness.runtime / "state" / "active-generation").exists()
        )
        self.assertFalse(self.harness.codex.is_symlink())
        self.assertFalse(self.harness.gh.is_symlink())

    def test_external_codex_stores_block_install(self) -> None:
        self.harness.seed_logged_in_state()
        config = self.harness.codex / "config.toml"
        config.write_text("sqlite_home = \"/tmp/codex-state\"\n", encoding="utf-8")

        sqlite_result = self.harness.install()

        self.assertNotEqual(sqlite_result.returncode, 0)
        self.assertIn("sqlite_home", sqlite_result.stdout)
        self.assertFalse((self.harness.runtime / "current").exists())

        for store in ("auto", "keyring"):
            with self.subTest(store=store):
                original = f'cli_auth_credentials_store = "{store}"\n'.encode()
                config.write_bytes(original)

                result = self.harness.install()

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("existing non-file store preserved", result.stdout)
                self.assertEqual(config.read_bytes(), original)
                self.assertFalse((self.harness.runtime / "current").exists())

    def test_prepare_is_not_a_user_facing_command(self) -> None:
        result = self.harness.run("prepare")

        self.assertEqual(result.returncode, 2)
        self.assertNotIn("prepare", result.stdout + result.stderr)
        self.assertFalse(self.harness.runtime.exists())


if __name__ == "__main__":
    unittest.main()
