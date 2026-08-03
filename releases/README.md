# Releases

The canonical source for each released version is the annotated Git tag
`v<VERSION>`. `scripts/build.sh` also creates a structure-preserving archive
from the files tracked in `HEAD` and writes a manifest containing the archive's
SHA-256 checksum to `dist/`.

The `dist/` directory is not version-controlled. Validation, artifact creation,
local release tagging, publication, and deployment are deliberately separate
operations. Therefore, validation and build runs do not modify Git history or
a production system.
