"""Synthetic remote lifecycle tests: no host changes, network or login refresh."""
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import struct
import tempfile
import threading
import unittest
from unittest.mock import patch, Mock

SPEC = importlib.util.spec_from_file_location('hacp_remote', Path(__file__).resolve().parents[1] / 'scripts/hacp_remote.py')
remote = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(remote)


def snapshot(root):
    return {str(p.relative_to(root)): (p.lstat().st_mode, p.read_bytes() if p.is_file() else None)
            for p in root.rglob('*') if not p.is_socket()}


class RemoteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'runtime'
        self.root.mkdir(mode=0o700)
        for name in ('bootstrap', 'state', 'locks', 'current/codex-home'):
            (self.root / name).mkdir(parents=True, mode=0o700)
        (self.root / '.hacp-runtime-owner').write_bytes(remote.OWNER)
        self.home = self.root / 'current/codex-home'
        (self.home / 'auth.json').write_text('{"synthetic":true}')
        packages=self.home/'packages/standalone'
        release=packages/'releases/synthetic/bin'
        release.mkdir(parents=True)
        (packages/'current').symlink_to('releases/synthetic',target_is_directory=True)
        self.cli = release/'codex'
        self.cli.write_text('#!/bin/sh\nprintf "codex-cli 0.154.0\\n"\n')
        self.cli.chmod(0o700)
        self.options = {'packages': ['curl'], 'init_commands': ['HACP_MANAGED=home-assistant-codex-persistence sh /example/boot', 'echo keep'], 'other': {'keep': True}}
        self.command = f'{remote.REMOTE_MARKER} python3 {self.root}/bootstrap/hacp_remote.py boot --runtime-root {self.root}'

    def enable(self):
        desired = remote.desired_options(self.options, self.command, True)
        with patch.object(remote, 'supervisor', side_effect=[{'options':self.options}, {'options':self.options}, {}, {'options':desired}]) as api:
            result = remote.configure(self.root, True, self.cli)
        return result, api

    def test_enable_disable_preserve_options_and_do_not_start(self):
        before = snapshot(self.home)
        with patch.object(remote.subprocess, 'run', return_value=Mock(stdout=b'codex-cli 0.154.0')), patch.object(remote.subprocess, 'Popen') as launch:
            result, api = self.enable()
            self.assertTrue(result['enabled'])
            desired = api.call_args_list[2].args[1]['options']
            self.assertEqual(desired['packages'], ['curl','procps','python3'])
            self.assertEqual(desired['init_commands'][1], self.command)
            self.assertEqual(desired['init_commands'][-1], 'echo keep')
            self.assertEqual(desired['other'], self.options['other'])
            disabled = remote.desired_options(desired, self.command, False)
            with patch.object(remote, 'supervisor', side_effect=[{'options':desired},{'options':desired},{},{'options':disabled}]):
                self.assertFalse(remote.configure(self.root, False, None)['enabled'])
            launch.assert_not_called()
        self.assertEqual(before, snapshot(self.home))
        self.assertEqual(remote.start(self.root)['connection'], 'disabled')

    def test_repeated_options_are_idempotent_and_ordered(self):
        desired = remote.desired_options(self.options, self.command, True)
        self.assertEqual(desired, remote.desired_options(desired, self.command, True))
        for bad in ({**self.options,'packages':'wrong'}, {**self.options,'init_commands':['echo wrong']}, {**self.options,'init_commands':[self.options['init_commands'][0],remote.REMOTE_MARKER+' foreign']}):
            with self.assertRaises(remote.RemoteError):
                remote.desired_options(bad,self.command,True)

    def test_concurrent_supervisor_edit_preserves_active_helper_and_state(self):
        self.enable()
        before = snapshot(self.root)
        with patch.object(remote, 'supervisor', side_effect=[{'options':self.options},{'options':{'changed':True}}]) as api:
            with self.assertRaisesRegex(remote.RemoteError,'concurrently'):
                remote.configure(self.root,True,self.cli)
            self.assertEqual(api.call_count,2)
        self.assertEqual(before, snapshot(self.root))

    def test_readback_failure_restores_previous_helper_and_active_state(self):
        self.enable()
        helper = self.root / 'bootstrap/hacp_remote.py'
        helper.write_bytes(b'# older helper\n')
        before = snapshot(self.root)
        with patch.object(remote, 'supervisor', side_effect=[{'options':self.options},{'options':self.options},{},{'options':{'concurrent':True}}]) as api:
            with self.assertRaisesRegex(remote.RemoteError,'read-back'):
                remote.configure(self.root,True,self.cli)
            self.assertEqual(api.call_count,4)  # no blind rollback of concurrent options
        self.assertEqual(before, snapshot(self.root))

    def test_missing_ps_and_unsupported_cli_do_not_activate(self):
        for missing in (True,False):
            with self.subTest(missing_ps=missing), patch.object(remote,'supervisor',return_value={'options':self.options}), patch.object(remote.shutil,'which',return_value=None if missing else '/synthetic/ps'), patch.object(remote.subprocess,'run',return_value=Mock(stdout=b'unsupported-cli')):
                with self.assertRaises(remote.RemoteError): remote.configure(self.root,True,self.cli)
                self.assertFalse((self.root/'state/remote.json').exists())

    def test_unsafe_cli_and_missing_auth_fail_without_launch(self):
        self.enable()
        for mode in ('permissions','auth','outside'):
            with self.subTest(mode=mode), patch.object(remote.subprocess,'run') as launch:
                if mode == 'permissions': self.cli.chmod(0o777)
                if mode == 'auth':
                    self.cli.chmod(0o700)
                    (self.home/'auth.json').unlink()
                if mode == 'outside':
                    current=self.home/'packages/standalone/current'
                    current.unlink(); current.symlink_to(Path(self.temp.name))
                with self.assertRaises((remote.RemoteError,OSError)): remote.start(self.root)
                launch.assert_not_called()

    def test_native_update_selection_is_preserved_without_copy_or_pin(self):
        self.enable()
        current=self.home/'packages/standalone/current'
        updated=self.home/'packages/standalone/releases/next/bin'
        updated.mkdir(parents=True)
        (updated/'codex').write_bytes(self.cli.read_bytes())
        (updated/'codex').chmod(0o700)
        current.unlink(); current.symlink_to('releases/next')
        self.assertEqual(remote.native_cli(self.root),updated/'codex')
        self.assertFalse(list((self.root/'bootstrap').glob('remote-codex*')))
        self.assertEqual(remote.read_json(self.root/'state/remote.json')['cli'],'native-managed-current')

    def test_competing_start_cannot_acquire_lock(self):
        self.enable()
        with remote.mutation_lock(self.root), patch.object(remote.subprocess,'Popen') as launch:
            with self.assertRaisesRegex(remote.RemoteError,'active'): remote.start(self.root)
            launch.assert_not_called()

    def test_running_daemon_is_not_replaced_even_if_disconnected(self):
        self.enable()
        for connection in ('connected','connecting','errored','disabled'):
            with self.subTest(connection=connection), patch.object(remote,'remote_status',return_value={'daemon':'running','connection':connection}), patch.object(remote.subprocess,'Popen') as launch:
                self.assertEqual(remote.start(self.root)['start'],'already-running')
                launch.assert_not_called()

    def test_unreachable_socket_is_not_deleted_or_replaced(self):
        self.enable()
        with patch.object(remote,'remote_status',return_value={'daemon':'unreachable','connection':'unknown'}), patch.object(remote.subprocess,'Popen') as launch:
            with self.assertRaisesRegex(remote.RemoteError,'unreachable'): remote.start(self.root)
            launch.assert_not_called()

    def test_first_start_uses_official_remote_control_without_model_overrides(self):
        self.enable()
        with patch.object(remote,'remote_status',side_effect=[{'daemon':'stopped','connection':'unavailable'},{'daemon':'running','connection':'connected'}]), patch.object(remote.subprocess,'run') as launch:
            self.assertEqual(remote.start(self.root)['start'],'started')
            args=launch.call_args.args[0]
            self.assertEqual(args,[str(self.cli),'remote-control','start','--json'])
            self.assertEqual(launch.call_args.kwargs['timeout'],45)
            self.assertTrue(launch.call_args.kwargs['start_new_session'])

    def test_native_failure_and_timeout_are_bounded(self):
        self.enable()
        for exc in (remote.subprocess.CalledProcessError(1,['native-cli']),remote.subprocess.TimeoutExpired(['native-cli'],45)):
            with self.subTest(error=type(exc).__name__), patch.object(remote,'remote_status',return_value={'daemon':'stopped','connection':'unavailable'}), patch.object(remote.subprocess,'run',side_effect=exc):
                with self.assertRaises(remote.subprocess.SubprocessError): remote.start(self.root)

    def test_boot_error_does_not_block_editor(self):
        with patch('sys.argv',['helper','boot','--runtime-root',str(self.root)]), patch('builtins.print') as output:
            self.assertEqual(remote.main(),0)
            self.assertIn('warning',output.call_args.args[0])
        with patch('sys.argv',['helper','boot','--runtime-root',str(self.root)]), patch.object(remote,'start',return_value={'connection':'connecting'}), patch('builtins.print'):
            self.assertEqual(remote.main(),0)

    def test_status_without_daemon_is_completely_read_only(self):
        before=snapshot(self.root)
        with patch.object(remote.subprocess,'Popen') as launch:
            self.assertEqual(remote.remote_status(self.root)['daemon'],'stopped')
            launch.assert_not_called()
        self.assertEqual(before,snapshot(self.root))

    def test_invalid_owner_and_symlinked_control_files_rejected(self):
        marker=self.root/'.hacp-runtime-owner'
        marker.write_bytes(b'foreign\n')
        with self.assertRaises(remote.RemoteError): remote.validate_runtime(self.root)
        marker.write_bytes(remote.OWNER)
        target=self.root/'state/remote.json'
        target.symlink_to(self.cli)
        with patch.object(remote,'supervisor') as api:
            with self.assertRaises(remote.RemoteError): remote.configure(self.root,True,self.cli)
            api.assert_not_called()

    def test_crashed_socket_is_identified_without_unlinking(self):
        directory=self.home/'app-server-control'
        directory.mkdir(mode=0o700)
        endpoint=directory/'app-server-control.sock'
        listener=socket.socket(socket.AF_UNIX)
        listener.bind(str(endpoint))
        listener.close()
        before=endpoint.stat().st_ino
        self.assertEqual(remote.remote_status(self.root)['daemon'],'stale')
        self.assertEqual(endpoint.stat().st_ino,before)

    def test_real_unix_websocket_status_sanitized_without_mutation(self):
        directory=self.home/'app-server-control'
        directory.mkdir(mode=0o700)
        endpoint=directory/'app-server-control.sock'
        listener=socket.socket(socket.AF_UNIX)
        listener.bind(str(endpoint)); listener.listen(1); listener.settimeout(5)
        self.addCleanup(listener.close)
        received=[]
        errors=[]
        def server():
            try:
                conn,_=listener.accept()
                with conn:
                    conn.settimeout(5)
                    header=b''
                    while not header.endswith(b'\r\n\r\n'): header+=conn.recv(1)
                    key=[line.split(b':',1)[1].strip() for line in header.split(b'\r\n') if line.lower().startswith(b'sec-websocket-key:')][0]
                    accept=base64.b64encode(hashlib.sha1(key+b'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').digest())
                    conn.sendall(b'HTTP/1.1 101 Switching Protocols\r\nSec-WebSocket-Accept: '+accept+b'\r\n\r\n')
                    def exact(n):
                        data=b''
                        while len(data)<n:
                            part=conn.recv(n-len(data))
                            if not part: raise EOFError()
                            data+=part
                        return data
                    for _ in range(3):
                        first,second=exact(2)
                        assert second & 128
                        size=second & 127
                        if size==126: size=struct.unpack('!H',exact(2))[0]
                        mask=exact(4); body=exact(size)
                        request=json.loads(bytes(v^mask[i%4] for i,v in enumerate(body)))
                        received.append(request['method'])
                        if 'id' in request:
                            result={} if request['id']==1 else {'status':'connected','environmentId':'synthetic-sensitive-id','serverName':'synthetic-sensitive-name'}
                            payload=json.dumps({'id':request['id'],'result':result}).encode()
                            prefix=bytes([129,len(payload)]) if len(payload)<126 else bytes([129,126])+struct.pack('!H',len(payload))
                            conn.sendall(prefix+payload)
            except Exception as exc: errors.append(exc)
        thread=threading.Thread(target=server,daemon=True); thread.start()
        before=snapshot(self.root)
        result=remote.remote_status(self.root)
        thread.join(timeout=6)
        self.assertFalse(thread.is_alive()); self.assertEqual(errors,[])
        self.assertEqual(result,{'daemon':'running','connection':'connected'})
        self.assertEqual(received,['initialize','initialized','remoteControl/status/read'])
        self.assertEqual(before,snapshot(self.root))


if __name__ == '__main__': unittest.main()
