"""TC-026/027: version, documentation and artifact boundary regressions."""
import hashlib
import importlib.util
import io
from pathlib import Path
import tarfile
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('verify_release',ROOT/'scripts/verify_release.py')
verifier=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(verifier)


class ReleaseContractTests(unittest.TestCase):
    def test_candidate_version_and_documentation_are_consistent(self):
        version=(ROOT/'VERSION').read_text().strip()
        self.assertIn('PROGRAM_VERSION='+version,(ROOT/'scripts/ha-codex-persistence.sh').read_text())
        self.assertIn('"version": "'+version+'"',(ROOT/'scripts/hacp_remote.py').read_text())
        self.assertIn('## '+version,(ROOT/'CHANGELOG.md').read_text())
        for name in ('README.md','docs/PROJECT-PLAN.md','docs/TEST-PLAN.md'):
            self.assertIn('DEVELOPMENT-PLAN.md',(ROOT/name).read_text())
        self.assertIn('Codex Memories',(ROOT/'docs/MEMORY-COMPATIBILITY.md').read_text())

    def test_current_711_and_native_memory_activation_are_bounded(self):
        readme=(ROOT/'README.md').read_text()
        profile=(ROOT/'PROJECT-PROFILE.md').read_text()
        memory=(ROOT/'docs/MEMORY-COMPATIBILITY.md').read_text()
        evidence=(ROOT/'docs/BETA-4-ACCEPTANCE.md').read_text()
        self.assertIn('Studio Code Server `7.1.1`',readme)
        self.assertIn('current `7.1.1` post-repair restart',profile)
        self.assertIn('disabled | enabled',memory)
        self.assertIn('explicit operator approval',memory)
        self.assertIn('Live generation/retrieval remains unverified',evidence)
        self.assertIn('does not alter the beta.4 archives',evidence)

    def test_valid_archive_and_negative_identity_checksum_and_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); archive=root/'candidate.tar.gz'; manifest=root/'candidate.manifest.txt'
            required=['VERSION','CHANGELOG.md','docs/DEVELOPMENT-PLAN.md','scripts/ha-codex-persistence.sh','scripts/hacp_remote.py','scripts/validate.sh']
            def build(extra=None,kind=None):
                with tarfile.open(archive,'w:gz') as bundle:
                    for name in required+([extra] if extra else []):
                        member=tarfile.TarInfo(name); body=b'0.9.0-beta.4\n'
                        if name==extra and kind:
                            member.type=kind; member.linkname='/synthetic/foreign'
                            bundle.addfile(member)
                        else:
                            member.size=len(body); bundle.addfile(member,io.BytesIO(body))
                digest=hashlib.sha256(archive.read_bytes()).hexdigest()
                manifest.write_text(f'version=0.9.0-beta.4\ncommit=synthetic-commit\nsource=tracked-files-from-HEAD\n{digest}  {archive.name}\n')
            build()
            self.assertEqual(verifier.verify(archive,manifest,'0.9.0-beta.4','synthetic-commit'),len(required))
            with self.assertRaises(ValueError): verifier.verify(archive,manifest,'wrong','synthetic-commit')
            archive.write_bytes(archive.read_bytes()+b'corrupt')
            with self.assertRaises(ValueError): verifier.verify(archive,manifest,'0.9.0-beta.4','synthetic-commit')
            for name,kind in [('../escape',None),('/absolute',None),('safe-link',tarfile.SYMTYPE),('hard-link',tarfile.LNKTYPE),('.codex/auth.json',None),('state.sqlite',None),('VERSION',None)]:
                with self.subTest(name=name):
                    build(name,kind)
                    with self.assertRaises(ValueError): verifier.verify(archive,manifest,'0.9.0-beta.4','synthetic-commit')

if __name__=='__main__': unittest.main()
