#!/usr/bin/env python3
"""Opt-in remote startup and read-only status for an existing HACP installation.

HACP never builds, copies, pins or replaces Codex. Remote start delegates to the
official CLI; its native package/update behavior remains owned by OpenAI. Status
is read-only. HACP does not generate memory, change models or mutate threads.
"""
from __future__ import annotations

import argparse
import base64
import contextlib
import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import stat
import struct
import subprocess
import sys
import tempfile
import time
import urllib.request

OWNER = b"home-assistant-codex-persistence-v1\n"
REMOTE_MARKER = "HACP_REMOTE=home-assistant-codex-persistence"
MAX_MESSAGE = 1024 * 1024


class RemoteError(ValueError):
    pass


def private_path(path: Path, *, directory: bool = False) -> None:
    for parent in (path, *path.parents):
        if parent.is_symlink():
            raise RemoteError("symlinked control path rejected")
    st = path.stat()
    if st.st_uid != os.getuid() or st.st_mode & 0o022:
        raise RemoteError("unsafe control ownership or permissions")
    expected = stat.S_ISDIR if directory else stat.S_ISREG
    if not expected(st.st_mode) or (not directory and st.st_nlink != 1):
        raise RemoteError("invalid control file type")


def validate_runtime(root: Path) -> None:
    private_path(root, directory=True)
    marker = root / ".hacp-runtime-owner"
    private_path(marker)
    if marker.read_bytes() != OWNER:
        raise RemoteError("HACP ownership marker mismatch")
    for name in ("bootstrap", "state", "locks"):
        private_path(root / name, directory=True)
    home = (root / "current/codex-home").resolve(strict=True)
    if not home.is_relative_to(root) or not home.is_dir():
        raise RemoteError("persistent Codex home is outside runtime")


def read_json(path: Path) -> dict:
    private_path(path)
    if path.stat().st_size > 16384:
        raise RemoteError("oversized control file")
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise RemoteError("invalid control object")
    return value


