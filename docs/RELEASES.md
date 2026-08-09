# Releases and publication

## Current status

`0.9.0-beta.2` is the current GitHub Prerelease. The public repository has a
clean root history, while the full development history remains in a separate
private archive. `0.9.0-beta.1` remains the first published prerelease.

Changing a version file, building an artifact, pushing Git commits, publishing
a release, and changing repository visibility are deliberately separate
actions.

## Version policy

Versions follow `MAJOR.MINOR.PATCH` with optional prerelease identifiers.

| Change | Example | Meaning |
|---|---:|---|
| beta iteration | `0.9.0-beta.2` | another prerelease with no stable compatibility promise |
| compatible bug fix after a stable release | `0.9.1` | patch release |
| backward-compatible feature | `0.10.0` | minor release |
| breaking path, startup contract, runtime format, or migration change | next `MAJOR.0.0` | major release with migration instructions |
| first stable public contract | `1.0.0` | only after public beta evidence and explicit approval |

Beta means real-world testing is welcome, but operators must expect incomplete
platform coverage and possible migration work before a later release.

## Beta release gate

Before publishing any beta, including `v0.9.0-beta.2`:

1. Finish the English public-documentation review.
2. Run `./scripts/validate.sh` and
   `./scripts/security-scan.sh --all-history` from a clean committed tree.
3. Confirm that Git history, tags, build artifacts, examples, and screenshots
   contain no credentials, sessions, databases, populated memories, or private
   metadata.
4. Obtain one independent installation report if practical.
5. Record explicit owner approval for the beta and repository visibility.

The absence of independent feedback may be accepted as a documented beta risk,
but it must not be silently presented as broad compatibility evidence.

## Public repository assessment

The repository can be published under MIT because it contains only this
project's own code and does not vendor or redistribute upstream projects. The
review and official upstream license links are recorded in
[`THIRD_PARTY.md`](../THIRD_PARTY.md).

Compatibility names are descriptive only. Real credentials, chats, native
session data, populated memories, and the private runtime remain local and are
never part of a release.

## Release procedure

1. Update `VERSION`, the program version, this policy, `CHANGELOG.md`, and
   `RELEASE_NOTES.md`.
2. Run all validation and security gates.
3. Commit the complete candidate and obtain explicit release approval.
4. `./scripts/release.sh` creates the local artifact and annotated tag.
5. Inspect the artifact and manifest.
6. Push the reviewed tag to the public repository only after explicit release approval.
7. Create and inspect the GitHub prerelease as a separately approved action.
