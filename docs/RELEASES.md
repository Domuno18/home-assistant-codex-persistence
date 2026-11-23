# Releases and publication

## Current status

`0.9.1` is a stable diagnostic hotfix for `0.9.0`. It corrects how HACP
reports the scope of its access-profile check. The check reads stored
configuration. Each worker must verify its own effective sandbox and tools.

`0.9.0` was the regular release for the runtime-layout diagnostic and
Python 3.14 Remote endpoint compatibility. It follows `0.9.0-beta.6`. The
[7.2.0 maintenance verification](REFERENCE-UPDATE-7.2.0.md#maintenance-verification--2026-11-22)
records the running-system repair on the previous beta. Release artifacts,
installation, and restart verification have separate evidence.
[BETA-5-ACCEPTANCE.md](BETA-5-ACCEPTANCE.md) retains the earlier release results.

Changing a version file, building an artifact, pushing Git commits, publishing
a release, and changing repository visibility are deliberately separate
actions.

## Version policy

Versions follow `MAJOR.MINOR.PATCH` with optional prerelease identifiers.

| Change | Example | Meaning |
|---|---:|---|
| beta iteration | `0.9.0-beta.3` | another prerelease with no stable compatibility promise |
| compatible bug fix after a stable release | `0.9.1` | patch release |
| backward-compatible feature | `0.10.0` | minor release |
| breaking path, startup contract, runtime format, or migration change | next `MAJOR.0.0` | major release with migration instructions |
| first major public compatibility contract | `1.0.0` | only after public beta evidence and explicit approval |

Beta means real-world testing is welcome, but operators must expect incomplete
platform coverage and possible migration work before a later release.

## Beta release gate

Before publishing a beta:

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

1. Update `VERSION`, the program version, this policy, and `CHANGELOG.md`.
2. Run all validation and security gates.
3. Commit the complete candidate and obtain explicit release approval.
4. Set `HACP_PEER_REPO` to the other local repository and invoke the root
   release entry point. Both worktrees must be clean and pass the documented
   parity check before the release can build or tag:

   ```sh
   HACP_PEER_REPO=/path/to/other-repository ./release.sh
   ```

   In the private repository, use `./release.sh --private` with the same
   environment variable. This selects a private candidate; it grants no public
   publication permission. The permitted metadata/provenance exceptions are
   defined in [REPOSITORY-PARITY.md](REPOSITORY-PARITY.md).
5. Inspect the artifact and manifest, verify their commit/version binding, and
   validate a clean extraction. Record private and public results separately.
6. Publish public commits and the reviewed tag through explicit `git push`
   commands only after owner authorization. The administrative `publish.sh`
   helper is private-only and must not be used to publish the public repository.
7. Create the public GitHub prerelease using an explicit `gh release create`
   operation with the matching `CHANGELOG.md` section and verified artifacts;
   inspect the resulting release. Publication remains separate from installation.

## Beta.4 acceptance

The owner authorized both repository pushes and documented beta prereleases.
Repository visibility is unchanged. Product code uses the original Codex CLI;
no upstream executable is included in the source archive. The matching
[BETA-4-ACCEPTANCE.md](BETA-4-ACCEPTANCE.md) distinguishes completed automated
checks, live smoke checks and open behavioral/platform boundaries. Verify each
archive with `scripts/verify_release.py` using its actual version and commit,
then validate a clean extraction before publication.

The 2026-09-19 post-release documentation addendum records the current Studio
Code Server `7.1.1` running state and explicit native-memory activation. It does
not rebuild or replace the published beta.4 archives. Release-page text may link
to the corrected main-branch documentation but must preserve that distinction.

## Beta.5 acceptance

The beta.5 changes preserve the original CLI and its package ownership. The
source release includes HACP's compatibility adapter and regression evidence,
not native executables or private operational state. The
[beta.5 acceptance record](BETA-5-ACCEPTANCE.md) must identify fresh validation,
repository parity, source/artifact checks, and the remaining client behavior.

The operator-confirmed new-chat-in-explicit-folder-to-voice workaround and
existing-chat voice do not establish successful automatic home selection. A suspected iOS client issue is not a proven cause,
and untested platforms or a new container replacement must not be presented as
accepted merely because earlier beta lifecycle checks passed.

## Beta.5 post-release compatibility addendum — 2026-09-29

Studio Code Server `7.2.0` is supported on the tested reference installation.
The real `7.1.1` to `7.2.0` update passed the authenticated HACP audit, startup
and access-profile checks; remote control was connected and commands worked
without a sandbox or `bwrap` error. The
[7.2.0 acceptance record](REFERENCE-UPDATE-7.2.0.md) is authoritative for this
fresh evidence and its limits.

Both beta.5 release pages receive the same dated compatibility addendum linking
to the new main-branch evidence. This documentation update leaves the version,
release tag and published archives unchanged; the original tagged documentation
predates the 7.2.0 acceptance.