def atomic_write(path: Path, value: bytes, mode: int = 0o600) -> None:
    if path.exists() or path.is_symlink():
        private_path(path)
    fd, name = tempfile.mkstemp(prefix=".remote-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            os.fchmod(stream.fileno(), mode)
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


@contextlib.contextmanager
def mutation_lock(root: Path):
    path = root / "locks/remote.lock"
    if path.exists() or path.is_symlink():
        private_path(path)
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    except BlockingIOError as exc:
        raise RemoteError("another remote operation is active") from exc
    finally:
        os.close(fd)


def native_socket_path(path: Path, *, allow_missing_alias: bool = False) -> Path:
    """Accept a private socket or the deterministic native Linux rendezvous alias."""
    private_path(path.parent, directory=True)
    entry = path.lstat()
    if stat.S_ISLNK(entry.st_mode):
        uid = os.getuid()
        if entry.st_uid != uid or stat.S_IMODE(path.parent.stat().st_mode) != 0o700:
            raise RemoteError("unsafe native socket alias")
        for ancestor in path.parent.parents:
            info = ancestor.lstat()
            if (not stat.S_ISDIR(info.st_mode) or info.st_uid not in {0, uid}
                    or (info.st_mode & 0o022
                        and not (info.st_uid == 0 and info.st_mode & stat.S_ISVTX))):
                raise RemoteError("unsafe native socket alias ancestor")
        root = Path("/").lstat()
        temporary = Path("/tmp").lstat()
        if (not stat.S_ISDIR(root.st_mode) or root.st_uid != 0 or root.st_mode & 0o022
                or not stat.S_ISDIR(temporary.st_mode) or temporary.st_uid != 0
                or not temporary.st_mode & stat.S_ISVTX):
            raise RemoteError("unsafe native temporary socket root")
        directory = Path("/tmp") / f"codex-daemon-{uid}"
        canonical_alias = path.parent.resolve(strict=True) / path.name
        expected = directory / hashlib.sha256(os.fsencode(canonical_alias)).hexdigest()
        if os.readlink(path) != str(expected):
            raise RemoteError("unexpected native socket alias target")
        try:
            directory_info = directory.lstat()
        except FileNotFoundError:
            if allow_missing_alias:
                return expected
            raise
        if (not stat.S_ISDIR(directory_info.st_mode) or directory_info.st_uid != uid
                or stat.S_IMODE(directory_info.st_mode) != 0o700):
            raise RemoteError("unsafe native socket directory")
        path = expected
        try:
            entry = path.lstat()
        except FileNotFoundError:
            if allow_missing_alias:
                return expected
            raise
    if (entry.st_uid != os.getuid() or not stat.S_ISSOCK(entry.st_mode)
            or entry.st_mode & 0o022):
        raise RemoteError("unsafe native control socket")
    return path


class RemoteSocket:
    """Bounded WebSocket JSON-RPC over the native private Unix socket."""
    def __init__(self, path: Path):
        path = native_socket_path(path)
        self.sock = socket.socket(socket.AF_UNIX)
        self.deadline = time.monotonic() + 8
        self.sock.settimeout(5)
        try:
            self.sock.connect(str(path))
            key = base64.b64encode(os.urandom(16)).decode()
            request = ("GET / HTTP/1.1\r\nHost: localhost\r\nUpgrade: websocket\r\n"
                       "Connection: Upgrade\r\nSec-WebSocket-Key: " + key +
                       "\r\nSec-WebSocket-Version: 13\r\n\r\n")
            self.sock.sendall(request.encode())
            header = b""
            while not header.endswith(b"\r\n\r\n"):
                if len(header) > 8192:
                    raise RemoteError("oversized WebSocket handshake")
                header += self.exact(1)
            accept = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest())
            fields = {line.split(b":", 1)[0].lower(): line.split(b":", 1)[1].strip()
                      for line in header.split(b"\r\n")[1:] if b":" in line}
            if not header.startswith(b"HTTP/1.1 101 ") or fields.get(b"sec-websocket-accept") != accept:
                raise RemoteError("invalid native WebSocket handshake")
        except BaseException:
            self.sock.close()
            raise

    def exact(self, count: int) -> bytes:
        result = b""
        while len(result) < count:
            remaining = self.deadline - time.monotonic()
            if remaining <= 0:
                raise RemoteError("native status deadline exceeded")
            self.sock.settimeout(min(5, remaining))
            block = self.sock.recv(count - len(result))
            if not block:
                raise RemoteError("native connection closed")
            result += block
        return result

    def send(self, payload: bytes, opcode: int = 1) -> None:
        size = len(payload)
        header = bytes((0x80 | opcode, 0x80 | size)) if size < 126 else bytes((0x80 | opcode, 254)) + struct.pack("!H", size)
        mask = os.urandom(4)
        self.sock.sendall(header + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(payload)))

    def result(self, request_id: int) -> dict:
        for _ in range(32):
            first, second = self.exact(2)
            if not first & 0x80 or second & 0x80:
                raise RemoteError("unsupported native WebSocket frame")
            size = second & 127
            if size == 126:
                size = struct.unpack("!H", self.exact(2))[0]
            elif size == 127:
                size = struct.unpack("!Q", self.exact(8))[0]
            if size > MAX_MESSAGE:
                raise RemoteError("oversized native response")
            payload = self.exact(size)
            opcode = first & 15
            if opcode == 9:
                self.send(payload, 10)
                continue
            if opcode != 1:
                raise RemoteError("unexpected native WebSocket opcode")
            response = json.loads(payload)
            if not isinstance(response, dict):
                raise RemoteError("invalid native response object")
            if response.get("id") == request_id:
                if "error" in response or not isinstance(response.get("result"), dict):
                    raise RemoteError("native status request rejected")
                return response["result"]
        raise RemoteError("native response limit exceeded")

    def status(self) -> dict:
        self.send(json.dumps({"id": 1, "method": "initialize", "params": {
            "clientInfo": {"name": "hacp-status", "version": "0.9.0-beta.5"},
            "capabilities": {"experimentalApi": True}}}).encode())
        self.result(1)
        self.send(b'{"method":"initialized"}')
        self.send(b'{"id":2,"method":"remoteControl/status/read"}')
        status = self.result(2).get("status")
        if not isinstance(status, str) or status not in {"disabled", "connecting", "connected", "errored"}:
            raise RemoteError("unknown native remote status")
        return {"daemon": "running", "connection": status}


def kernel_socket_paths() -> set[str]:
    """Unknown kernel evidence must never authorize stale endpoint recovery."""
    lines = Path("/proc/net/unix").read_text(errors="surrogateescape").splitlines()
    if not lines or lines[0].split() != ["Num", "RefCount", "Protocol", "Flags", "Type", "St", "Inode", "Path"]:
        raise RemoteError("unrecognized kernel socket table")
    paths = set()
    for line in lines[1:]:
        fields = line.split(maxsplit=7)
        if len(fields) not in {7, 8} or not fields[0].endswith(":"):
            raise RemoteError("unrecognized kernel socket entry")
        try:
            for field in (fields[0][:-1], *fields[1:6]):
                int(field, 16)
            int(fields[6], 10)
        except ValueError as exc:
            raise RemoteError("unrecognized kernel socket entry") from exc
        if len(fields) == 8:
            paths.add(fields[7])
    return paths


