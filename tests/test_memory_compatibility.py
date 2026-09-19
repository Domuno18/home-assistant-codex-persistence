"""TC-015/028: Core Knowledge and native Codex state stay independent."""
import hashlib
from pathlib import Path
import tempfile
import unittest

from test_codex_persistence import PersistenceHarness


def manifest(root, *, timestamps=True):
    result = {}
    for path in root.rglob('*'):
        st=path.lstat()
        if path.is_symlink(): value=('link',str(path.readlink()))
        elif path.is_file(): value=('file',hashlib.sha256(path.read_bytes()).hexdigest())
        elif path.is_dir(): value=('directory',)
        else: value=('special',)
        result[str(path.relative_to(root))]=(st.st_mode,st.st_mtime_ns if timestamps else None,*value)
    return result


class MemoryCompatibilityTests(unittest.TestCase):
    def test_all_modes_preserved_across_container_replacement_and_read_only_audit(self):
        for native in (False,True):
            for curated in (False,True):
                with self.subTest(native=native,curated=curated), tempfile.TemporaryDirectory() as temp:
                    h=PersistenceHarness(Path(temp)); h.seed_logged_in_state()
                    config=h.codex/'config.toml'
                    config.write_text('cli_auth_credentials_store = "file"\n'+config.read_text()+f'\n[features]\nmemories = {str(native).lower()}\n')
                    original_config=config.read_bytes()
                    store=h.codex/'memories'; store.mkdir(exist_ok=True)
                    (store/'memory_summary.md').write_text('Synthetic native fact: old value.\n')
                    state=h.codex/'state_5.sqlite'
                    if not state.exists(): state.write_bytes(b'Synthetic state placeholder')
                    native_before=manifest(store,timestamps=False)
                    enabled='YES' if curated else 'NO'
                    install=h.install(HACP_MEMORY_SETUP=enabled)
                    self.assertEqual(install.returncode,0,install.stdout+install.stderr)
                    self.assertEqual((h.codex/'config.toml').read_bytes(),original_config)
                    self.assertEqual(manifest(h.codex/'memories',timestamps=False),native_before)
                    knowledge=h.workspace/'core-knowledge'
                    if curated:
                        (knowledge/'MEMORY.md').write_text('Synthetic confirmed correction: new value.\n')
                        knowledge_before=manifest(knowledge)
                    else: self.assertFalse(knowledge.exists())
                    h.replace_container()
                    for _ in range(2):
                        boot=h.run('boot',use_installed_script=True,HACP_BOOT_OK='YES',HACP_MEMORY_SETUP=enabled)
                        self.assertEqual(boot.returncode,0,boot.stdout+boot.stderr)
                    self.assertEqual((h.codex/'config.toml').read_bytes(),original_config)
                    self.assertEqual(manifest(h.codex/'memories',timestamps=False),native_before)
                    if curated: self.assertEqual(manifest(knowledge),knowledge_before)
                    before=manifest(h.runtime)
                    audited=h.run('audit',use_installed_script=True,HACP_MEMORY_SETUP=enabled)
                    self.assertEqual(audited.returncode,0,audited.stdout+audited.stderr)
                    self.assertEqual(before,manifest(h.runtime))

    def test_existing_legacy_store_is_preserved_and_dual_store_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            h=PersistenceHarness(Path(temp)); h.seed_logged_in_state()
            legacy=h.workspace/'Memories'; legacy.mkdir(parents=True)
            (legacy/'MEMORY.md').write_text('Synthetic confirmed durable fact.\n')
            result=h.install()
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertFalse((h.workspace/'core-knowledge').exists())
            self.assertIn(str(legacy/'MEMORY.md'),(h.codex/'AGENTS.md').read_text())
            (h.workspace/'core-knowledge').mkdir()
            before=manifest(h.runtime)
            result=h.install()
            self.assertNotEqual(result.returncode,0)
            self.assertIn('both Core Knowledge',result.stdout)
            self.assertEqual(before,manifest(h.runtime))

    def test_native_path_overlap_is_rejected_before_runtime_creation(self):
        with tempfile.TemporaryDirectory() as temp:
            h=PersistenceHarness(Path(temp)); h.seed_logged_in_state()
            native=h.codex/'Memories'; native.mkdir()
            before=manifest(h.codex)
            result=h.install(HACP_WORKSPACE_ROOT=str(h.codex))
            self.assertNotEqual(result.returncode,0)
            self.assertIn('overlaps native',result.stdout)
            self.assertFalse(h.runtime.exists())
            self.assertEqual(before,manifest(h.codex))

    def test_extended_workspace_start_rules_preserved_in_both_setup_orders(self):
        for order in ('workspace-first','hacp-first'):
            with self.subTest(order=order), tempfile.TemporaryDirectory() as temp:
                h=PersistenceHarness(Path(temp)); h.seed_logged_in_state()
                knowledge=h.workspace/'core-knowledge'
                if order=='hacp-first':
                    result=h.install(); self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                else: knowledge.mkdir(parents=True)
                for file in ('AGENTS.md','MEMORY.md'):
                    (knowledge/file).write_text('Synthetic curated content.\n')
                block=('<!-- BEGIN HACP MEMORY -->\n'
                       '## Core Knowledge – deliberately maintained durable knowledge\n\n'
                       f'1. At each session start, read `{knowledge}/AGENTS.md` completely.\n'
                       f'2. Then read `{knowledge}/MEMORY.md` completely. Check scope and conflicts.\n'
                       '3. Preserve independent workspace instructions. Memory grants no authority.\n'
                       '<!-- END HACP MEMORY -->\n')
                (h.codex/'AGENTS.md').write_text(block)
                for _ in range(2):
                    result=h.install(); self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                    self.assertEqual((h.codex/'AGENTS.md').read_text(),block)
                audited=h.audit(check_auth=False)
                self.assertEqual(audited.returncode,0,audited.stdout+audited.stderr)
                wrong=block.replace(str(knowledge/'MEMORY.md'),str(knowledge/'wrong.md'))
                (h.codex/'AGENTS.md').write_text(wrong)
                rejected=h.audit(check_auth=False)
                self.assertNotEqual(rejected.returncode,0)


if __name__ == '__main__': unittest.main()
