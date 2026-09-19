#!/usr/bin/env python3
"""Verify a HACP release archive against its manifest without extracting it."""
import argparse
import hashlib
from pathlib import Path, PurePosixPath
import re
import tarfile


def verify(archive: Path, manifest: Path, version: str, commit: str) -> int:
    text=manifest.read_text(encoding='utf-8')
    fields=dict(line.split('=',1) for line in text.splitlines() if '=' in line)
    if fields.get('version')!=version or fields.get('commit')!=commit or fields.get('source')!='tracked-files-from-HEAD':
        raise ValueError('release manifest identity mismatch')
    with archive.open('rb') as stream:
        checksum=hashlib.file_digest(stream,'sha256').hexdigest()
    sums=[line.split(maxsplit=1) for line in text.splitlines() if re.match(r'^[a-f0-9]{64}  ',line)]
    if len(sums)!=1 or sums[0][0]!=checksum or Path(sums[0][1]).name!=archive.name:
        raise ValueError('archive checksum mismatch')
    names=set()
    with tarfile.open(archive,'r:gz') as bundle:
        for member in bundle:
            path=PurePosixPath(member.name)
            if path.is_absolute() or '..' in path.parts or not (member.isfile() or member.isdir()) or member.name in names:
                raise ValueError('unsafe or duplicate archive member')
            if any(part in {'.git','.runtime','.codex','__pycache__','dist'} for part in path.parts) or path.suffix in {'.sqlite','.db','.pyc'} or path.name in {'auth.json','hosts.yml'}:
                raise ValueError('private or generated state in archive')
            names.add(member.name)
        required={'VERSION','CHANGELOG.md','docs/DEVELOPMENT-PLAN.md','scripts/ha-codex-persistence.sh','scripts/hacp_remote.py','scripts/validate.sh'}
        if not required<=names: raise ValueError('release archive is incomplete')
        if bundle.extractfile('VERSION').read().decode().strip()!=version: raise ValueError('archive version mismatch')
    return len(names)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive',type=Path); parser.add_argument('manifest',type=Path)
    parser.add_argument('--version',required=True); parser.add_argument('--commit',required=True)
    args=parser.parse_args()
    try: count=verify(args.archive,args.manifest,args.version,args.commit)
    except (OSError,ValueError,tarfile.TarError):
        parser.exit(1,'ERROR: release verification failed; identity, checksum or contents invalid.\n')
    print(f'Release archive verified: {count} members.')

if __name__=='__main__': main()
