"""TC-029/030: native compatibility with isolated state and non-root UID fixtures.

Covers REQ-I-006/007, REQ-F-007, REQ-O-006, REQ-Q-003,
DOM-R-014/015/017/019/020. No native
daemon, real authentication, shared temporary socket, or network is modified.
"""
from contextlib import contextmanager
import errno
import hashlib
import importlib.util
import os
from pathlib import Path
import socket
import stat
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

SPEC = importlib.util.spec_from_file_location(
    'native_compat_remote', Path(__file__).resolve().parents[1] / 'scripts/hacp_remote.py')
remote = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(remote)

KERNEL_HEADER = 'Num RefCount Protocol Flags Type St Inode Path\n'


def metadata(kind, mode, uid=1000):
    return SimpleNamespace(st_mode=kind | mode, st_uid=uid, st_nlink=1)


class NativeSocketCompatibility(unittest.TestCase):
    def setUp(self):
        self.root = Path('/owned')
        self.alias = self.root / 'current/codex-home/app-server-control/app-server-control.sock'
        self.directory = Path('/tmp/codex-daemon-1000')
        self.target = self.directory / hashlib.sha256(os.fsencode(self.alias)).hexdigest()
        self.nodes = {
            **{path: metadata(stat.S_IFDIR, 0o700) for path in self.alias.parent.parents},
            Path('/'): metadata(stat.S_IFDIR, 0o755, 0),
            self.alias.parent: metadata(stat.S_IFDIR, 0o700),
            self.alias: metadata(stat.S_IFLNK, 0o777),
            Path('/tmp'): metadata(stat.S_IFDIR, 0o1777, 0),
            self.directory: metadata(stat.S_IFDIR, 0o700),
            self.target: metadata(stat.S_IFSOCK, 0o600),
        }
        self.link_target = str(self.target)

    @contextmanager
    def filesystem(self):
        def lstat(path, *args, **kwargs):
            if path not in self.nodes:
                raise FileNotFoundError(errno.ENOENT, 'synthetic missing path', str(path))
            return self.nodes[path]

        def followed_stat(path, *args, **kwargs):
            result = lstat(path)
            if stat.S_ISLNK(result.st_mode) and path == self.alias:
                return lstat(Path(self.link_target))
            return result

        with patch.object(Path, 'lstat', lstat), patch.object(Path, 'stat', followed_stat), \
                patch.object(Path, 'resolve', lambda path, strict=False: path), \
                patch.object(remote.os, 'getuid', return_value=1000), \
                patch.object(remote.os, 'readlink', return_value=self.link_target):
            yield

    def validate(self, **kwargs):
        with self.filesystem():
            return remote.native_socket_path(self.alias, **kwargs)

    def state(self, kernel=KERNEL_HEADER, error=None):
        failure = error or ConnectionRefusedError(errno.ECONNREFUSED, 'synthetic refusal')
        with self.filesystem(), patch.object(remote, 'RemoteSocket', side_effect=failure), \
                patch.object(Path, 'read_text', return_value=kernel), \
                patch.object(Path, 'unlink') as unlink, \
                patch.object(remote.subprocess, 'run') as launch:
            result = remote.remote_status(self.root)
            unlink.assert_not_called()
            launch.assert_not_called()
            return result

    def test_exact_native_alias_and_legacy_socket_are_accepted(self):
        self.assertEqual(self.validate(), self.target)
        self.nodes[self.alias] = metadata(stat.S_IFSOCK, 0o600)
        self.assertEqual(self.validate(), self.alias)

    def test_connection_uses_physical_native_socket_and_closes_on_error(self):
        connection = Mock()
        connection.connect.side_effect = ConnectionRefusedError(errno.ECONNREFUSED, 'synthetic refusal')
        with self.filesystem(), patch.object(remote.socket, 'socket', return_value=connection):
            with self.assertRaises(ConnectionRefusedError):
                remote.RemoteSocket(self.alias)
        connection.connect.assert_called_once_with(str(self.target))
        connection.close.assert_called_once()

    def test_alias_owner_ancestors_and_target_permissions_fail_closed(self):
        cases = {
            'foreign alias owner': (self.alias, metadata(stat.S_IFLNK, 0o777, 2000)),
            'public alias parent': (self.alias.parent, metadata(stat.S_IFDIR, 0o755)),
            'writable alias parent': (self.alias.parent, metadata(stat.S_IFDIR, 0o770)),
            'foreign alias parent': (self.alias.parent, metadata(stat.S_IFDIR, 0o700, 2000)),
            'symlink ancestor': (self.root, metadata(stat.S_IFLNK, 0o777)),
            'foreign ancestor': (self.root, metadata(stat.S_IFDIR, 0o700, 2000)),
            'writable ancestor': (self.root, metadata(stat.S_IFDIR, 0o770)),
            'non-root sticky ancestor': (self.root, metadata(stat.S_IFDIR, 0o1777)),
            'writable root': (Path('/'), metadata(stat.S_IFDIR, 0o777, 0)),
            'foreign root': (Path('/'), metadata(stat.S_IFDIR, 0o755, 2000)),
            'symlink tmp': (Path('/tmp'), metadata(stat.S_IFLNK, 0o1777, 0)),
            'foreign tmp': (Path('/tmp'), metadata(stat.S_IFDIR, 0o1777, 2000)),
            'non-sticky tmp': (Path('/tmp'), metadata(stat.S_IFDIR, 0o777, 0)),
            'symlink target directory': (self.directory, metadata(stat.S_IFLNK, 0o700)),
            'foreign target directory': (self.directory, metadata(stat.S_IFDIR, 0o700, 2000)),
            'public target directory': (self.directory, metadata(stat.S_IFDIR, 0o755)),
            'writable target directory': (self.directory, metadata(stat.S_IFDIR, 0o770)),
            'target regular file': (self.target, metadata(stat.S_IFREG, 0o600)),
            'target symlink': (self.target, metadata(stat.S_IFLNK, 0o777)),
            'foreign target socket': (self.target, metadata(stat.S_IFSOCK, 0o600, 2000)),
            'group-writable socket': (self.target, metadata(stat.S_IFSOCK, 0o620)),
            'world-writable socket': (self.target, metadata(stat.S_IFSOCK, 0o602)),
        }
        for label, (path, replacement) in cases.items():
            with self.subTest(case=label):
                original = self.nodes[path]
                self.nodes[path] = replacement
                try:
                    with self.assertRaises(remote.RemoteError):
                        self.validate()
                    self.assertEqual(self.state(), {'daemon': 'unreachable', 'connection': 'unknown'})
                finally:
                    self.nodes[path] = original

    def test_root_owned_sticky_ancestor_supports_non_root_temp_roots(self):
        self.nodes[self.root] = metadata(stat.S_IFDIR, 0o1777, 0)
        self.assertEqual(self.validate(), self.target)

    def test_legacy_socket_foreign_owner_type_or_writable_mode_rejected(self):
        for entry in (metadata(stat.S_IFSOCK, 0o600, 2000),
                      metadata(stat.S_IFSOCK, 0o666), metadata(stat.S_IFREG, 0o600)):
            with self.subTest(entry=entry):
                self.nodes[self.alias] = entry
                with self.assertRaises(remote.RemoteError):
                    self.validate()

    def test_only_exact_absolute_hash_and_uid_target_is_accepted(self):
        for target in (str(self.directory / ('a' * 64)),
                       str(Path('/tmp/codex-daemon-2000') / self.target.name),
                       '/tmp/foreign.sock', str(self.target).lstrip('/'),
                       str(self.directory / '..' / self.directory.name / self.target.name)):
            with self.subTest(target=target):
                self.link_target = target
                with self.assertRaises(remote.RemoteError):
                    self.validate()
                self.assertEqual(self.state()['daemon'], 'unreachable')

    def test_container_replacement_missing_target_is_stale_without_connecting(self):
        del self.nodes[self.target]
        for missing_directory in (False, True):
            with self.subTest(directory_missing=missing_directory):
                if missing_directory:
                    del self.nodes[self.directory]
                self.assertEqual(self.validate(allow_missing_alias=True), self.target)
                with self.assertRaises(FileNotFoundError):
                    self.validate()
                with self.filesystem(), patch.object(remote, 'RemoteSocket') as connect:
                    self.assertEqual(remote.remote_status(self.root),
                                     {'daemon': 'stale', 'connection': 'unavailable'})
                    connect.assert_not_called()

    def test_missing_target_does_not_bypass_alias_or_directory_validation(self):
        del self.nodes[self.target]
        self.nodes[self.directory] = metadata(stat.S_IFLNK, 0o700)
        self.assertEqual(self.state()['daemon'], 'unreachable')
        del self.nodes[self.directory]
        self.link_target = '/tmp/foreign.sock'
        self.assertEqual(self.state()['daemon'], 'unreachable')

    def test_missing_endpoint_is_not_startable_below_an_unsafe_control_parent(self):
        del self.nodes[self.alias]
        for entry in (metadata(stat.S_IFLNK, 0o777), metadata(stat.S_IFREG, 0o600),
                      metadata(stat.S_IFDIR, 0o700, 2000), metadata(stat.S_IFDIR, 0o770)):
            with self.subTest(parent=entry):
                self.nodes[self.alias.parent] = entry
                self.assertEqual(self.state(), {'daemon': 'unreachable', 'connection': 'unknown'})
        del self.nodes[self.alias.parent]
        self.nodes[self.root] = metadata(stat.S_IFLNK, 0o777)
        self.assertEqual(self.state()['daemon'], 'unreachable')

    def test_missing_endpoint_under_safe_or_missing_control_parent_is_stopped(self):
        del self.nodes[self.alias]
        self.assertEqual(self.state(), {'daemon': 'stopped', 'connection': 'unavailable'})
        del self.nodes[self.alias.parent]
        self.assertEqual(self.state(), {'daemon': 'stopped', 'connection': 'unavailable'})

    def test_refused_alias_or_direct_socket_is_stale_only_without_kernel_entry(self):
        for direct in (False, True):
            with self.subTest(direct=direct):
                if direct:
                    self.nodes[self.alias] = metadata(stat.S_IFSOCK, 0o600)
                self.assertEqual(self.state(), {'daemon': 'stale', 'connection': 'unavailable'})
                for path in ((self.alias,) if direct else (self.alias, self.target)):
                    table = KERNEL_HEADER + '0: 2 0 00010000 0001 01 123 ' + str(path) + '\n'
                    self.assertEqual(self.state(kernel=table),
                                     {'daemon': 'unreachable', 'connection': 'unknown'})

    def test_unknown_kernel_evidence_and_other_errors_remain_unreachable(self):
        for table in ('', 'unrecognized header\n', KERNEL_HEADER + 'broken row\n',
                      KERNEL_HEADER + '0: 2 0 invalid 1 1 123 /other\n'):
            with self.subTest(table=table):
                self.assertEqual(self.state(kernel=table)['daemon'], 'unreachable')
        for error in (PermissionError(errno.EACCES, 'denied'), TimeoutError()):
            with self.subTest(error=type(error).__name__):
                self.assertEqual(self.state(error=error)['daemon'], 'unreachable')
        for error in (PermissionError(), FileNotFoundError()):
            with self.subTest(kernel_error=type(error).__name__), self.filesystem(), \
                    patch.object(remote, 'RemoteSocket', side_effect=ConnectionRefusedError(errno.ECONNREFUSED, 'refused')), \
                    patch.object(Path, 'read_text', side_effect=error):
                self.assertEqual(remote.remote_status(self.root)['daemon'], 'unreachable')

    def test_kernel_paths_with_spaces_and_unnamed_sockets_are_supported(self):
        table = (KERNEL_HEADER + '0: 2 0 0 1 1 123\n'
                 + '1: 2 0 10000 1 1 456 /synthetic/path with spaces\n')
        with patch.object(Path, 'read_text', return_value=table):
            self.assertEqual(remote.kernel_socket_paths(), {'/synthetic/path with spaces'})

    def test_real_direct_socket_and_foreign_alias_are_read_only(self):
        with tempfile.TemporaryDirectory(prefix='hacp-socket-') as temp:
            path = Path(temp) / 'local.sock'
            listener = socket.socket(socket.AF_UNIX)
            self.addCleanup(listener.close)
            listener.bind(str(path))
            path.chmod(0o600)
            self.assertEqual(remote.native_socket_path(path), path)
            alias = Path(temp) / 'foreign.sock'
            alias.symlink_to(path)
            before = (alias.lstat().st_ino, path.lstat().st_ino)
            with self.assertRaises(remote.RemoteError):
                remote.native_socket_path(alias)
            self.assertEqual((alias.lstat().st_ino, path.lstat().st_ino), before)

    @unittest.skipUnless(sys.platform == 'linux', 'native /tmp rendezvous layout is Linux-specific')
    def test_real_persistent_alias_survives_missing_temporary_socket_without_mutation(self):
        with tempfile.TemporaryDirectory(prefix='hacp-rendezvous-') as temp:
            root = Path(temp)
            alias = root / 'current/codex-home/app-server-control/app-server-control.sock'
            alias.parent.mkdir(parents=True, mode=0o700)
            canonical = alias.parent.resolve() / alias.name
            target = Path('/tmp') / f'codex-daemon-{os.getuid()}' / hashlib.sha256(os.fsencode(canonical)).hexdigest()
            self.assertFalse(target.exists())
            alias.symlink_to(target)
            before = (alias.lstat().st_ino, os.readlink(alias))
            self.assertEqual(remote.remote_status(root), {'daemon': 'stale', 'connection': 'unavailable'})
            self.assertEqual((alias.lstat().st_ino, os.readlink(alias)), before)
            self.assertFalse(target.exists())