def remote_status(root: Path) -> dict:
    endpoint = root / "current/codex-home/app-server-control/app-server-control.sock"
    try:
        if not endpoint.exists() and not endpoint.is_symlink():
            # Absence is a first-start condition only below a safe control path.
            # Preserve conflicting paths instead of asking Codex to replace them.
            for parent in (endpoint.parent, *endpoint.parent.parents):
                if parent.is_symlink():
                    raise RemoteError("symlinked control path rejected")
            if endpoint.parent.exists():
                private_path(endpoint.parent, directory=True)
            return {"daemon": "stopped", "connection": "unavailable"}
        physical = native_socket_path(endpoint, allow_missing_alias=True)
        if physical != endpoint and not physical.exists():
            # Container replacement can remove /tmp while the validated native
            # rendezvous alias remains. Native Codex owns endpoint recovery.
            return {"daemon": "stale", "connection": "unavailable"}
        channel = RemoteSocket(endpoint)
        try:
            return channel.status()
        finally:
            channel.sock.close()
    except OSError as exc:
        if exc.errno == errno.ECONNREFUSED:
            # Revalidate before consulting kernel evidence; do not unlink
            # endpoints or terminate their processes ourselves.
            try:
                physical = native_socket_path(endpoint, allow_missing_alias=True)
                paths = kernel_socket_paths()
                if str(endpoint) not in paths and str(physical) not in paths:
                    return {"daemon": "stale", "connection": "unavailable"}
            except (OSError, RemoteError):
                pass
        return {"daemon": "unreachable", "connection": "unknown"}
    except (RemoteError, json.JSONDecodeError):
        # Do not delete stale sockets or infer that their owner is safe to stop.
        return {"daemon": "unreachable", "connection": "unknown"}


def native_cli(root: Path) -> Path:
    """Resolve the native package manager's current CLI; never copy or pin it."""
    home = (root / "current/codex-home").resolve(strict=True)
    packages = home / "packages/standalone"
    if not packages.resolve(strict=True).is_relative_to(home):
        raise RemoteError("native package directory escapes Codex home")
    cli = (packages / "current/bin/codex").resolve(strict=True)
    if not cli.is_relative_to(packages.resolve(strict=True)) or not cli.is_file():
        raise RemoteError("official managed CLI is outside its native package directory")
    st = cli.stat()
    if st.st_mode & 0o022 or st.st_nlink != 1 or not os.access(cli, os.X_OK):
        raise RemoteError("unsafe official managed CLI executable")
    return cli


def native_environment(root: Path) -> dict:
    """Use the native default alias only when it is the same persistent home."""
    home = (root / "current/codex-home").resolve(strict=True)
    environment = {**os.environ, "CODEX_HOME": str(home)}
    alias = Path.home() / ".codex"
    try:
        if alias.is_symlink() and alias.resolve(strict=True) == home:
            environment.pop("CODEX_HOME", None)
    except (OSError, RuntimeError):
        # Older Python versions report symlink loops as RuntimeError.
        pass
    return environment


def start(root: Path) -> dict:
    validate_runtime(root)
    config = read_json(root / "state/remote.json")
    if not isinstance(config.get("enabled"), bool):
        raise RemoteError("invalid remote opt-in state")
    if not config["enabled"]:
        return {"daemon": "disabled", "connection": "disabled"}
    with mutation_lock(root):
        if shutil.which("ps") is None:
            raise RemoteError("procps is missing; install it during explicit setup")
        cli = native_cli(root)
        auth = root / "current/codex-home/auth.json"
        private_path(auth)
        if auth.stat().st_size == 0:
            raise RemoteError("Codex login is missing; sign in explicitly")
        state = remote_status(root)
        if state["daemon"] == "running":
            return {**state, "start": "already-running"}
        if state["daemon"] not in {"stopped", "stale"}:
            raise RemoteError("existing native endpoint is unreachable; no replacement attempted")
        # Delegate lifecycle, package selection and updater behavior to OpenAI.
        # No replacement CLI, direct daemon implementation or model override.
        subprocess.run([str(cli), "remote-control", "start", "--json"],
                       env=native_environment(root), cwd=root.parent,
                       stdin=subprocess.DEVNULL, capture_output=True, timeout=45,
                       check=True, start_new_session=True)
        state = remote_status(root)
        return {**state, "start": "started" if state["connection"] == "connected" else "connection-pending"}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise RemoteError("Supervisor redirects are forbidden")


def supervisor(path: str, body: dict | None = None) -> dict:
    if path not in {"info", "options"}:
        raise RemoteError("unsupported Supervisor endpoint")
    bearer = os.environ.get("SUPERVISOR_TOKEN", "")
    if not bearer or any(c in bearer for c in "\r\n"):
        raise RemoteError("Supervisor authentication unavailable")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    req = urllib.request.Request("http://supervisor/addons/self/" + path,
        data=None if body is None else json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + bearer, "Content-Type": "application/json"})
    with opener.open(req, timeout=20) as response:
        data = json.load(response)
    if data.get("result") != "ok":
        raise RemoteError("Supervisor rejected request")
    return data.get("data", {})