class NativeEnvironmentCompatibility(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='hacp-environment-')
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.root = self.base / 'runtime'
        self.home = self.root / 'current/codex-home'
        self.home.mkdir(parents=True)
        self.user_home = self.base / 'user'
        self.user_home.mkdir()
        self.alias = self.user_home / '.codex'
        self.environment = {'HOME': str(self.user_home), 'PATH': '/synthetic/bin',
                            'CODEX_HOME': '/synthetic/previous', 'UNRELATED_SETTING': 'preserved'}

    def environment_result(self):
        with patch.dict(os.environ, self.environment, clear=True), \
                patch.object(Path, 'home', return_value=self.user_home):
            before = dict(os.environ)
            result = remote.native_environment(self.root)
            self.assertEqual(dict(os.environ), before)
            return result

    def test_matching_default_alias_omits_only_codex_home(self):
        self.alias.symlink_to(self.home)
        result = self.environment_result()
        self.assertEqual(result, {key: value for key, value in self.environment.items() if key != 'CODEX_HOME'})
        self.assertTrue(self.alias.is_symlink())

    def test_missing_wrong_dangling_and_real_directory_use_persistent_fallback(self):
        for kind in ('missing', 'wrong', 'dangling', 'real-directory'):
            with self.subTest(kind=kind):
                if kind == 'wrong':
                    self.alias.symlink_to(self.base)
                elif kind == 'dangling':
                    self.alias.symlink_to(self.base / 'missing')
                elif kind == 'real-directory':
                    self.alias.mkdir()
                try:
                    result = self.environment_result()
                    self.assertEqual(result, {**self.environment, 'CODEX_HOME': str(self.home.resolve())})
                finally:
                    if self.alias.is_symlink():
                        self.alias.unlink()
                    elif self.alias.is_dir():
                        self.alias.rmdir()

    def test_alias_loop_and_resolution_failure_keep_explicit_fallback(self):
        self.alias.symlink_to(self.alias.name)
        self.assertEqual(self.environment_result()['CODEX_HOME'], str(self.home.resolve()))
        original = Path.resolve
        for error in (PermissionError(), RuntimeError('legacy Python symlink loop')):
            def resolve(path, *args, **kwargs):
                if path == self.alias:
                    raise error
                return original(path, *args, **kwargs)
            with self.subTest(error=type(error).__name__), patch.object(Path, 'resolve', resolve):
                self.assertEqual(self.environment_result()['CODEX_HOME'], str(self.home.resolve()))

    def test_missing_persistent_home_blocks_without_creating_paths(self):
        self.home.rmdir()
        with self.assertRaises(FileNotFoundError):
            self.environment_result()
        self.assertFalse(self.home.exists())

    def test_start_uses_original_cli_explicit_working_directory_and_native_environment(self):
        cli = self.base / 'original-codex'
        credential_path = self.home / 'auth.json'
        credential_path.write_text('{"synthetic": true}')
        (self.root / 'locks').mkdir()
        for matching in (False, True):
            with self.subTest(matching_alias=matching):
                if matching:
                    self.alias.symlink_to(self.home)
                with patch.dict(os.environ, self.environment, clear=True), \
                        patch.object(Path, 'home', return_value=self.user_home), \
                        patch.object(remote, 'validate_runtime'), \
                        patch.object(remote, 'read_json', return_value={'enabled': True}), \
                        patch.object(remote.shutil, 'which', return_value='/synthetic/ps'), \
                        patch.object(remote, 'native_cli', return_value=cli), \
                        patch.object(remote, 'remote_status', side_effect=[
                            {'daemon': 'stale', 'connection': 'unavailable'},
                            {'daemon': 'running', 'connection': 'connected'}]), \
                        patch.object(remote.subprocess, 'run', return_value=Mock()) as launch:
                    self.assertEqual(remote.start(self.root)['start'], 'started')
                    launch.assert_called_once()
                    self.assertEqual(launch.call_args.args[0], [str(cli), 'remote-control', 'start', '--json'])
                    options = launch.call_args.kwargs
                    self.assertEqual(options['cwd'], self.root.parent)
                    self.assertEqual(options['timeout'], 45)
                    self.assertTrue(options['check'])
                    self.assertTrue(options['start_new_session'])
                    expected = dict(self.environment)
                    if matching:
                        expected.pop('CODEX_HOME')
                    else:
                        expected['CODEX_HOME'] = str(self.home.resolve())
                    self.assertEqual(options['env'], expected)


if __name__ == '__main__':
    unittest.main()