def desired_options(baseline: dict, command: str, enabled: bool) -> dict:
    result = json.loads(json.dumps(baseline))
    packages = result.get("packages", [])
    commands = result.get("init_commands", [])
    if not isinstance(packages, list) or not all(isinstance(v, str) for v in packages):
        raise RemoteError("invalid package options")
    if not isinstance(commands, list) or not all(isinstance(v, str) for v in commands):
        raise RemoteError("invalid startup options")
    if not commands or not commands[0].startswith("HACP_MANAGED=home-assistant-codex-persistence "):
        raise RemoteError("HACP boot must be the first startup command")
    managed = [v for v in commands if v.startswith(REMOTE_MARKER + " ")]
    if any(v != command for v in managed):
        raise RemoteError("different managed remote command requires explicit reconciliation")
    result["init_commands"] = [v for v in commands if v != command]
    if enabled:
        result["init_commands"].insert(1, command)
        result["packages"] = packages + [v for v in ("procps", "python3") if v not in packages]
    return result


def configure(root: Path, enabled: bool, cli: Path | None) -> dict:
    validate_runtime(root)
    with mutation_lock(root):
        command = f"{REMOTE_MARKER} python3 {root}/bootstrap/hacp_remote.py boot --runtime-root {root}"
        if any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/_.-" for c in str(root)):
            raise RemoteError("runtime path is not safe for an init command")
        helper = root / "bootstrap/hacp_remote.py"
        state_path = root / "state/remote.json"
        for target in (helper, state_path):
            if target.exists() or target.is_symlink():
                private_path(target)
        previous_helper = helper.read_bytes() if helper.exists() else None
        previous_mode = stat.S_IMODE(helper.stat().st_mode) if helper.exists() else 0o700
        baseline = supervisor("info")["options"]
        desired = desired_options(baseline, command, enabled)
        config = {"enabled": False}
        if enabled:
            selected = native_cli(root)
            if cli is None or cli.resolve(strict=True) != selected:
                raise RemoteError("select the existing official managed Codex CLI")
            if shutil.which("ps") is None:
                raise RemoteError("install procps before configuring remote startup")
            probe = subprocess.run([str(selected), "--version"], capture_output=True, timeout=10, check=True)
            if not probe.stdout.startswith(b"codex-cli "):
                raise RemoteError("unsupported CLI")
            subprocess.run([str(selected), "remote-control", "start", "--help"],
                           capture_output=True, timeout=10, check=True)
            config = {"enabled": True, "cli": "native-managed-current",
                      "observed_version": probe.stdout.decode().strip()}
        helper_content = Path(__file__).read_bytes()
        if supervisor("info")["options"] != baseline:
            raise RemoteError("Supervisor options changed concurrently; no update sent")
        atomic_write(helper, helper_content, 0o700)
        try:
            if baseline != desired:
                supervisor("options", {"options": desired})
            if supervisor("info")["options"] != desired:
                raise RemoteError("Supervisor read-back mismatch; active remote state preserved")
            atomic_write(state_path, (json.dumps(config, sort_keys=True) + "\n").encode())
        except BaseException:
            # Do not overwrite concurrent Supervisor edits. Restore only our
            # unchanged helper; candidate executables are inert without config.
            if helper.read_bytes() == helper_content:
                if previous_helper is None:
                    helper.unlink()
                else:
                    atomic_write(helper, previous_helper, previous_mode)
            raise
        return {"configured": True, "enabled": enabled}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("configure", "boot", "start", "status"))
    parser.add_argument("--runtime-root", type=Path, required=True)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--enable", action="store_true")
    group.add_argument("--disable", action="store_true")
    parser.add_argument("--cli", type=Path)
    args = parser.parse_args()
    try:
        root = args.runtime_root.absolute()
        validate_runtime(root)
        if args.command == "configure":
            if not (args.enable or args.disable):
                raise RemoteError("explicit --enable or --disable required")
            result = configure(root, args.enable, args.cli)
        elif args.command == "status":
            result = remote_status(root)
        else:
            result = start(root)
        print(json.dumps(result, sort_keys=True))
        return 0 if args.command == "boot" or result.get("connection", "connected") in {"connected", "disabled"} else 1
    except (OSError, ValueError, subprocess.SubprocessError, KeyError) as exc:
        # Never emit command output, credentials, machine identity or native logs.
        reason = str(exc) if isinstance(exc, RemoteError) else type(exc).__name__
        print(json.dumps({"status": "warning" if args.command == "boot" else "error", "reason": reason}))
        return 0 if args.command == "boot" else 1


if __name__ == "__main__":
    raise SystemExit(main())
